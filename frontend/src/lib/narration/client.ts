import { API_URL } from "../api";
import { NORMALIZATION_VERSION } from "./text";

type Config = { available: boolean; version: string; voice: string };
const MAX_BYTES = 24 * 1024 * 1024;
const TTL = 30 * 60 * 1000;
const cache = new Map<string, { blob: Blob; created: number }>();
let bytes = 0;
let config: Config | undefined;
let checkedAt = 0;

export async function loadNarrationAudio(
  text: string,
  signal: AbortSignal,
): Promise<Blob> {
  try {
    if (!config || Date.now() - checkedAt > 60000) {
      const response = await fetch(`${API_URL}/api/speech/config`, { signal });
      if (!response.ok) throw new Error();
      config = await response.json();
      checkedAt = Date.now();
    }
    if (!config?.available) throw new Error("unavailable");
    const key = `${config.version}|${NORMALIZATION_VERSION}|${text}`;
    for (const [id, entry] of Array.from(cache)) {
      if (Date.now() - entry.created > TTL) {
        bytes -= entry.blob.size;
        cache.delete(id);
      }
    }
    const existing = cache.get(key);
    if (existing) {
      cache.delete(key);
      cache.set(key, existing);
      return existing.blob;
    }
    const response = await fetch(`${API_URL}/api/speech`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal,
    });
    if (!response.ok)
      throw new Error(response.status === 429 ? "busy" : "unavailable");
    if (!response.headers.get("content-type")?.includes("audio/"))
      throw new Error();
    const blob = await response.blob();
    if (!blob.size || blob.size > 8 * 1024 * 1024) throw new Error();
    signal.throwIfAborted();
    while (bytes + blob.size > MAX_BYTES && cache.size) {
      const first = cache.keys().next().value as string;
      bytes -= cache.get(first)!.blob.size;
      cache.delete(first);
    }
    cache.set(key, { blob, created: Date.now() });
    bytes += blob.size;
    return blob;
  } catch (error) {
    if (signal.aborted) throw error;
    // Never display upstream response bodies. Let retry re-check provider configuration.
    config = undefined;
    throw new Error(
      error instanceof Error && error.message === "busy"
        ? "Narration is busy. Please wait a moment, then retry."
        : "Narration is unavailable right now. Keep reading, or try again.",
    );
  }
}
