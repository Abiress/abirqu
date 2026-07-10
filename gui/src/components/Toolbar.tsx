import React, { useCallback, useState } from 'react';
import { useCircuitStore } from '../stores/circuitStore';
import { useJobStore } from '../stores/jobStore';
import { useHardwareStore } from '../stores/hardwareStore';
import { useThemeStore } from '../stores/themeStore';
import { api } from '../api/commands';

interface ToolbarProps {
  onExport?: () => void;
}

export default function Toolbar({ onExport }: ToolbarProps) {
  const { numQubits, setNumQubits, clearCircuit, getCircuitData } = useCircuitStore();
  const { addJob, updateJob, setResults } = useJobStore();
  const { selectedBackend, backends } = useHardwareStore();
  const { theme, toggleTheme } = useThemeStore();
  const [running, setRunning] = useState(false);
  const [shots, setShots] = useState(1024);

  const handleRun = useCallback(async () => {
    if (running) return;
    setRunning(true);
    try {
      const circuit = getCircuitData();
      const job = await api.executeCircuit(circuit, selectedBackend, shots);
      addJob(job);

      // Poll for completion
      const poll = async () => {
        try {
          const status = await api.getJobStatus(job.job_id);
          updateJob(status);
          if (status.status === 'completed') {
            const results = await api.getResults(job.job_id);
            setResults(job.job_id, results);
            setRunning(false);
          } else if (status.status === 'failed') {
            setRunning(false);
          } else {
            setTimeout(poll, 200);
          }
        } catch {
          setRunning(false);
        }
      };
      setTimeout(poll, 300);
    } catch (err) {
      console.error('Execute failed:', err);
      setRunning(false);
    }
  }, [running, selectedBackend, shots, getCircuitData, addJob, updateJob, setResults]);

  const handleStop = useCallback(() => {
    const { activeJobId } = useJobStore.getState();
    if (activeJobId) {
      api.cancelJob(activeJobId).catch(() => {});
      setRunning(false);
    }
  }, []);

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-panel)] border-b border-white/5">
      {/* Logo */}
      <div className="flex items-center gap-2 mr-2">
        <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
          <span className="text-white text-[10px] font-black">Q</span>
        </div>
        <span className="text-sm font-bold bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
          AbirQu
        </span>
      </div>

      <div className="w-px h-5 bg-white/5" />

      {/* File actions */}
      <ToolBtn label="New" onClick={clearCircuit} icon="📄" />
      <ToolBtn label="Save" onClick={() => {}} icon="💾" />
      <ToolBtn label="Export" onClick={onExport || (() => {})} icon="📤" />

      <div className="w-px h-5 bg-white/5" />

      {/* Run controls */}
      <button
        onClick={handleRun}
        disabled={running}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
          running
            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse'
            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/10'
        }`}
      >
        {running ? (
          <span className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
        ) : (
          <span className="text-[10px]">▶</span>
        )}
        {running ? 'Running...' : 'Run'}
      </button>

      <button
        onClick={handleStop}
        disabled={!running}
        className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
      >
        <span className="text-[10px]">■</span>
        Stop
      </button>

      <div className="w-px h-5 bg-white/5" />

      {/* Qubits */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Qubits</span>
        <select
          value={numQubits}
          onChange={(e) => setNumQubits(Number(e.target.value))}
          className="bg-[var(--bg-input)] text-[var(--text-primary)] border border-white/5 rounded-md px-2 py-1 text-xs focus:border-[var(--border-focus)] focus:outline-none transition-colors"
        >
          {[1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 16].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      {/* Shots */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Shots</span>
        <select
          value={shots}
          onChange={(e) => setShots(Number(e.target.value))}
          className="bg-[var(--bg-input)] text-[var(--text-primary)] border border-white/5 rounded-md px-2 py-1 text-xs focus:border-[var(--border-focus)] focus:outline-none transition-colors"
        >
          {[64, 128, 256, 512, 1024, 2048, 4096, 8192].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      <div className="flex-1" />

      {/* Backend */}
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Backend</span>
        <select
          value={selectedBackend}
          onChange={(e) => useHardwareStore.getState().selectBackend(e.target.value)}
          className="bg-[var(--bg-input)] text-[var(--text-primary)] border border-white/5 rounded-md px-2 py-1 text-xs max-w-[180px] focus:border-[var(--border-focus)] focus:outline-none transition-colors"
        >
          {backends.map((b) => (
            <option key={b.name} value={b.name}>{b.name}</option>
          ))}
        </select>
      </div>

      <div className="w-px h-5 bg-white/5" />

      {/* Theme */}
      <button
        onClick={toggleTheme}
        className="w-7 h-7 rounded-lg flex items-center justify-center text-sm bg-[var(--bg-input)] border border-white/5 hover:bg-[var(--border)] hover:border-white/10 transition-all"
      >
        {theme === 'dark' ? '☀️' : '🌙'}
      </button>
    </div>
  );
}

function ToolBtn({ label, onClick, icon }: { label: string; onClick: () => void; icon: string }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-[var(--text-secondary)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] transition-all"
    >
      <span className="text-[10px]">{icon}</span>
      {label}
    </button>
  );
}
