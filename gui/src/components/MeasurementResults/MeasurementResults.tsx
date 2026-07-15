import React from 'react';
import { useJobStore } from '../../stores/jobStore';

interface Props { compact?: boolean; }

export default function MeasurementResults({ compact = false }: Props) {
  const { activeJobId, results } = useJobStore();
  const data = activeJobId ? results[activeJobId] : null;

  if (!data?.counts) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)]">
        <span className="text-3xl mb-2 opacity-20">📊</span>
        <span className="text-[11px]">No measurement data yet</span>
      </div>
    );
  }

  const counts = data.counts as Record<string, number>;
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const entries = Object.entries(counts)
    .map(([state, count]) => ({ state, count, prob: count / total }))
    .sort((a, b) => b.count - a.count);
  const maxCount = entries.length > 0 ? Math.max(...entries.map((e) => e.count)) : 0;
  const numQubits = entries[0]?.state.length || 0;

  // Per-qubit bias
  const qubitStats = [];
  for (let q = 0; q < numQubits; q++) {
    let p0 = 0;
    for (const { state, count } of entries) {
      if (state[q] === '0') p0 += count;
    }
    qubitStats.push({ qubit: q, p0: p0 / total, p1: 1 - p0 / total });
  }

  // Entropy
  const entropy = -entries.reduce((sum, e) => {
    const p = e.prob;
    return sum + (p > 1e-10 ? p * Math.log2(p) : 0);
  }, 0);
  const maxEntropy = Math.log2(entries.length || 1);

  return (
    <div className="flex flex-col h-full overflow-auto p-3 space-y-4">
      {/* Histogram */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">Distribution</span>
          <span className="text-[10px] text-[var(--text-muted)]">{total} shots</span>
        </div>
        <div className="space-y-1">
          {entries.map(({ state, count, prob }, i) => (
            <div key={state} className="flex items-center gap-2 animate-fade-in" style={{ animationDelay: `${i * 20}ms` }}>
              <span className="text-[10px] font-mono text-[var(--accent-primary)] w-12 text-right">{state}</span>
              <div className="flex-1 h-5 bg-[var(--bg-input)] rounded-md overflow-hidden relative">
                <div
                  className="h-full rounded-md transition-all duration-500"
                  style={{
                    width: `${(count / maxCount) * 100}%`,
                    background: `linear-gradient(90deg, #8b5cf6, #c084fc)`,
                  }}
                />
                <span className="absolute inset-0 flex items-center justify-center text-[9px] font-mono text-white/80 mix-blend-difference font-medium">
                  {count}
                </span>
              </div>
              <span className="text-[9px] text-[var(--text-muted)] w-10 text-right font-mono">
                {(prob * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Per-qubit bias */}
      {!compact && qubitStats.length > 0 && (
        <div>
          <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium mb-2">Per-Qubit Bias</div>
          <div className="flex gap-2">
            {qubitStats.map(({ qubit, p0, p1 }) => (
              <div key={qubit} className="flex-1 text-center">
                <div className="text-[9px] text-[var(--text-muted)] mb-1">q{qubit}</div>
                <div className="h-16 bg-[var(--bg-input)] rounded-lg relative overflow-hidden">
                  <div
                    className="absolute bottom-0 left-0 right-0 rounded-b-lg transition-all duration-500"
                    style={{
                      height: `${p1 * 100}%`,
                      background: 'linear-gradient(to top, #8b5cf6, #a78bfa)',
                    }}
                  />
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-[9px] font-mono">
                    <span className="text-emerald-400 font-medium">{(p0 * 100).toFixed(0)}%</span>
                    <span className="text-red-400 font-medium">{(p1 * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      {!compact && (
        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Shots" value={String(total)} />
          <StatCard label="States" value={String(entries.length)} />
          <StatCard label="Entropy" value={`${entropy.toFixed(2)} bits`} />
          <StatCard label="Most likely" value={entries[0]?.state || '-'} highlight />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
      <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">{label}</div>
      <div className={`text-xs font-medium mt-0.5 ${highlight ? 'text-[var(--accent-primary)]' : 'text-[var(--text-primary)]'}`}>
        {value}
      </div>
    </div>
  );
}
