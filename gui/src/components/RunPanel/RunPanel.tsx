import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useCircuitStore } from '../../stores/circuitStore';
import { useJobStore } from '../../stores/jobStore';
import { useHardwareStore } from '../../stores/hardwareStore';
import { api, JobInfo } from '../../api/commands';

export interface SimulatorEngine {
  id: string;
  name: string;
  qubitLimit: number;
  description: string;
  type: 'statevector' | 'stabilizer' | 'tensor' | 'monte_carlo';
}

export const SIMULATOR_ENGINES: SimulatorEngine[] = [
  { id: 'statevector', name: 'NumPy Statevector', qubitLimit: 28, description: 'Exact full statevector simulation (CPU)', type: 'statevector' },
  { id: 'gpu', name: 'GPU Statevector', qubitLimit: 32, description: 'High-throughput accelerated statevector (CuPy)', type: 'statevector' },
  { id: 'clifford', name: 'Clifford Tableau', qubitLimit: 1000, description: 'Stabilizer circuits with polynomial scaling', type: 'stabilizer' },
  { id: 'mps', name: 'MPS Tensor Network', qubitLimit: 100, description: 'Matrix product state for low-entanglement circuits', type: 'tensor' },
  { id: 'ttn', name: 'Tree Tensor Network', qubitLimit: 200, description: 'Tree-structured tensor network for multi-qubit systems', type: 'tensor' },
  { id: 'monte_carlo', name: 'Monte Carlo Trajectories', qubitLimit: 24, description: 'Stochastic quantum jumps under open-system dynamics', type: 'monte_carlo' },
];

export default function RunPanel() {
  const { numQubits, getCircuitData } = useCircuitStore();
  const { addJob, updateJob, setResults, activeJobId, jobs } = useJobStore();
  const { selectedBackend, noiseConfig } = useHardwareStore();

  const [simulator, setSimulator] = useState<string>('statevector');
  const [shots, setShots] = useState<number>(1024);
  const [seed, setSeed] = useState<string>('');
  const [running, setRunning] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const pollRef = useRef<number | null>(null);

  const activeJob = activeJobId ? jobs.find((j) => j.job_id === activeJobId) : null;
  const currentEngine = SIMULATOR_ENGINES.find((e) => e.id === simulator) || SIMULATOR_ENGINES[0];
  const isQubitLimitExceeded = numQubits > currentEngine.qubitLimit;

  useEffect(() => {
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  const handleRun = useCallback(async () => {
    if (running || isQubitLimitExceeded) return;
    setErrorMsg(null);
    setRunning(true);
    setProgress(0.1);

    try {
      const circuit = getCircuitData();
      const seedVal = seed.trim() !== '' ? parseInt(seed, 10) : undefined;
      const job: JobInfo = await api.executeCircuit(
        circuit,
        selectedBackend,
        shots,
        noiseConfig,
        simulator,
        seedVal
      );
      addJob(job);

      const poll = async () => {
        try {
          const status = await api.getJobStatus(job.job_id);
          updateJob(status);
          setProgress(status.progress || 0.5);

          if (status.status === 'completed') {
            const results = await api.getResults(job.job_id);
            setResults(job.job_id, results);
            setProgress(1.0);
            setRunning(false);
          } else if (status.status === 'failed' || status.status === 'cancelled') {
            setErrorMsg(status.error || `Execution ${status.status}`);
            setRunning(false);
          } else {
            pollRef.current = window.setTimeout(poll, 150);
          }
        } catch (e: any) {
          setErrorMsg(e?.message || 'Error checking status');
          setRunning(false);
        }
      };

      pollRef.current = window.setTimeout(poll, 150);
    } catch (err: any) {
      setErrorMsg(err?.message || String(err));
      setRunning(false);
    }
  }, [running, isQubitLimitExceeded, getCircuitData, seed, selectedBackend, shots, noiseConfig, simulator, addJob, updateJob, setResults]);

  const handleCancel = useCallback(async () => {
    if (activeJobId) {
      try {
        await api.cancelJob(activeJobId);
      } catch {}
    }
    if (pollRef.current) {
      clearTimeout(pollRef.current);
      pollRef.current = null;
    }
    setRunning(false);
    setErrorMsg('Job cancelled by user');
  }, [activeJobId]);

  return (
    <div className="flex flex-col h-full bg-[var(--bg-panel)] border-r border-[var(--border)] overflow-y-auto p-3 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <span className="text-base">🚀</span>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">Execution & Simulator</h2>
            <p className="text-[10px] text-[var(--text-muted)]">Background worker with engine limits</p>
          </div>
        </div>
        <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-semibold ${
          running ? 'bg-amber-500/20 text-amber-400 animate-pulse border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400'
        }`}>
          {running ? 'RUNNING' : 'IDLE'}
        </span>
      </div>

      {/* Simulator Engine Selection */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-semibold text-[var(--text-secondary)]">Simulation Engine</label>
        <div className="grid grid-cols-1 gap-1.5">
          {SIMULATOR_ENGINES.map((engine) => {
            const isSelected = simulator === engine.id;
            const exceeds = numQubits > engine.qubitLimit;
            return (
              <div
                key={engine.id}
                onClick={() => setSimulator(engine.id)}
                className={`p-2 rounded-lg border text-left cursor-pointer transition-all ${
                  isSelected
                    ? 'border-[var(--accent-primary)] bg-[var(--accent-primary)]/10 text-[var(--text-primary)]'
                    : 'border-[var(--border)] bg-[var(--bg-card)] hover:border-[var(--border-strong)] text-[var(--text-secondary)]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold">{engine.name}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                    exceeds ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-[var(--bg-input)] text-[var(--text-muted)]'
                  }`}>
                    Limit: ≤{engine.qubitLimit}q
                  </span>
                </div>
                <p className="text-[10px] text-[var(--text-muted)] mt-1">{engine.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Qubit Refusal Warning */}
      {isQubitLimitExceeded && (
        <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start gap-2 animate-fade-in">
          <span className="text-sm">⚠️</span>
          <div>
            <span className="font-semibold">Qubit Limit Exceeded:</span>
            <p className="text-[11px] mt-0.5">
              Current circuit has <b>{numQubits}</b> qubits, exceeding {currentEngine.name}'s limit of <b>{currentEngine.qubitLimit}</b> qubits.
              Please choose a tensor network (MPS/TTN) or Clifford simulator.
            </p>
          </div>
        </div>
      )}

      {/* Execution Parameters */}
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1">
          <label className="text-[10px] uppercase font-semibold text-[var(--text-muted)]">Shots</label>
          <select
            value={shots}
            onChange={(e) => setShots(Number(e.target.value))}
            className="w-full bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] rounded-md px-2 py-1.5 text-xs focus:border-[var(--border-focus)] outline-none"
          >
            {[64, 128, 256, 512, 1024, 2048, 4096, 8192].map((n) => (
              <option key={n} value={n}>{n} shots</option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-[10px] uppercase font-semibold text-[var(--text-muted)]">Random Seed</label>
          <input
            type="number"
            placeholder="e.g. 42 (optional)"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            className="w-full bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] rounded-md px-2 py-1.5 text-xs focus:border-[var(--border-focus)] outline-none font-mono"
          />
        </div>
      </div>

      {/* Worker Progress & Status */}
      <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-[var(--text-secondary)] font-medium">Worker Progress</span>
          <span className="font-mono text-[var(--text-muted)]">{Math.round((activeJob?.progress || progress) * 100)}%</span>
        </div>
        <div className="w-full h-2 bg-[var(--bg-input)] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-violet-500 to-purple-600 transition-all duration-300 rounded-full"
            style={{ width: `${Math.max(5, Math.round((activeJob?.progress || progress) * 100))}%` }}
          />
        </div>
        {activeJobId && (
          <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)] font-mono">
            <span>Job ID: {activeJobId.slice(0, 8)}</span>
            <span className="capitalize">{activeJob?.status || 'Processing'}</span>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-2 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2">
        <button
          onClick={handleRun}
          disabled={running || isQubitLimitExceeded}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow transition-all"
        >
          {running ? (
            <>
              <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Running Simulator...
            </>
          ) : (
            <>
              <span>▶</span>
              Run on {currentEngine.name}
            </>
          )}
        </button>

        {running && (
          <button
            onClick={handleCancel}
            className="px-3 py-2 rounded-lg text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-all"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
