import React, { useEffect, useState } from 'react';
import { useHardwareStore } from '../../stores/hardwareStore';
import { api } from '../../api/commands';

interface Props {
  serverReady?: boolean;
}

export default function HardwareSidebar({ serverReady = false }: Props) {
  const { backends, selectedBackend, setBackends, selectBackend } = useHardwareStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!serverReady) return;
    let cancelled = false;
    const load = async () => {
      for (let i = 0; i < 5; i++) {
        try {
          const data = await api.listHardware();
          if (!cancelled) {
            setBackends(data);
            setLoading(false);
          }
          return;
        } catch {
          await new Promise((r) => setTimeout(r, 800));
        }
      }
      if (!cancelled) setLoading(false);
    };
    load();
    return () => { cancelled = true; };
  }, [serverReady, setBackends]);

  const providers = [...new Set(backends.map((b) => b.provider))];

  if (!serverReady) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)] p-4">
        <span className="text-2xl mb-2 opacity-30">⚡</span>
        <span className="text-[11px] font-medium text-[var(--text-secondary)] mb-1">Server not connected</span>
        <span className="text-[10px] text-center opacity-60">Starting Python backend. Backends will appear once connected.</span>
      </div>
    );
  }

  if (loading && serverReady) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-muted)]">
        <span className="w-3 h-3 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mr-2" />
        <span className="text-[10px]">Loading backends...</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-2 space-y-2 overflow-auto flex-1">
        {providers.map((provider) => (
          <div key={provider} className="animate-fade-in">
            <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest px-1 mb-1 font-semibold">
              {provider}
            </div>
            {backends
              .filter((b) => b.provider === provider)
              .map((b) => (
                <button
                  key={b.name}
                  onClick={() => selectBackend(b.name)}
                  className={`w-full text-left p-2 rounded-lg text-xs transition-all duration-150 mb-0.5 ${
                    selectedBackend === b.name
                      ? 'bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20 shadow-sm shadow-[var(--accent-primary)]/5'
                      : 'panel-hover border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        b.status === 'online' ? 'bg-[var(--accent-success)]' :
                        b.status === 'offline' ? 'bg-[var(--accent-error)]' : 'bg-[var(--accent-warning)]'
                      }`}
                    />
                    <span className="font-medium text-[var(--text-primary)] truncate">
                      {b.name.replace(provider + ' ', '')}
                    </span>
                  </div>
                  <div className="mt-1 ml-3.5 flex items-center gap-2 text-[10px] text-[var(--text-muted)]">
                    <span>{b.num_qubits}q</span>
                    <span>·</span>
                    <span className={
                      b.backend_type === 'real' ? 'text-[var(--accent-warning)]' :
                      b.backend_type === 'hybrid' ? 'text-cyan-400' : ''
                    }>
                      {b.backend_type}
                    </span>
                  </div>
                </button>
              ))}
          </div>
        ))}
        {backends.length === 0 && !loading && (
          <div className="text-center py-8 text-[var(--text-muted)]">
            <span className="text-2xl block mb-2 opacity-30">⚡</span>
            <span className="text-[10px]">No backends available</span>
          </div>
        )}
      </div>

      {selectedBackend && (
        <div className="p-2 border-t border-[var(--border)] bg-[var(--bg-panel)]">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)]" />
            <span className="text-[10px] font-semibold text-[var(--text-primary)]">Active: {selectedBackend}</span>
          </div>
          <div className="text-[9px] text-[var(--text-muted)]">
            {backends.find(b => b.name === selectedBackend)?.num_qubits} qubits · {backends.find(b => b.name === selectedBackend)?.provider}
          </div>
        </div>
      )}
    </div>
  );
}
