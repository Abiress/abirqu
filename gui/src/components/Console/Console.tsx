import React, { useState, useRef, useEffect } from 'react';
import { api } from '../../api/commands';

interface ConsoleLine {
  text: string;
  type: 'info' | 'error' | 'success';
  jobId?: string;
}

export default function Console() {
  const [lines, setLines] = useState<ConsoleLine[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const seenJobs = useRef<Set<string>>(new Set());

  useEffect(() => {
    const poll = async () => {
      try {
        const jobs = await api.listJobs();
        for (const job of jobs) {
          const id = job.job_id;
          if (!id) continue;
          const key = `${id}:${job.status}`;
          if (seenJobs.current.has(key)) continue;
          seenJobs.current.add(key);

          if (job.status === 'running' || job.status === 'pending') {
            setLines((prev) => [...prev.slice(-200), {
              text: `[${id.slice(0, 8)}] ${job.status} on ${job.backend} (${job.shots} shots)`,
              type: 'info',
              jobId: id,
            }]);
          } else if (job.status === 'completed') {
            setLines((prev) => [...prev.slice(-200), {
              text: `[${id.slice(0, 8)}] completed on ${job.backend}`,
              type: 'success',
              jobId: id,
            }]);
          } else if (job.status === 'failed' || job.status === 'error') {
            setLines((prev) => [...prev.slice(-200), {
              text: `[${id.slice(0, 8)}] ${job.error || 'failed'}`,
              type: 'error',
              jobId: id,
            }]);
          }
        }
      } catch {}
    };
    poll();
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [lines]);

  const colors = {
    info: 'text-[var(--text-secondary)]',
    error: 'text-[var(--accent-error)]',
    success: 'text-[var(--accent-success)]',
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto p-2 font-mono text-[11px] leading-relaxed" ref={scrollRef}>
        {lines.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[var(--text-muted)] text-xs">
            <span className="opacity-50">Ready. Run a circuit to see output.</span>
          </div>
        ) : (
          lines.map((line, i) => (
            <div key={i} className={`${colors[line.type]} whitespace-pre-wrap`}>
              <span className="text-[var(--text-muted)] mr-2 select-none">{String(i + 1).padStart(3, ' ')}</span>
              {line.text}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
