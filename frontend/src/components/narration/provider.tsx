"use client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useSyncExternalStore,
} from "react";
import { usePathname } from "next/navigation";
import {
  Headphones,
  Pause,
  Play,
  Square,
  RotateCcw,
  SkipBack,
  SkipForward,
  X,
  LocateFixed,
} from "lucide-react";
import { NarrationController } from "@/lib/narration/controller";
import { loadNarrationAudio } from "@/lib/narration/client";
import type { NarrationSegment } from "@/lib/narration/text";
import { Button } from "@/components/ui/button";

const Context = createContext<NarrationController | null>(null);
export function useNarration() {
  const controller = useContext(Context);
  if (!controller) throw new Error("NarrationProvider is missing");
  const state = useSyncExternalStore(
    controller.subscribe,
    controller.getSnapshot,
    controller.getServerSnapshot,
  );
  return { controller, state };
}
export function NarrationProvider({ children }: { children: React.ReactNode }) {
  const [controller] = useState(
    () => new NarrationController(loadNarrationAudio),
  );
  const pathname = usePathname();
  useEffect(() => () => controller.stop(), [controller, pathname]);
  return (
    <Context.Provider value={controller}>
      {children}
      <NarrationPlayer />
    </Context.Provider>
  );
}
export function ListenButton({
  owner,
  segments,
  startAt = 0,
  label = "Listen",
  className = "",
}: {
  owner: string;
  segments: NarrationSegment[];
  startAt?: number;
  label?: string;
  className?: string;
}) {
  const { controller, state } = useNarration();
  const contentKey = JSON.stringify(segments);
  useEffect(
    () => () => {
      if (controller.getSnapshot().owner === owner) controller.stop();
    },
    [controller, owner, contentKey],
  );
  const selected = state.owner === owner && state.status !== "idle";
  return (
    <Button
      variant="secondary"
      size="sm"
      className={`listen-button ${className}`}
      aria-label={`${label}: ${segments[startAt]?.title || "educational content"}`}
      aria-pressed={selected}
      onClick={() => controller.start(owner, segments, startAt)}
    >
      <Headphones size={15} aria-hidden="true" />
      {label}
    </Button>
  );
}
function time(seconds: number) {
  return `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0")}`;
}
function NarrationPlayer() {
  const { controller, state } = useNarration();
  const active = state.status !== "idle";
  const chunk = state.chunks[state.index];
  useEffect(() => {
    if (!active) return;
    document.body.classList.add("has-narration");
    return () => document.body.classList.remove("has-narration");
  }, [active]);
  useEffect(() => {
    if (!active || !chunk?.targetId || state.status === "ended") return;
    const element = document.getElementById(chunk.targetId);
    element?.setAttribute("data-narrating", "true");
    return () => element?.removeAttribute("data-narrating");
  }, [active, chunk?.targetId, state.status]);
  if (!active || !chunk) return null;
  const playing = state.status === "playing" || state.status === "loading";
  const progress =
    state.status === "ended"
      ? 100
      : (100 *
          (state.index +
            (state.duration ? state.currentTime / state.duration : 0))) /
        state.chunks.length;
  return (
    <section className="narration-player" aria-label="Read aloud player">
      <div className="narration-top">
        <div className="min-w-0">
          <p className="technical">AI voice · Read aloud</p>
          <p className="narration-title" aria-live="polite">
            {chunk.title}
            <span className="text-slate-400 text-xs font-normal ml-2">
              {chunk.parts > 1 ? `Part ${chunk.part + 1}/${chunk.parts}` : ""}
            </span>
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Stop narration and close player"
          onClick={controller.stop}
        >
          <X size={18} />
        </Button>
      </div>
      <div className="narration-controls">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            aria-label="Previous narration segment"
            onClick={controller.previous}
            disabled={state.index === 0 && !state.currentTime}
          >
            <SkipBack size={17} />
          </Button>
          {state.status === "error" ? (
            <Button onClick={controller.retry}>Retry audio</Button>
          ) : state.status === "ended" ? (
            <Button onClick={controller.replay}>
              <RotateCcw size={16} />
              Replay
            </Button>
          ) : (
            <Button
              onClick={playing ? controller.pause : controller.resume}
              aria-label={playing ? "Pause narration" : "Resume narration"}
            >
              {playing ? <Pause size={16} /> : <Play size={16} />}
              {playing ? "Pause" : "Resume"}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            aria-label="Next narration segment"
            onClick={controller.next}
            disabled={state.index >= state.chunks.length - 1}
          >
            <SkipForward size={17} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Stop narration"
            onClick={controller.stop}
          >
            <Square size={16} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Replay narration from beginning"
            onClick={controller.replay}
          >
            <RotateCcw size={16} />
          </Button>
        </div>
        <div className="narration-options">
          <label className="sr-only" htmlFor="narration-speed">
            Narration speed
          </label>
          <select
            id="narration-speed"
            className="ui-input !w-auto !min-h-10 !py-1 text-sm"
            value={state.speed}
            onChange={(e) => controller.setSpeed(Number(e.target.value))}
          >
            {[0.75, 1, 1.25, 1.5, 2].map((speed) => (
              <option value={speed} key={speed}>
                {speed}×
              </option>
            ))}
          </select>
          <label className="narration-volume text-xs text-slate-400">
            Volume
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={state.volume}
              onChange={(e) => controller.setVolume(Number(e.target.value))}
            />
          </label>
          {chunk.targetId && (
            <Button
              variant="ghost"
              size="sm"
              aria-label="Show narrated section"
              onClick={() =>
                document.getElementById(chunk.targetId!)?.scrollIntoView({
                  block: "center",
                  behavior: window.matchMedia(
                    "(prefers-reduced-motion: reduce)",
                  ).matches
                    ? "auto"
                    : "smooth",
                })
              }
            >
              <LocateFixed size={17} />
            </Button>
          )}
        </div>
      </div>
      <div className="narration-timeline">
        <label htmlFor="narration-position" className="sr-only">
          Playback position in current segment
        </label>
        <input
          id="narration-position"
          type="range"
          min="0"
          max={state.duration || 1}
          step="0.1"
          value={Math.min(state.currentTime, state.duration || 1)}
          disabled={
            !state.duration ||
            state.status === "loading" ||
            state.status === "error"
          }
          onChange={(e) => controller.seek(Number(e.target.value))}
          aria-valuetext={`${time(state.currentTime)} of ${time(state.duration)}`}
        />
        <span className="font-mono text-xs text-slate-400">
          {time(state.currentTime)} /{" "}
          {state.duration ? time(state.duration) : "—:—"}
        </span>
      </div>
      <div className="narration-bottom">
        <p role="status" className="text-xs text-slate-400">
          {state.status === "loading"
            ? "Preparing natural narration…"
            : state.status === "ended"
              ? "Narration complete"
              : state.status === "paused"
                ? "Paused"
                : state.status === "error"
                  ? "Audio unavailable"
                  : "Reading"}{" "}
          · Segment {state.index + 1} of {state.chunks.length}
        </p>
        <progress
          aria-label="Overall narration progress"
          className="progress-track"
          value={progress}
          max={100}
        />
      </div>
      {state.error && (
        <p role="alert" className="narration-error">
          {state.error}
        </p>
      )}
    </section>
  );
}
