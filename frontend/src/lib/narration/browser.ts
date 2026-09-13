import { chunkSpeech } from "./text";

export type BrowserVoice = {
  speak: (
    text: string,
    speed: number,
    volume: number,
    events: {
      playing: () => void;
      ended: () => void;
      error: (message: string) => void;
    },
  ) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  configure?: (speed: number, volume: number) => void;
};


export function createBrowserVoice(): BrowserVoice | null {
  if (
    typeof window === "undefined" ||
    !window.speechSynthesis ||
    typeof window.SpeechSynthesisUtterance !== "function"
  )
    return null;
  const synth = window.speechSynthesis;
  
  let utterance: SpeechSynthesisUtterance | null = null;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let paused = false;
  let rate = 1;
  let loudness = 1;
  let started = false;
  let advance: (() => void) | null = null;
  const detach = () => {
    clearTimeout(timer);
    if (utterance)
      utterance.onstart = utterance.onend = utterance.onerror = null;
    utterance = null;
  };
  const stop = () => {
    advance = null;
    paused = false;
    detach();
    synth.cancel();
  };
  return {
    stop,
    configure(speed, volume) {
      rate = speed;
      loudness = volume;
    },
    speak(text, speed, volume, events) {
      stop();
      rate = speed;
      loudness = volume;
      const parts = chunkSpeech(text, 240);
      let index = 0;
      const next = () => {
        detach();
        if (index === parts.length) {
          events.ended();
          return;
        }
        const current = new window.SpeechSynthesisUtterance(parts[index++]);
        utterance = current;
        started = false;
        current.lang = "en-US";

        current.voice =
          synth.getVoices().find((voice) => /^en\b/i.test(voice.lang)) || null;
        current.rate = rate;
        current.volume = loudness;
        const fail = (message: string) => {
          if (utterance !== current) return;
          stop();
          events.error(message);
        };
        current.onstart = () => {
          if (utterance !== current) return;
          started = true;
          clearTimeout(timer);
          if (!paused) events.playing();
        };
        current.onend = () => {
          if (utterance !== current) return;
          if (paused) {
            detach();
            advance = next;
          } else next();
        };
        current.onerror = (event) =>
          fail(
            event.error === "not-allowed"
              ? "Your browser blocked speech. Press Retry audio to allow playback."
              : "Browser speech is unavailable. Check that an English voice is installed, then retry.",
          );
        timer = setTimeout(
          () =>
            fail(
              "Browser speech did not start. Check your device’s speech voices, then retry.",
            ),
          10000,
        );
        try {
          synth.resume();
          synth.speak(current);
        } catch {
          fail("Browser speech is unavailable. Please retry.");
        }
      };
      next();
    },
    pause() {
      paused = true;
      clearTimeout(timer);
      synth.pause();
    },
    resume() {
      paused = false;
      if (advance) {
        const next = advance;
        advance = null;
        next();
      } else {
        synth.resume();
        if (!started && utterance) {
          const current = utterance;
          timer = setTimeout(
            () =>
              current.onerror?.({
                error: "synthesis-unavailable",
              } as SpeechSynthesisErrorEvent),
            10000,
          );
        }
      }
    },
  };
}
