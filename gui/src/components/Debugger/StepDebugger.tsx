import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useCircuitStore } from '../../stores/circuitStore';
import { api, GateData } from '../../api/commands';

export interface AmplitudeEntry {
  basis: string;
  real: number;
  imag: number;
  magnitude: number;
  phase: number;
  probability: number;
}

export interface BlochVectorEntry {
  qubit: number;
  x: number;
  y: number;
  z: number;
  purity: number;
  entanglement: number;
}

export interface StepDebugState {
  step: number;
  total_steps: number;
  current_gate?: GateData;
  next_gate?: GateData;
  hit_breakpoint: boolean;
  amplitudes: AmplitudeEntry[];
  bloch_vectors: BlochVectorEntry[];
  probabilities: Record<string, number>;
  success: boolean;
}

export default function StepDebugger() {
  const { getCircuitData, numQubits } = useCircuitStore();
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [breakpoints, setBreakpoints] = useState<number[]>([]);
  const [debugData, setDebugData] = useState<StepDebugState | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const playTimerRef = useRef<number | null>(null);

  const circuit = getCircuitData();
  const totalGates = circuit.gates?.length || 0;

  const fetchStep = useCallback(
    async (stepIndex: number) => {
      setLoading(true);
      try {
        const c = getCircuitData();
        const res = await api.stepCircuit(c, stepIndex, breakpoints);
        setDebugData(res);
        setCurrentStep(res.step);
      } catch (err) {
        console.error('Failed to step circuit:', err);
      } finally {
        setLoading(false);
      }
    },
    [getCircuitData, breakpoints]
  );

  useEffect(() => {
    fetchStep(0);
  }, [totalGates]);

  const toggleBreakpoint = (gateIndex: number) => {
    setBreakpoints((prev) =>
      prev.includes(gateIndex) ? prev.filter((i) => i !== gateIndex) : [...prev, gateIndex]
    );
  };

  const stepForward = useCallback(() => {
    if (currentStep < totalGates) {
      fetchStep(currentStep + 1);
    }
  }, [currentStep, totalGates, fetchStep]);

  const stepBackward = useCallback(() => {
    if (currentStep > 0) {
      fetchStep(currentStep - 1);
    }
  }, [currentStep, fetchStep]);

  const reset = useCallback(() => {
    setIsPlaying(false);
    fetchStep(0);
  }, [fetchStep]);

  const jumpToEnd = useCallback(() => {
    setIsPlaying(false);
    fetchStep(totalGates);
  }, [totalGates, fetchStep]);

  // Auto-play stepping logic
  useEffect(() => {
    if (isPlaying) {
      playTimerRef.current = window.setTimeout(() => {
        if (currentStep < totalGates) {
          const nextStep = currentStep + 1;
          if (breakpoints.includes(nextStep)) {
            setIsPlaying(false);
          }
          fetchStep(nextStep);
        } else {
          setIsPlaying(false);
        }
      }, 600);
    } else {
      if (playTimerRef.current) clearTimeout(playTimerRef.current);
    }
    return () => {
      if (playTimerRef.current) clearTimeout(playTimerRef.current);
    };
  }, [isPlaying, currentStep, totalGates, breakpoints, fetchStep]);

  return (
    <div className="flex flex-col h-full bg-[var(--bg-panel)] overflow-hidden text-xs">
      {/* Top Controls & Status Bar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--border)] bg-[var(--bg-card)]">
        <div className="flex items-center gap-1.5">
          <button
            onClick={reset}
            title="Reset to step 0"
            className="p-1 rounded bg-[var(--bg-input)] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] font-mono text-[10px]"
          >
            |◀
          </button>
          <button
            onClick={stepBackward}
            disabled={currentStep <= 0}
            title="Step backward"
            className="px-2 py-1 rounded bg-[var(--bg-input)] hover:bg-[var(--bg-hover)] disabled:opacity-30 text-[var(--text-primary)] font-mono"
          >
            ◀
          </button>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            title={isPlaying ? 'Pause' : 'Auto Play'}
            className={`px-2.5 py-1 rounded font-semibold text-[11px] transition-all ${
              isPlaying
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'bg-violet-600 hover:bg-violet-500 text-white'
            }`}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          <button
            onClick={stepForward}
            disabled={currentStep >= totalGates}
            title="Step forward"
            className="px-2 py-1 rounded bg-[var(--bg-input)] hover:bg-[var(--bg-hover)] disabled:opacity-30 text-[var(--text-primary)] font-mono"
          >
            ▶
          </button>
          <button
            onClick={jumpToEnd}
            title="Jump to end"
            className="p-1 rounded bg-[var(--bg-input)] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] font-mono text-[10px]"
          >
            ▶|
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-[11px] font-mono text-[var(--text-muted)]">
            Step <span className="font-bold text-[var(--accent-primary)]">{currentStep}</span> / {totalGates}
          </div>
          {debugData?.current_gate ? (
            <span className="px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20 font-mono font-medium">
              Applied: {debugData.current_gate.name} (q{debugData.current_gate.qubits.join(', q')})
            </span>
          ) : (
            <span className="text-[10px] text-[var(--text-muted)] italic">Initial State |0...0⟩</span>
          )}
        </div>
      </div>

      {/* Breakpoints Timeline Strip */}
      <div className="px-3 py-1.5 border-b border-[var(--border)] bg-[var(--bg-editor)] flex items-center gap-1 overflow-x-auto">
        <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mr-1">Gates:</span>
        <button
          onClick={() => fetchStep(0)}
          className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
            currentStep === 0 ? 'bg-violet-600 text-white font-bold' : 'bg-[var(--bg-input)] text-[var(--text-muted)]'
          }`}
        >
          Init
        </button>
        {circuit.gates?.map((g, idx) => {
          const stepNum = idx + 1;
          const isCurrent = currentStep === stepNum;
          const hasBp = breakpoints.includes(stepNum);
          return (
            <div key={idx} className="relative flex items-center">
              <button
                onClick={() => fetchStep(stepNum)}
                className={`px-2 py-0.5 rounded text-[10px] font-mono border transition-all ${
                  isCurrent
                    ? 'bg-violet-600 text-white border-violet-400 font-bold shadow'
                    : 'bg-[var(--bg-input)] text-[var(--text-secondary)] border-[var(--border)] hover:border-[var(--border-strong)]'
                }`}
              >
                {g.name}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleBreakpoint(stepNum);
                }}
                title={hasBp ? 'Remove breakpoint' : 'Set breakpoint'}
                className={`absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border border-black ${
                  hasBp ? 'bg-red-500' : 'bg-transparent hover:bg-red-500/40'
                }`}
              />
            </div>
          );
        })}
      </div>

      {/* Split Views: Amplitudes & Bloch Spheres */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2 p-3 overflow-hidden">
        {/* Left: Statevector Amplitude Table with Phase-Coloured Bars */}
        <div className="flex flex-col border border-[var(--border)] rounded-xl bg-[var(--bg-card)] overflow-hidden">
          <div className="px-3 py-2 border-b border-[var(--border)] bg-[var(--bg-panel)] flex items-center justify-between">
            <span className="font-semibold text-xs text-[var(--text-primary)]">Statevector Amplitudes & Phase</span>
            <span className="text-[10px] text-[var(--text-muted)] font-mono">
              Dim: {debugData?.amplitudes?.length || 2 ** numQubits}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-[var(--border)]/50 p-2 space-y-1">
            {debugData?.amplitudes?.map((entry) => {
              // Hue mapped to phase angle in [-pi, pi]
              const phaseDeg = (entry.phase * 180) / Math.PI;
              const hue = Math.round(((entry.phase + Math.PI) / (2 * Math.PI)) * 360);
              const barColor = `hsl(${hue}, 85%, 55%)`;

              return (
                <div key={entry.basis} className="p-1.5 rounded hover:bg-[var(--bg-hover)] space-y-1">
                  <div className="flex items-center justify-between font-mono">
                    <span className="text-[11px] font-bold text-violet-400">|{entry.basis}⟩</span>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {(entry.probability * 100).toFixed(2)}%
                    </span>
                  </div>

                  {/* Phase-Coloured Amplitude Bar */}
                  <div className="w-full h-3 bg-[var(--bg-input)] rounded overflow-hidden relative">
                    <div
                      className="h-full transition-all duration-300 rounded"
                      style={{
                        width: `${Math.max(entry.magnitude > 1e-6 ? 4 : 0, entry.magnitude * 100)}%`,
                        backgroundColor: barColor,
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[9px] text-[var(--text-muted)] font-mono">
                    <span>
                      α = {entry.real >= 0 ? '+' : ''}
                      {entry.real.toFixed(4)} {entry.imag >= 0 ? '+' : ''}
                      {entry.imag.toFixed(4)}i
                    </span>
                    <span>
                      θ = {phaseDeg.toFixed(1)}° ({entry.phase.toFixed(2)} rad)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Per-Qubit Reduced Bloch Spheres & Entanglement Gauges */}
        <div className="flex flex-col border border-[var(--border)] rounded-xl bg-[var(--bg-card)] overflow-hidden">
          <div className="px-3 py-2 border-b border-[var(--border)] bg-[var(--bg-panel)] flex items-center justify-between">
            <span className="font-semibold text-xs text-[var(--text-primary)]">Per-Qubit Reduced States & Bloch Vectors</span>
            <span className="text-[10px] text-[var(--text-muted)]">Traced Subsystems</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {debugData?.bloch_vectors?.map((bv) => (
              <div key={bv.qubit} className="p-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-panel)] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-[var(--text-primary)]">Qubit q[{bv.qubit}]</span>
                  <div className="flex items-center gap-2 font-mono text-[10px]">
                    <span className={`px-1.5 py-0.5 rounded ${
                      bv.purity > 0.99 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      Purity: {(bv.purity * 100).toFixed(1)}%
                    </span>
                    <span className={`px-1.5 py-0.5 rounded ${
                      bv.entanglement > 0.5 ? 'bg-purple-500/20 text-purple-400 font-semibold' : 'bg-[var(--bg-input)] text-[var(--text-muted)]'
                    }`}>
                      Entanglement: {(bv.entanglement * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* 3D Bloch vector representation */}
                <div className="grid grid-cols-3 gap-1 text-center font-mono text-[10px] bg-[var(--bg-input)] p-1.5 rounded">
                  <div>
                    <span className="text-[var(--text-muted)] block text-[8px]">r_x</span>
                    <span className="text-emerald-400 font-semibold">{bv.x.toFixed(3)}</span>
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)] block text-[8px]">r_y</span>
                    <span className="text-sky-400 font-semibold">{bv.y.toFixed(3)}</span>
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)] block text-[8px]">r_z</span>
                    <span className="text-violet-400 font-semibold">{bv.z.toFixed(3)}</span>
                  </div>
                </div>

                {/* Visual Purity / Entanglement Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[9px] text-[var(--text-muted)]">
                    <span>Mixed (0.5)</span>
                    <span>Pure (1.0)</span>
                  </div>
                  <div className="w-full h-1.5 bg-[var(--bg-input)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-emerald-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.max(0, (bv.purity - 0.5) * 200)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
