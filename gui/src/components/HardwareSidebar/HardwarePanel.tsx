import React, { useEffect } from 'react';
import { useHardwareStore } from '../../stores/hardwareStore';
import { api } from '../../api/commands';

export default function HardwareSidebar() {
  const { backends, selectedBackend, setBackends, selectBackend } = useHardwareStore();

  useEffect(() => {
    api.listHardware().then(setBackends).catch(console.error);
  }, [setBackends]);

  const providers = [...new Set(backends.map((b) => b.provider))];

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
                        b.status === 'online' ? 'bg-emerald-400' :
                        b.status === 'offline' ? 'bg-red-400' : 'bg-amber-400'
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
                      b.backend_type === 'real' ? 'text-amber-400' :
                      b.backend_type === 'hybrid' ? 'text-cyan-400' : ''
                    }>
                      {b.backend_type}
                    </span>
                  </div>
                </button>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}
