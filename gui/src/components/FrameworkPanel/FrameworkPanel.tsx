import React, { useState, useEffect, useCallback } from 'react';
import { useCircuitStore } from '../../stores/circuitStore';
import { useJobStore } from '../../stores/jobStore';
import { useHardwareStore } from '../../stores/hardwareStore';
import { api } from '../../api/commands';

type Framework = 'abirqu' | 'qiskit' | 'cirq' | 'oqtopus' | 'dwave';

const FRAMEWORK_INFO: Record<Framework, { name: string; icon: string; color: string; desc: string }> = {
  abirqu: { name: 'AbirQu', icon: 'Q', color: '#8b5cf6', desc: 'Native simulator' },
  qiskit: { name: 'Qiskit', icon: 'Q', color: '#6929c4', desc: 'IBM Aer simulator' },
  cirq: { name: 'Cirq', icon: 'C', color: '#4285f4', desc: 'Google simulator' },
  oqtopus: { name: 'OQTOPUS', icon: 'O', color: '#00a651', desc: 'OQTOPUS cloud' },
  dwave: { name: 'D-Wave', icon: 'D', color: '#0085ff', desc: 'Quantum annealing' },
};

export default function FrameworkPanel() {
  const [activeFramework, setActiveFramework] = useState<Framework>('abirqu');
  const [frameworkStatus, setFrameworkStatus] = useState<Record<string, { installed: boolean }>>({});
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const { getCircuitData } = useCircuitStore();
  const { addJob, updateJob, setResults } = useJobStore();
  const { selectedBackend } = useHardwareStore();

  useEffect(() => {
    api.getFrameworks().then(setFrameworkStatus).catch(() => {});
  }, []);

  const handleRun = useCallback(async () => {
    if (running) return;
    setRunning(true);
    setLastResult(null);
    const circuit = getCircuitData();
    try {
      let result: any;
      switch (activeFramework) {
        case 'qiskit':
          result = await api.runQiskit(circuit, 1024);
          break;
        case 'cirq':
          result = await api.runCirq(circuit, 1024);
          break;
        case 'oqtopus':
          result = await api.runOqtopus(circuit, 1024);
          break;
        case 'dwave':
          result = await api.runDwave(circuit, 1024);
          break;
        default:
          result = await api.executeCircuit(circuit, selectedBackend, 1024);
          if (result?.job_id) {
            addJob(result);
            const poll = async () => {
              const status = await api.getJobStatus(result.job_id);
              updateJob(status);
              if (status.status === 'completed') {
                const r = await api.getResults(result.job_id);
                setResults(result.job_id, r);
                setLastResult(r);
                setRunning(false);
              } else if (status.status === 'failed') {
                setRunning(false);
              } else {
                setTimeout(poll, 200);
              }
            };
            setTimeout(poll, 300);
            return;
          }
          break;
      }
      setLastResult(result);
    } catch (err) {
      setLastResult({ error: String(err) });
    }
    setRunning(false);
  }, [running, activeFramework, getCircuitData, selectedBackend, addJob, updateJob, setResults]);

  const fw = FRAMEWORK_INFO[activeFramework];
  const counts = lastResult?.counts || lastResult?.data?.counts;
  const total = counts ? Object.values(counts as Record<string, number>).reduce((a: number, b: number) => a + b, 0) : 0;

  return (
    <div className="flex flex-col h-full">
      {/* Framework tabs */}
      <div className="flex border-b border-[var(--border)] bg-[var(--bg-panel)]">
        {(Object.keys(FRAMEWORK_INFO) as Framework[]).map((key) => {
          const f = FRAMEWORK_INFO[key];
          const installed = key === 'abirqu' || frameworkStatus[key]?.installed !== false;
          return (
            <button
              key={key}
              onClick={() => setActiveFramework(key)}
              className={`flex items-center gap-1.5 px-3 py-2 text-[11px] font-medium transition-all border-b-2 ${
                activeFramework === key
                  ? 'border-current text-current bg-current/5'
                  : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
              }`}
              style={{ color: activeFramework === key ? f.color : undefined }}
            >
              <span
                className="w-5 h-5 rounded flex items-center justify-center text-[9px] font-black text-white"
                style={{ backgroundColor: f.color }}
              >
                {f.icon}
              </span>
              {f.name}
              {!installed && <span className="text-[8px] text-[var(--accent-warning)]">!</span>}
            </button>
          );
        })}
      </div>

      {/* Framework info + run */}
      <div className="p-3 space-y-3 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <span
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black text-white"
            style={{ backgroundColor: fw.color }}
          >
            {fw.icon}
          </span>
          <div>
            <div className="text-xs font-semibold" style={{ color: fw.color }}>{fw.name} Backend</div>
            <div className="text-[10px] text-[var(--text-muted)]">{fw.desc}</div>
          </div>
          <div className="flex-1" />
          <button
            onClick={handleRun}
            disabled={running}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              running
                ? 'animate-pulse text-white border'
                : 'text-white hover:shadow-lg hover:scale-105'
            }`}
            style={{
              backgroundColor: running ? fw.color + '60' : fw.color,
              borderColor: fw.color,
              boxShadow: running ? undefined : `0 0 20px ${fw.color}30`,
            }}
          >
            {running ? (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Running...
              </span>
            ) : (
              <span className="flex items-center gap-1">▶ Run on {fw.name}</span>
            )}
          </button>
        </div>

        {/* Framework status */}
        <div className="flex gap-2 flex-wrap">
          {Object.entries(frameworkStatus).map(([name, info]) => (
            <div
              key={name}
              className={`px-2 py-0.5 rounded-full text-[9px] font-medium border ${
                info.installed
                  ? 'text-[var(--accent-success)] border-[var(--accent-success)]/20 bg-[var(--accent-success)]/10'
                  : 'text-[var(--text-muted)] border-[var(--border)] bg-[var(--bg-input)]'
              }`}
            >
              {info.installed ? '●' : '○'} {name}
            </div>
          ))}
        </div>
      </div>

      {/* Results preview */}
      {lastResult && (
        <div className="flex-1 overflow-auto p-3 space-y-2">
          {lastResult.error ? (
            <div className="p-2 rounded-lg bg-[var(--accent-error)]/10 border border-[var(--accent-error)]/20 text-[var(--accent-error)] text-[11px]">
              {lastResult.error}
            </div>
          ) : counts ? (
            <>
              <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
                {fw.name} Results · {total} shots
              </div>
              {Object.entries(counts as Record<string, number>)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 12)
                .map(([state, count]) => (
                  <div key={state} className="flex items-center gap-2">
                    <span className="text-[10px] font-mono w-12 text-right" style={{ color: fw.color }}>
                      {state}
                    </span>
                    <div className="flex-1 h-4 bg-[var(--bg-input)] rounded overflow-hidden">
                      <div
                        className="h-full rounded transition-all duration-500"
                        style={{
                          width: `${(count / Math.max(...Object.values(counts as Record<string, number>))) * 100}%`,
                          backgroundColor: fw.color,
                        }}
                      />
                    </div>
                    <span className="text-[9px] text-[var(--text-muted)] w-10 text-right font-mono">
                      {((count / total) * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
            </>
          ) : (
            <div className="text-[11px] text-[var(--text-muted)] text-center py-4">
              {JSON.stringify(lastResult).slice(0, 200)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
