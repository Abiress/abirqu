import React, { useState, useRef, useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';

export default function Console() {
  const [lines, setLines] = useState<{ text: string; type: 'info' | 'error' | 'success' }[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unlisten = listen<string>('python-output', (event) => {
      setLines((prev) => [...prev.slice(-200), { text: event.payload, type: 'info' }]);
    });
    return () => { unlisten.then((fn) => fn()); };
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [lines]);

  const colors = {
    info: 'text-[var(--text-secondary)]',
    error: 'text-red-400',
    success: 'text-emerald-400',
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
