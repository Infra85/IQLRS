import {
  prepareNarration,
  type NarrationChunk,
  type NarrationSegment,
} from "./text";

export type PlaybackStatus =
  "idle" | "loading" | "playing" | "paused" | "ended" | "error";
export type PlaybackState = {
  status: PlaybackStatus;
  owner: string;
  chunks: NarrationChunk[];
  index: number;
  currentTime: number;
  duration: number;
  speed: number;
  volume: number;
  error: string | null;
};
type Loader = (text: string, signal: AbortSignal) => Promise<Blob>;
const initial: PlaybackState = {
  status: "idle",
  owner: "",
  chunks: [],
  index: 0,
  currentTime: 0,
  duration: 0,
  speed: 1,
  volume: 1,
  error: null,
};

/** One audio element, one request, and one immutable playback snapshot for the whole app. */
export class NarrationController {
  private state: PlaybackState = initial;
  private listeners = new Set<() => void>();
  private audio: HTMLAudioElement | null = null;
  private request: AbortController | null = null;
  private url: string | null = null;
  private generation = 0;
  private wantsPlayback = false;
  constructor(
    private load: Loader,
    private createAudio: () => HTMLAudioElement = () => new Audio(),
  ) {}
  getSnapshot = () => this.state;
  getServerSnapshot = () => initial;
  subscribe = (callback: () => void) => {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  };
  private update(patch: Partial<PlaybackState>) {
    this.state = { ...this.state, ...patch };
    this.listeners.forEach((fn) => fn());
  }
  private release() {
    this.request?.abort();
    this.request = null;
    if (this.audio) {
      this.audio.onended =
        this.audio.onerror =
        this.audio.ontimeupdate =
        this.audio.onloadedmetadata =
        this.audio.onpause =
        this.audio.onplaying =
          null;
      this.audio.pause();
      this.audio.removeAttribute("src");
      this.audio.load();
      this.audio = null;
    }
    if (this.url) URL.revokeObjectURL(this.url);
    this.url = null;
  }
  stop = () => {
    this.generation++;
    this.wantsPlayback = false;
    this.release();
    this.update({
      ...initial,
      speed: this.state.speed,
      volume: this.state.volume,
    });
  };
  start = (owner: string, segments: NarrationSegment[], startAt = 0) => {
    this.stop();
    const chunks = prepareNarration(segments);
    if (!chunks.length) return;
    const index = Math.max(
      0,
      chunks.findIndex((chunk) => chunk.id === segments[startAt]?.id),
    );
    this.update({ owner, chunks, index });
    void this.loadIndex(index);
  };
  private async playCurrent(token: number) {
    if (!this.audio || token !== this.generation) return;
    try {
      await this.audio.play();
      if (token !== this.generation) return;
      if (!this.wantsPlayback) {
        this.audio?.pause();
        return;
      }
      this.update({ status: "playing", error: null });
    } catch (error) {
      if (token !== this.generation || !this.wantsPlayback) return;
      // Mobile browser gesture policies can require an explicit Resume tap.
      if (error instanceof Error && error.name === "NotAllowedError") {
        this.wantsPlayback = false;
        this.update({
          status: "paused",
          error: "Audio is ready. Press Resume to listen.",
        });
      } else
        this.update({
          status: "error",
          error: "Audio couldn’t be played. Try again.",
        });
    }
  }
  private async loadIndex(index: number) {
    this.generation++;
    const token = this.generation;
    this.release();
    this.wantsPlayback = true;
    const request = new AbortController();
    this.request = request;
    this.update({
      index,
      status: "loading",
      error: null,
      currentTime: 0,
      duration: 0,
    });
    try {
      const blob = await this.load(
        this.state.chunks[index].spokenText,
        request.signal,
      );
      if (token !== this.generation) return;
      const audio = this.createAudio();
      this.audio = audio;
      this.url = URL.createObjectURL(blob);
      audio.preload = "auto";
      audio.playbackRate = this.state.speed;
      audio.volume = this.state.volume;
      audio.onloadedmetadata = () => {
        if (token === this.generation)
          this.update({
            duration: Number.isFinite(audio.duration) ? audio.duration : 0,
          });
      };
      audio.ontimeupdate = () => {
        if (token === this.generation)
          this.update({ currentTime: audio.currentTime });
      };
      audio.onpause = () => {
        if (token === this.generation && audio.paused && !audio.ended) {
          this.wantsPlayback = false;
          this.update({ status: "paused" });
        }
      };
      audio.onplaying = () => {
        if (token === this.generation && this.wantsPlayback)
          this.update({ status: "playing" });
      };
      audio.onerror = () => {
        if (token === this.generation)
          this.update({
            status: "error",
            error: "Audio couldn’t be played. Try again.",
          });
      };
      audio.onended = () => {
        if (token !== this.generation) return;
        if (index + 1 < this.state.chunks.length)
          void this.loadIndex(index + 1);
        else {
          this.wantsPlayback = false;
          this.update({ status: "ended", currentTime: audio.duration || 0 });
        }
      };
      audio.src = this.url;
      if (this.wantsPlayback) await this.playCurrent(token);
      else this.update({ status: "paused" });
    } catch (error) {
      if (token !== this.generation || request.signal.aborted) return;
      this.wantsPlayback = false;
      this.update({
        status: "error",
        error:
          error instanceof Error
            ? error.message
            : "Narration is unavailable. Try again.",
      });
    }
  }
  pause = () => {
    this.wantsPlayback = false;
    this.audio?.pause();
    this.update({ status: "paused" });
  };
  resume = () => {
    this.wantsPlayback = true;
    if (this.audio) void this.playCurrent(this.generation);
    else if (this.request && !this.request.signal.aborted)
      this.update({ status: "loading" });
    else void this.loadIndex(this.state.index);
  };
  retry = () => {
    void this.loadIndex(this.state.index);
  };
  replay = () => {
    void this.loadIndex(0);
  };
  next = () => {
    if (this.state.index + 1 < this.state.chunks.length)
      void this.loadIndex(this.state.index + 1);
  };
  previous = () => {
    void this.loadIndex(Math.max(0, this.state.index - 1));
  };
  seek = (time: number) => {
    if (this.audio && this.state.duration) {
      this.audio.currentTime = Math.max(0, Math.min(time, this.state.duration));
      this.update({ currentTime: this.audio.currentTime });
    }
  };
  setSpeed = (speed: number) => {
    if (![0.75, 1, 1.25, 1.5, 2].includes(speed)) return;
    if (this.audio) this.audio.playbackRate = speed;
    this.update({ speed });
  };
  setVolume = (volume: number) => {
    const value = Math.min(1, Math.max(0, volume));
    if (this.audio) this.audio.volume = value;
    this.update({ volume: value });
  };
}
