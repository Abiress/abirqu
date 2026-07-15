import React from 'react';
import { useCircuitStore } from '../stores/circuitStore';
import { useHardwareStore } from '../stores/hardwareStore';
import { useJobStore } from '../stores/jobStore';

export default function StatusBar() {
  const { numQubits, gates } = useCircuitStore();
  const { selectedBackend } = useHardwareStore();
  const { activeJobId, jobs } = useJobStore();
  const activeJob = jobs.find((j) => j.job_id === activeJobId);

  return (
    <div className="flex items-center gap-4 px-3 py-1 bg-[var(--bg-panel)] border-t border-[var(--border)] text-[10px]">
      <StatusItem
        icon="⚡"
        label="Backend"
        value={selectedBackend}
        color="text-[var(--accent-primary)]"
      />
      <StatusItem icon="◻" label="Qubits" value={String(numQubits)} />
      <StatusItem icon="⊞" label="Gates" value={String(gates.length)} />

      {activeJob && (
        <>
          <div className="w-px h-3 bg-[var(--border)]" />
          <StatusItem
            icon={activeJob.status === 'running' ? '⟳' : activeJob.status === 'completed' ? '✓' : '○'}
            label="Job"
            value={`${activeJob.job_id.slice(0, 8)} · ${activeJob.status}`}
            color={
              activeJob.status === 'completed' ? 'text-[var(--accent-success)]' :
              activeJob.status === 'running' ? 'text-[var(--accent-warning)]' :
              activeJob.status === 'failed' ? 'text-[var(--accent-error)]' : ''
            }
          />
          {activeJob.status === 'running' && (
            <span className="text-[var(--accent-warning)]">{Math.round(activeJob.progress * 100)}%</span>
          )}
        </>
      )}

      <div className="flex-1" />
      <span className="text-[var(--text-muted)]">AbirQu v1.2.3</span>
    </div>
  );
}

function StatusItem({ icon, label, value, color }: { icon: string; label: string; value: string; color?: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className="text-[var(--text-muted)]">{icon}</span>
      <span className="text-[var(--text-muted)]">{label}:</span>
      <span className={color || 'text-[var(--text-primary)]'}>{value}</span>
    </span>
  );
}
