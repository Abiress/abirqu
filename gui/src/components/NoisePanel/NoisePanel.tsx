import React, { useState } from 'react';
import { useHardwareStore, NoiseConfig } from '../../stores/hardwareStore';

const PRESETS: { name: string; config: NoiseConfig }[] = [
  { name: 'Noiseless', config: { depolarizing: 0, amplitudeDamping: 0, phaseDamping: 0, readoutError: 0, enabled: false } },
  { name: 'IBM Nairobi', config: { depolarizing: 0.005, amplitudeDamping: 0.01, phaseDamping: 0.008, readoutError: 0.02, enabled: true } },
  { name: 'Google Sycamore', config: { depolarizing: 0.003, amplitudeDamping: 0.005, phaseDamping: 0.004, readoutError: 0.015, enabled: true } },
  { name: 'Heavy Noise', config: { depolarizing: 0.05, amplitudeDamping: 0.08, phaseDamping: 0.06, readoutError: 0.1, enabled: true } },
];

export default function NoisePanel() {
  const [expanded, setExpanded] = useState(false);
  const { noiseConfig, setNoiseConfig } = useHardwareStore();

  const update = (partial: Partial<NoiseConfig>) => {
    setNoiseConfig({ ...noiseConfig, ...partial });
  };

  return (
    <div className="border border-white/5 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-white/[0.02] transition-colors"
      >
        <span className={`w-2 h-2 rounded-full ${noiseConfig.enabled ? 'bg-amber-400' : 'bg-emerald-400'}`} />
        <span className="text-[11px] font-medium text-[var(--text-primary)]">Noise Model</span>
        <span className="text-[9px] text-[var(--text-muted)] ml-auto">
          {noiseConfig.enabled ? 'Enabled' : 'Disabled'} {expanded ? '▾' : '▸'}
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3 animate-fade-in">
          {/* Enable/disable */}
          <label className="flex items-center gap-2 cursor-pointer">
            <div
              onClick={() => update({ enabled: !noiseConfig.enabled })}
              className={`w-8 h-4 rounded-full transition-colors relative ${
                noiseConfig.enabled ? 'bg-[var(--accent-primary)]' : 'bg-[var(--bg-input)]'
              }`}
            >
              <div
                className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
                  noiseConfig.enabled ? 'translate-x-4' : 'translate-x-0.5'
                }`}
              />
            </div>
            <span className="text-[10px] text-[var(--text-secondary)]">Enable noise simulation</span>
          </label>

          {/* Presets */}
          <div className="flex gap-1 flex-wrap">
            {PRESETS.map((p) => (
              <button
                key={p.name}
                onClick={() => setNoiseConfig(p.config)}
                className="px-2 py-0.5 rounded text-[9px] font-medium bg-[var(--bg-input)] border border-white/5 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-white/10 transition-all"
              >
                {p.name}
              </button>
            ))}
          </div>

          {/* Sliders */}
          {noiseConfig.enabled && (
            <div className="space-y-2">
              <NoiseSlider label="Depolarizing" value={noiseConfig.depolarizing} max={0.1} onChange={(v) => update({ depolarizing: v })} />
              <NoiseSlider label="Amplitude Damping" value={noiseConfig.amplitudeDamping} max={0.1} onChange={(v) => update({ amplitudeDamping: v })} />
              <NoiseSlider label="Phase Damping" value={noiseConfig.phaseDamping} max={0.1} onChange={(v) => update({ phaseDamping: v })} />
              <NoiseSlider label="Readout Error" value={noiseConfig.readoutError} max={0.2} onChange={(v) => update({ readoutError: v })} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function NoiseSlider({ label, value, max, onChange }: { label: string; value: number; max: number; onChange: (v: number) => void }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] text-[var(--text-muted)] w-24 truncate">{label}</span>
      <input
        type="range"
        min={0}
        max={max}
        step={max / 100}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="flex-1 h-1 accent-[var(--accent-primary)]"
      />
      <span className="text-[9px] text-[var(--text-secondary)] w-12 text-right font-mono">
        {(value * 100).toFixed(1)}%
      </span>
    </div>
  );
}
