import React, { useState, useEffect, useCallback } from 'react';
import { useHardwareStore, NoiseConfig } from '../../stores/hardwareStore';
import { useCircuitStore } from '../../stores/circuitStore';
import { api } from '../../api/commands';

const PRESETS: { name: string; config: NoiseConfig }[] = [
  { name: 'Noiseless', config: { depolarizing: 0, amplitudeDamping: 0, phaseDamping: 0, readoutError: 0, enabled: false } },
  { name: 'IBM Nairobi', config: { depolarizing: 0.005, amplitudeDamping: 0.01, phaseDamping: 0.008, readoutError: 0.02, enabled: true } },
  { name: 'Google Sycamore', config: { depolarizing: 0.003, amplitudeDamping: 0.005, phaseDamping: 0.004, readoutError: 0.015, enabled: true } },
  { name: 'Heavy Noise', config: { depolarizing: 0.05, amplitudeDamping: 0.08, phaseDamping: 0.06, readoutError: 0.1, enabled: true } },
];

export interface NoiseLabResult {
  tvd: number;
  ideal_distribution: Record<string, number>;
  noisy_distribution: Record<string, number>;
  calibration: {
    gate_fidelity: number;
    readout_fidelity: number;
    purity_retention: number;
    depolarizing: number;
    amplitude_damping: number;
    phase_damping: number;
    readout_error: number;
  };
}

export default function NoisePanel() {
  const [expanded, setExpanded] = useState(true);
  const { noiseConfig, setNoiseConfig } = useHardwareStore();
  const { getCircuitData, numQubits } = useCircuitStore();

  const [labResult, setLabResult] = useState<NoiseLabResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const update = (partial: Partial<NoiseConfig>) => {
    setNoiseConfig({ ...noiseConfig, ...partial });
  };

  const runAnalysis = useCallback(async () => {
    setAnalyzing(true);
    try {
      const circuit = getCircuitData();
      const res = await api.simulateNoiseLab(circuit, noiseConfig);
      setLabResult(res);
    } catch (e) {
      console.error('Noise lab simulation failed:', e);
    } finally {
      setAnalyzing(false);
    }
  }, [getCircuitData, noiseConfig]);

  useEffect(() => {
    if (noiseConfig.enabled) {
      runAnalysis();
    }
  }, [noiseConfig.enabled, noiseConfig.depolarizing, noiseConfig.amplitudeDamping, noiseConfig.readoutError, numQubits]);

  return (
    <div className="border border-[var(--border)] rounded-xl overflow-hidden bg-[var(--bg-card)] space-y-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-[var(--bg-hover)] transition-colors"
      >
        <span className={`w-2 h-2 rounded-full ${noiseConfig.enabled ? 'bg-amber-400' : 'bg-emerald-400'}`} />
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">Noise Lab & TVD</span>
        <span className="text-[10px] text-[var(--text-muted)] ml-auto">
          {noiseConfig.enabled ? 'Enabled' : 'Disabled'} {expanded ? '▾' : '▸'}
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3 animate-fade-in text-xs">
          {/* Toggle */}
          <div className="flex items-center justify-between">
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
              <span className="text-[11px] text-[var(--text-secondary)] font-medium">Enable noise simulation</span>
            </label>

            {noiseConfig.enabled && (
              <button
                onClick={runAnalysis}
                disabled={analyzing}
                className="px-2 py-0.5 rounded text-[10px] font-semibold bg-violet-600/20 text-violet-400 border border-violet-500/30 hover:bg-violet-600/30"
              >
                {analyzing ? 'Simulating...' : 'Recalculate'}
              </button>
            )}
          </div>

          {/* Presets */}
          <div className="flex gap-1 flex-wrap">
            {PRESETS.map((p) => (
              <button
                key={p.name}
                onClick={() => setNoiseConfig(p.config)}
                className="px-2 py-0.5 rounded text-[9px] font-medium bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-all"
              >
                {p.name}
              </button>
            ))}
          </div>

          {/* Sliders */}
          {noiseConfig.enabled && (
            <div className="space-y-2 bg-[var(--bg-panel)] p-2 rounded-lg border border-[var(--border)]">
              <NoiseSlider label="Depolarizing" value={noiseConfig.depolarizing} max={0.1} onChange={(v) => update({ depolarizing: v })} />
              <NoiseSlider label="Amplitude Damping" value={noiseConfig.amplitudeDamping} max={0.1} onChange={(v) => update({ amplitudeDamping: v })} />
              <NoiseSlider label="Phase Damping" value={noiseConfig.phaseDamping} max={0.1} onChange={(v) => update({ phaseDamping: v })} />
              <NoiseSlider label="Readout Error" value={noiseConfig.readoutError} max={0.2} onChange={(v) => update({ readoutError: v })} />
            </div>
          )}

          {/* Total Variation Distance & Calibration Card */}
          {noiseConfig.enabled && labResult && (
            <div className="space-y-2 pt-1 border-t border-[var(--border)]">
              {/* TVD Metric Display */}
              <div className="p-2.5 rounded-lg bg-[var(--bg-panel)] border border-[var(--border)] flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block font-semibold">
                    Total Variation Distance
                  </span>
                  <span className="text-[13px] font-mono font-black text-[var(--text-primary)]">
                    TVD = {labResult.tvd.toFixed(4)}
                  </span>
                </div>
                <span className={`px-2 py-1 rounded text-[10px] font-mono font-bold ${
                  labResult.tvd < 0.05
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : labResult.tvd < 0.15
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-red-500/20 text-red-400 border border-red-500/30'
                }`}>
                  {labResult.tvd < 0.05 ? 'Low Distortion' : labResult.tvd < 0.15 ? 'Moderate Noise' : 'Severe Decoherence'}
                </span>
              </div>

              {/* Calibration Summary */}
              <div className="grid grid-cols-3 gap-1 text-center font-mono text-[9px] bg-[var(--bg-panel)] p-2 rounded border border-[var(--border)]">
                <div>
                  <span className="text-[var(--text-muted)] block text-[8px]">F_gate</span>
                  <span className="text-emerald-400 font-semibold">
                    {(labResult.calibration.gate_fidelity * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)] block text-[8px]">F_readout</span>
                  <span className="text-sky-400 font-semibold">
                    {(labResult.calibration.readout_fidelity * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-[var(--text-muted)] block text-[8px]">Purity Retention</span>
                  <span className="text-purple-400 font-semibold">
                    {(labResult.calibration.purity_retention * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Side-by-side Ideal vs Noisy Distribution */}
              <div className="space-y-1 bg-[var(--bg-panel)] p-2 rounded border border-[var(--border)]">
                <div className="flex items-center justify-between text-[10px] font-semibold text-[var(--text-muted)] pb-1">
                  <span>Ideal vs Noisy Probabilities</span>
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-violet-500" /> Ideal
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-amber-400" /> Noisy
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {Object.keys(labResult.ideal_distribution)
                    .slice(0, 16)
                    .map((state) => {
                      const pIdeal = labResult.ideal_distribution[state] || 0;
                      const pNoisy = labResult.noisy_distribution[state] || 0;
                      const maxP = Math.max(0.01, ...Object.values(labResult.ideal_distribution));

                      return (
                        <div key={state} className="space-y-0.5">
                          <div className="flex justify-between font-mono text-[9px] text-[var(--text-muted)]">
                            <span className="font-bold text-violet-400">|{state}⟩</span>
                            <span>
                              {(pIdeal * 100).toFixed(1)}% → {(pNoisy * 100).toFixed(1)}%
                            </span>
                          </div>
                          {/* Ideal Bar */}
                          <div className="w-full h-1.5 bg-[var(--bg-input)] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-violet-500 rounded-full"
                              style={{ width: `${(pIdeal / maxP) * 100}%` }}
                            />
                          </div>
                          {/* Noisy Bar */}
                          <div className="w-full h-1.5 bg-[var(--bg-input)] rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-400 rounded-full"
                              style={{ width: `${(pNoisy / maxP) * 100}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
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
