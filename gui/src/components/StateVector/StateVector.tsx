import React from 'react';
import { useJobStore } from '../../stores/jobStore';

export default function StateVector() {
  const { activeJobId, results } = useJobStore();
  const data = activeJobId ? results[activeJobId] : null;

  if (!data?.counts) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)]">
        <span className="text-3xl mb-2 opacity-20">|ψ⟩</span>
        <span className="text-[11px]">Run a circuit to see state vector</span>
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
      <div className="px-3 py-1.5 border-t border-white/5 text-[10px] text-[var(--text-muted)]">
        {entries.length} states · {total} shots
      </div>
    </div>
  );
}
