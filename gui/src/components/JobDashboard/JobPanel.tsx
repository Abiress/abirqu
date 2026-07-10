import React from 'react';
import { useJobStore } from '../../stores/jobStore';

export default function JobDashboard() {
  const { jobs, activeJobId, setActiveJob } = useJobStore();

  const statusConfig: Record<string, { icon: string; color: string; bg: string }> = {
    completed: { icon: '✓', color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
    running: { icon: '⟳', color: 'text-amber-400', bg: 'bg-amber-400/10' },
    failed: { icon: '✗', color: 'text-red-400', bg: 'bg-red-400/10' },
    cancelled: { icon: '⊘', color: 'text-slate-400', bg: 'bg-slate-400/10' },
    pending: { icon: '○', color: 'text-slate-500', bg: 'bg-slate-500/10' },
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto p-1.5">
        {jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)]">
            <span className="text-2xl mb-2 opacity-30">📋</span>
            <span className="text-[11px]">No jobs yet</span>
            <span className="text-[10px] opacity-50 mt-0.5">Click Run to execute a circuit</span>
          </div>
        ) : (
          <div className="space-y-1">
            {jobs.map((job) => {
              const cfg = statusConfig[job.status] || statusConfig.pending;
              return (
                <button
                  key={job.job_id}
                  onClick={() => setActiveJob(job.job_id)}
                  className={`w-full text-left p-2 rounded-lg text-xs transition-all duration-150 ${
                    activeJobId === job.job_id
                      ? 'bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20'
                      : 'panel-hover border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold ${cfg.bg} ${cfg.color}`}>
                      {cfg.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-[var(--text-primary)] truncate">{job.job_id.slice(0, 8)}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">{job.backend} · {job.shots} shots</div>
                    </div>
                  </div>
                  {job.status === 'running' && (
                    <div className="mt-1.5 h-1 bg-[var(--bg-input)] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress * 100}%` }}
                      />
                    </div>
                  )}
                  {job.error && (
                    <div className="mt-1 text-[10px] text-red-400 truncate">{job.error}</div>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {jobs.length > 0 && (
        <div className="p-2 border-t border-white/5">
          <button
            onClick={() => useJobStore.getState().clearJobs()}
            className="w-full text-[10px] text-[var(--text-muted)] hover:text-red-400 transition-colors"
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}
