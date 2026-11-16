import React from 'react';
import { useJobStore } from '../../stores/jobStore';

export default function StateVector() {
  const { activeJobId, results } = useJobStore();
  const data = activeJobId ? results[activeJobId] : null;

  if (!data?.counts && !data?.statevector) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)]">
        <span className="text-3xl mb-2 opacity-20">|ψ⟩</span>
        <span className="text-[11px]">Run or step a circuit to see state vector</span>
      </div>
    );
  }

  // If exact statevector amplitudes are available
  if (Array.isArray(data?.statevector) && data.statevector.length > 0) {
    const sv = data.statevector;
    return (
      <div className="flex flex-col h-full">
        <div className="px-3 py-1.5 border-b border-[var(--border)] bg-[var(--bg-card)] flex justify-between items-center text-[10px] text-[var(--text-muted)]">
          <span className="font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Exact Statevector</span>
          <span>{sv.length} Amplitudes</span>
        </div>
        <div className="flex-1 overflow-auto p-3 space-y-2">
          {sv.map((entry: any, i: number) => {
            const hue = Math.round(((entry.phase + Math.PI) / (2 * Math.PI)) * 360);
            const barColor = `hsl(${hue}, 85%, 55%)`;
            const phaseDeg = ((entry.phase * 180) / Math.PI).toFixed(1);

            return (
              <div key={entry.basis || i} className="p-1.5 rounded bg-[var(--bg-card)] border border-[var(--border)] space-y-1">
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="font-bold text-violet-400">|{entry.basis}⟩</span>
                  <span className="text-[10px] text-[var(--text-muted)]">
                    {(entry.probability * 100).toFixed(2)}%
                  </span>
                </div>

                <div className="w-full h-3 bg-[var(--bg-input)] rounded overflow-hidden relative">
                  <div
                    className="h-full rounded transition-all duration-300"
                    style={{
                      width: `${Math.max(entry.magnitude > 1e-6 ? 4 : 0, entry.magnitude * 100)}%`,
                      backgroundColor: barColor,
                    }}
                  />
                  <span className="absolute inset-0 flex items-center justify-center text-[9px] font-mono font-semibold text-white/90 mix-blend-difference">
                    |α| = {entry.magnitude.toFixed(4)}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[9px] text-[var(--text-muted)] font-mono">
                  <span>
                    α = {entry.real >= 0 ? '+' : ''}{entry.real.toFixed(4)} {entry.imag >= 0 ? '+' : ''}{entry.imag.toFixed(4)}i
                  </span>
                  <span>θ = {phaseDeg}°</span>
                </div>
              </div>
            );
          })}
        </div>
        <div className="px-3 py-1.5 border-t border-[var(--border)] text-[10px] text-[var(--text-muted)] font-mono">
          Phase mapped: -π (Red) → 0 (Cyan) → +π (Red)
        </div>
      </div>
    );
  }

  const counts = data.counts as Record<string, number>;
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const entries = Object.entries(counts)
    .map(([state, count]) => ({ state, count, prob: count / total }))
    .sort((a, b) => b.prob - a.prob);

  const maxProb = Math.max(...entries.map((e) => e.prob));

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto p-3 space-y-1.5">
        {entries.map(({ state, count, prob }, i) => (
          <div key={state} className="flex items-center gap-2 animate-fade-in" style={{ animationDelay: `${i * 30}ms` }}>
            <span className="text-[11px] font-mono text-[var(--accent-primary)] w-16 text-right">
              |{state}⟩
            </span>
            <div className="flex-1 h-5 bg-[var(--bg-input)] rounded-md overflow-hidden relative">
              <div
                className="h-full rounded-md transition-all duration-500 ease-out"
                style={{
                  width: `${(prob / maxProb) * 100}%`,
                  background: `linear-gradient(90deg, #8b5cf6, #a78bfa)`,
                }}
              />
              <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-white/80 mix-blend-difference font-medium">
                {(prob * 100).toFixed(1)}%
              </span>
            </div>
            <span className="text-[10px] text-[var(--text-muted)] w-10 text-right font-mono">
              {count}
            </span>
          </div>
        ))}
      </div>
      <div className="px-3 py-1.5 border-t border-[var(--border)] text-[10px] text-[var(--text-muted)]">
        {entries.length} states · {total} shots
      </div>
    </div>
  );
}
