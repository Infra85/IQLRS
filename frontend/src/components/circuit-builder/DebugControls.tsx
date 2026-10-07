"use client";
import { Input, Select } from "@/components/ui/input";
import type { DebugSettings } from "@/lib/simulation-trace";

export function DebugControls({ settings, onChange }: { settings: DebugSettings; onChange: (settings: DebugSettings) => void }) {
  return <section className="panel p-5 space-y-4" aria-label="Debug configuration">
    <label className="flex items-center gap-2 text-sm">
      <input type="checkbox" checked={settings.enabled} onChange={e => onChange({ ...settings, enabled: e.target.checked })} />
      Debug execution
    </label>
    {settings.enabled && <>
      <div className="flex flex-wrap items-end gap-4">
        <label className="text-sm">Debug shots (1-based)
          <Input aria-label="Debug shots (1-based)" value={settings.shots} maxLength={160} onChange={e => onChange({ ...settings, shots: e.target.value })} placeholder="1, 3, 8" />
        </label>
        <label className="text-sm">Checkpoints
          <Select aria-label="Checkpoint mode" value={settings.mode} onChange={e => onChange({ ...settings, mode: e.target.value as DebugSettings["mode"] })}>
            <option value="all">All operations</option><option value="selected">Selected operations + events</option>
          </Select>
        </label>
        {settings.mode === "selected" && <label className="text-sm">Operations to inspect (1-based)
          <Input aria-label="Operations to inspect (1-based)" value={settings.operations} maxLength={1500} onChange={e => onChange({ ...settings, operations: e.target.value })} />
        </label>}
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={settings.amplitudes} onChange={e => onChange({ ...settings, amplitudes: e.target.checked })} />Include checkpoint amplitudes</label>
      </div>
      <p className="text-sm text-slate-400">Select up to 16 shots. Start/end, measurement, reset and all classical conditions—including skipped operations—are retained. Limits: 256 checkpoints per shot, 512 total, 32,768 basis probabilities, 64 amplitude snapshots. Large requests must select fewer checkpoints.</p>
      <p className="text-sm text-slate-400">Traces describe individual shots and are returned only for this run. They are not saved to activity history. A seed lets you repeat the execution.</p>
    </>}
  </section>;
}
