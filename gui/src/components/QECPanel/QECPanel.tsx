import React, { useState, useCallback, useMemo } from 'react';
import { api } from '../../api/commands';

interface CodeInfo {
  id: string;
  name: string;
  n: number;
  k: number;
  d: number;
  stabilizers: string[];
  qubitLayout: 'line' | 'grid' | 'custom';
  gridSize?: { rows: number; cols: number };
  backendType: string;
}

const CODES: CodeInfo[] = [
  {
    id: 'repetition-3',
    name: 'Repetition [[3,1,1]]',
    n: 3,
    k: 1,
    d: 1,
    stabilizers: ['ZZI', 'IZZ'],
    qubitLayout: 'line',
    backendType: 'repetition',
  },
  {
    id: 'bit-flip',
    name: 'Bit-flip [[3,1,1]]',
    n: 3,
    k: 1,
    d: 1,
    stabilizers: ['ZZI', 'IZZ'],
    qubitLayout: 'line',
    backendType: 'bit_flip',
  },
  {
    id: 'phase-flip',
    name: 'Phase-flip [[3,1,1]]',
    n: 3,
    k: 1,
    d: 1,
    stabilizers: ['XXI', 'IXX'],
    qubitLayout: 'line',
    backendType: 'phase_flip',
  },
  {
    id: 'shor-9',
    name: 'Shor [[9,1,3]]',
    n: 9,
    k: 1,
    d: 3,
    stabilizers: [
      'ZZIIIIIII',
      'IZZIIIIII',
      'IIZZIIIII',
      'IIIZZIIII',
      'IIIIZZIII',
      'IIIIIZZII',
      'IIIIIIZZI',
      'IIIIIIIZZ',
      'XXXXXXIII',
      'IIXXXXXXIII',
      'IIIXXXXXXIII',
    ],
    qubitLayout: 'grid',
    gridSize: { rows: 3, cols: 3 },
    backendType: 'shor',
  },
  {
    id: 'steane-7',
    name: 'Steane [[7,1,3]]',
    n: 7,
    k: 1,
    d: 3,
    stabilizers: [
      'IIIXXXX',
      'IXXIIXX',
      'XIXIXIX',
      'IIIZZZZ',
      'IZZIIZZ',
      'ZIZIZIZ',
    ],
    qubitLayout: 'custom',
    backendType: 'steane',
  },
  {
    id: 'surface-3',
    name: 'Surface d=3 [[9,1,3]]',
    n: 9,
    k: 1,
    d: 3,
    stabilizers: [
      'ZZ.I.I...',
      'I.ZZ.I..I',
      'I.I.ZZ..I',
      'XXXX.....',
      '.XXXX....',
      '..XXXX...',
    ],
    qubitLayout: 'grid',
    gridSize: { rows: 3, cols: 3 },
    backendType: 'surface',
  },
  {
    id: 'surface-5',
    name: 'Surface d=5 [[25,1,5]]',
    n: 25,
    k: 1,
    d: 5,
    stabilizers: Array(24).fill('....'),
    qubitLayout: 'grid',
    gridSize: { rows: 5, cols: 5 },
    backendType: 'surface',
  },
  {
    id: 'surface-7',
    name: 'Surface d=7 [[49,1,7]]',
    n: 49,
    k: 1,
    d: 7,
    stabilizers: Array(48).fill('....'),
    qubitLayout: 'grid',
    gridSize: { rows: 7, cols: 7 },
    backendType: 'surface',
  },
  {
    id: 'color',
    name: 'Color [[7,1,3]]',
    n: 7,
    k: 1,
    d: 3,
    stabilizers: ['ZZZ.III', 'IIIZZZ.', '.III.ZZZ'],
    qubitLayout: 'custom',
    backendType: 'color',
  },
  {
    id: 'ldpc',
    name: 'LDPC [[12,2,4]]',
    n: 12,
    k: 2,
    d: 4,
    stabilizers: [
      'ZZZZ......II',
      'II..ZZZZ.II',
      'XXXX......XX',
      '..XX..XXXX.XX',
    ],
    qubitLayout: 'grid',
    gridSize: { rows: 3, cols: 4 },
    backendType: 'surface',
  },
];

type DecoderType = 'syndrome-lookup' | 'mwpm' | 'bp';
const DECODERS: { id: DecoderType; name: string; description: string }[] = [
  { id: 'syndrome-lookup', name: 'Syndrome Lookup', description: 'Direct table lookup' },
  { id: 'mwpm', name: 'MWPM (Greedy)', description: 'Minimum Weight Perfect Matching' },
  { id: 'bp', name: 'Belief Propagation', description: 'Iterative message passing' },
];

interface QubitState {
  id: number;
  error: 'none' | 'X' | 'Z' | 'Y';
  row: number;
  col: number;
}

interface SyndromeResult {
  triggeredStabilizers: number[];
  syndrome: string;
}

interface DistillationResult {
  inputStates: number;
  outputStates: number;
  success: boolean;
  fidelity: number;
  round: number;
}

interface Stats {
  totalRuns: number;
  successfulCorrections: number;
  logicalErrorRate: number;
  successRate: number;
}

function generateRandomError(n: number): QubitState[] {
  const errorProb = 0.3;
  const qubits: QubitState[] = [];
  for (let i = 0; i < n; i++) {
    const r = Math.random();
    let error: 'none' | 'X' | 'Z' | 'Y' = 'none';
    if (r < errorProb / 3) error = 'X';
    else if (r < (2 * errorProb) / 3) error = 'Z';
    else if (r < errorProb) error = 'Y';
    qubits.push({ id: i, error, row: 0, col: 0 });
  }
  return qubits;
}

function computeSyndrome(qubits: QubitState[], stabilizers: string[]): SyndromeResult {
  const triggered: number[] = [];
  let syndrome = '';
  for (let i = 0; i < Math.min(stabilizers.length, 8); i++) {
    const stab = stabilizers[i];
    let anticommutes = false;
    for (let j = 0; j < qubits.length && j < stab.length; j++) {
      const s = stab[j];
      const e = qubits[j].error;
      if (s === 'X' && (e === 'Z' || e === 'Y')) anticommutes = true;
      if (s === 'Z' && (e === 'X' || e === 'Y')) anticommutes = true;
      if (s === 'Y' && (e === 'X' || e === 'Z')) anticommutes = true;
    }
    if (anticommutes) {
      triggered.push(i);
      syndrome += '1';
    } else {
      syndrome += '0';
    }
  }
  return { triggeredStabilizers: triggered, syndrome };
}

function applyDecoder(
  decoder: DecoderType,
  qubits: QubitState[],
  syndrome: SyndromeResult,
  code: CodeInfo
): QubitState[] {
  const corrected = qubits.map((q) => ({ ...q }));
  if (decoder === 'syndrome-lookup') {
    for (const idx of syndrome.triggeredStabilizers) {
      const stab = code.stabilizers[idx];
      if (stab) {
        for (let j = 0; j < corrected.length && j < stab.length; j++) {
          if (stab[j] === 'X' && corrected[j].error !== 'none') {
            corrected[j].error = 'none';
            break;
          }
        }
      }
    }
  } else if (decoder === 'mwpm') {
    for (let i = 0; i < corrected.length; i++) {
      if (corrected[i].error !== 'none' && syndrome.triggeredStabilizers.length > 0) {
        const hasAdjacent = syndrome.triggeredStabilizers.some((s) => {
          const stab = code.stabilizers[s];
          return stab && (stab[i] === 'X' || stab[i] === 'Z' || stab[i] === 'Y');
        });
        if (hasAdjacent) {
          corrected[i].error = 'none';
        }
      }
    }
  } else if (decoder === 'bp') {
    for (let iter = 0; iter < 3; iter++) {
      for (let i = 0; i < corrected.length; i++) {
        if (corrected[i].error !== 'none') {
          const voteCount = syndrome.triggeredStabilizers.filter((s) => {
            const stab = code.stabilizers[s];
            return stab && stab[i] !== '.' && stab[i] !== 'I';
          }).length;
          if (voteCount >= 2) {
            corrected[i].error = 'none';
          }
        }
      }
    }
  }
  return corrected;
}

function runDistillation(inputStates: number, round: number): DistillationResult {
  const baseSuccessRate = inputStates === 15 ? 0.72 : 0.65;
  const success = Math.random() < baseSuccessRate + round * 0.02;
  return {
    inputStates,
    outputStates: success ? 1 : 0,
    success,
    fidelity: success ? 0.99 + Math.random() * 0.009 : 0.0,
    round,
  };
}

function getQubitLayout(code: CodeInfo): { row: number; col: number }[] {
  const positions: { row: number; col: number }[] = [];
  if (code.gridSize) {
    for (let r = 0; r < code.gridSize.rows; r++) {
      for (let c = 0; c < code.gridSize.cols; c++) {
        positions.push({ row: r, col: c });
      }
    }
  } else {
    for (let i = 0; i < code.n; i++) {
      const angle = (2 * Math.PI * i) / code.n;
      const radius = 1.5;
      positions.push({
        row: Math.round(radius + radius * Math.sin(angle)),
        col: Math.round(radius + radius * Math.cos(angle)),
      });
    }
  }
  return positions;
}

export default function QECPanel() {
  const [selectedCode, setSelectedCode] = useState<string>(CODES[0].id);
  const [selectedDecoder, setSelectedDecoder] = useState<DecoderType>('syndrome-lookup');
  const [qubits, setQubits] = useState<QubitState[]>([]);
  const [syndrome, setSyndrome] = useState<SyndromeResult | null>(null);
  const [correctedQubits, setCorrectedQubits] = useState<QubitState[]>([]);
  const [hasEncoded, setHasEncoded] = useState(false);
  const [hasDecoded, setHasDecoded] = useState(false);
  const [distillationRound, setDistillationRound] = useState(1);
  const [distillationResults, setDistillationResults] = useState<DistillationResult[]>([]);
  const [stats, setStats] = useState<Stats>({
    totalRuns: 0,
    successfulCorrections: 0,
    logicalErrorRate: 0,
    successRate: 0,
  });
  const [backendResult, setBackendResult] = useState<any>(null);
  const [backendRunning, setBackendRunning] = useState(false);

  const code = useMemo(() => CODES.find((c) => c.id === selectedCode)!, [selectedCode]);
  const positions = useMemo(() => getQubitLayout(code), [code]);

  const handleEncode = useCallback(() => {
    const newQubits = generateRandomError(code.n);
    for (let i = 0; i < newQubits.length; i++) {
      newQubits[i].row = positions[i].row;
      newQubits[i].col = positions[i].col;
    }
    const syn = computeSyndrome(newQubits, code.stabilizers);
    setQubits(newQubits);
    setSyndrome(syn);
    setHasEncoded(true);
    setHasDecoded(false);
    setCorrectedQubits([]);
    setDistillationResults([]);
  }, [code, positions]);

  const handleDecode = useCallback(() => {
    if (!hasEncoded || !syndrome) return;
    const corrected = applyDecoder(selectedDecoder, qubits, syndrome, code);
    setCorrectedQubits(corrected);
    setHasDecoded(true);

    const remainingErrors = corrected.filter((q) => q.error !== 'none').length;
    const success = remainingErrors === 0;

    setStats((prev) => {
      const newTotal = prev.totalRuns + 1;
      const newSuccesses = prev.successfulCorrections + (success ? 1 : 0);
      return {
        totalRuns: newTotal,
        successfulCorrections: newSuccesses,
        logicalErrorRate: 1 - newSuccesses / newTotal,
        successRate: newSuccesses / newTotal,
      };
    });
  }, [hasEncoded, syndrome, qubits, selectedDecoder, code]);

  const handleDistill = useCallback(() => {
    const tResult = runDistillation(15, distillationRound);
    const hResult = runDistillation(20, distillationRound);
    setDistillationResults([tResult, hResult]);
  }, [distillationRound]);

  const resetQubitColor = (q: QubitState, display: 'original' | 'corrected') => {
    if (display === 'corrected') {
      return q.error === 'none' ? 'var(--accent-success)' : 'var(--accent-error)';
    }
    return q.error === 'none' ? 'var(--accent-success)' : 'var(--accent-error)';
  };

  const getErrorLabel = (e: 'none' | 'X' | 'Z' | 'Y') => {
    if (e === 'none') return '✓';
    return e;
  };

  return (
    <div className="h-full flex flex-col text-[var(--text-primary)] overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-white/5 bg-[var(--bg-panel)]">
        <span className="text-[11px] font-semibold text-[var(--accent-primary)]">QEC Lab</span>
        <span className="text-[9px] text-[var(--text-muted)]">Quantum Error Correction Simulator</span>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        {/* Code Picker */}
        <div className="space-y-1.5">
          <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Error Correction Code</label>
          <select
            value={selectedCode}
            onChange={(e) => {
              setSelectedCode(e.target.value);
              setQubits([]);
              setSyndrome(null);
              setCorrectedQubits([]);
              setHasEncoded(false);
              setHasDecoded(false);
              setDistillationResults([]);
            }}
            className="w-full px-2 py-1.5 rounded-md bg-[var(--bg-input)] border border-white/5 text-[11px] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
          >
            {CODES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Code Properties */}
        <div className="flex gap-2 animate-fade-in">
          <div className="flex-1 rounded-md bg-[var(--bg-input)] border border-white/5 px-2 py-1.5 text-center">
            <div className="text-[9px] text-[var(--text-muted)]">n (physical)</div>
            <div className="text-[11px] font-mono font-bold text-[var(--accent-primary)]">{code.n}</div>
          </div>
          <div className="flex-1 rounded-md bg-[var(--bg-input)] border border-white/5 px-2 py-1.5 text-center">
            <div className="text-[9px] text-[var(--text-muted)]">k (logical)</div>
            <div className="text-[11px] font-mono font-bold text-[var(--accent-primary)]">{code.k}</div>
          </div>
          <div className="flex-1 rounded-md bg-[var(--bg-input)] border border-white/5 px-2 py-1.5 text-center">
            <div className="text-[9px] text-[var(--text-muted)]">d (distance)</div>
            <div className="text-[11px] font-mono font-bold text-[var(--accent-primary)]">{code.d}</div>
          </div>
        </div>

        {/* Encode Button */}
        <button
          onClick={handleEncode}
          className="w-full py-1.5 rounded-md bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 text-[11px] font-medium text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/20 transition-colors"
        >
          Encode (Generate Random Error)
        </button>

        {/* Qubit Grid */}
        {hasEncoded && (
          <div className="space-y-1.5 animate-fade-in">
            <div className="flex items-center gap-2">
              <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Qubit State</label>
              <div className="flex-1" />
              <div className="flex items-center gap-1 text-[9px]">
                <span className="w-2 h-2 rounded-full bg-[var(--accent-success)]" />
                <span className="text-[var(--text-muted)]">OK</span>
                <span className="w-2 h-2 rounded-full bg-[var(--accent-error)] ml-1" />
                <span className="text-[var(--text-muted)]">Error</span>
              </div>
            </div>
            <div className="rounded-md bg-[var(--bg-input)] border border-white/5 p-2">
              {code.gridSize ? (
                <div
                  className="grid gap-1 mx-auto"
                  style={{
                    gridTemplateColumns: `repeat(${code.gridSize.cols}, minmax(0, 1fr))`,
                    maxWidth: `${code.gridSize.cols * 36}px`,
                  }}
                >
                  {(hasDecoded ? correctedQubits : qubits).map((q) => (
                    <div
                      key={q.id}
                      className="relative aspect-square rounded-md border border-white/10 flex flex-col items-center justify-center transition-all duration-300"
                      style={{ backgroundColor: `${resetQubitColor(q, hasDecoded ? 'corrected' : 'original')}15` }}
                    >
                      <span
                        className="text-[10px] font-mono font-bold"
                        style={{ color: resetQubitColor(q, hasDecoded ? 'corrected' : 'original') }}
                      >
                        {getErrorLabel(q.error)}
                      </span>
                      <span className="text-[8px] text-[var(--text-muted)]">q{q.id}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-wrap gap-1 justify-center">
                  {(hasDecoded ? correctedQubits : qubits).map((q) => (
                    <div
                      key={q.id}
                      className="w-8 h-8 rounded-md border border-white/10 flex flex-col items-center justify-center transition-all duration-300"
                      style={{ backgroundColor: `${resetQubitColor(q, hasDecoded ? 'corrected' : 'original')}15` }}
                    >
                      <span
                        className="text-[10px] font-mono font-bold"
                        style={{ color: resetQubitColor(q, hasDecoded ? 'corrected' : 'original') }}
                      >
                        {getErrorLabel(q.error)}
                      </span>
                      <span className="text-[8px] text-[var(--text-muted)]">q{q.id}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Syndrome Display */}
        {syndrome && (
          <div className="space-y-1.5 animate-fade-in">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Syndrome</label>
            <div className="rounded-md bg-[var(--bg-input)] border border-white/5 p-2">
              <div className="flex flex-wrap gap-1 mb-1.5">
                {syndrome.syndrome.split('').map((bit, i) => (
                  <span
                    key={i}
                    className={`inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-mono font-bold border ${
                      bit === '1'
                        ? 'bg-[var(--accent-error)]/15 border-[var(--accent-error)]/40 text-[var(--accent-error)]'
                        : 'bg-white/[0.02] border-white/5 text-[var(--text-muted)]'
                    }`}
                  >
                    {bit}
                  </span>
                ))}
              </div>
              <div className="text-[9px] text-[var(--text-muted)]">
                {syndrome.triggeredStabilizers.length > 0 ? (
                  <span>
                    Triggered:{' '}
                    {syndrome.triggeredStabilizers.map((idx) => (
                      <span key={idx} className="text-[var(--accent-error)]">
                        S{idx + 1}{' '}
                      </span>
                    ))}
                  </span>
                ) : (
                  <span className="text-[var(--accent-success)]">No errors detected</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Decoder Selector */}
        {hasEncoded && (
          <div className="space-y-1.5 animate-fade-in">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Decoder</label>
            <div className="flex gap-1">
              {DECODERS.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelectedDecoder(d.id)}
                  className={`flex-1 px-2 py-1.5 rounded-md text-[10px] font-medium border transition-all ${
                    selectedDecoder === d.id
                      ? 'bg-[var(--accent-primary)]/10 border-[var(--accent-primary)]/40 text-[var(--accent-primary)]'
                      : 'bg-[var(--bg-input)] border-white/5 text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-white/10'
                  }`}
                >
                  {d.name}
                </button>
              ))}
            </div>
            <div className="text-[9px] text-[var(--text-muted)] px-1">
              {DECODERS.find((d) => d.id === selectedDecoder)?.description}
            </div>
          </div>
        )}

        {/* Decode Button */}
        {hasEncoded && (
          <button
            onClick={handleDecode}
            className="w-full py-1.5 rounded-md bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 text-[11px] font-medium text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/20 transition-colors"
          >
            Decode ({DECODERS.find((d) => d.id === selectedDecoder)?.name})
          </button>
        )}

        {/* Correction Result */}
        {hasDecoded && (
          <div className="space-y-1.5 animate-fade-in">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Correction Result</label>
            <div className="rounded-md bg-[var(--bg-input)] border border-white/5 p-2">
              <div className="flex items-center gap-2 mb-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    correctedQubits.every((q) => q.error === 'none')
                      ? 'bg-[var(--accent-success)]'
                      : 'bg-[var(--accent-error)]'
                  }`}
                />
                <span className="text-[11px] font-medium text-[var(--text-primary)]">
                  {correctedQubits.every((q) => q.error === 'none')
                    ? 'All errors corrected'
                    : `${correctedQubits.filter((q) => q.error !== 'none').length} residual error(s)`}
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {correctedQubits
                  .filter((q) => q.error !== 'none')
                  .map((q) => (
                    <span
                      key={q.id}
                      className="px-1.5 py-0.5 rounded bg-[var(--accent-error)]/10 border border-[var(--accent-error)]/30 text-[9px] font-mono text-[var(--accent-error)]"
                    >
                      q{q.id}:{q.error}
                    </span>
                  ))}
              </div>
              {correctedQubits.every((q) => q.error === 'none') && (
                <div className="text-[9px] text-[var(--accent-success)] mt-1">✓ Decoding successful</div>
              )}
            </div>
          </div>
        )}

        {/* Magic State Distillation */}
        <div className="space-y-1.5">
          <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Magic State Distillation</label>
          <div className="rounded-md bg-[var(--bg-input)] border border-white/5 p-2 space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[var(--text-secondary)]">Round:</span>
              {[1, 2, 3, 4, 5].map((r) => (
                <button
                  key={r}
                  onClick={() => setDistillationRound(r)}
                  className={`w-6 h-6 rounded text-[10px] font-mono font-bold border transition-all ${
                    distillationRound === r
                      ? 'bg-[var(--accent-primary)]/15 border-[var(--accent-primary)]/40 text-[var(--accent-primary)]'
                      : 'border-white/5 text-[var(--text-muted)] hover:border-white/10'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="rounded border border-white/5 p-2">
                <div className="text-[10px] text-[var(--text-muted)] mb-1">T-State (15-to-1)</div>
                <div className="text-[11px] font-mono text-[var(--text-primary)]">
                  {distillationResults[0] ? (
                    distillationResults[0].success ? (
                      <span className="text-[var(--accent-success)]">
                        Fid: {(distillationResults[0].fidelity * 100).toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-[var(--accent-error)]">Failed</span>
                    )
                  ) : (
                    <span className="text-[var(--text-muted)]">—</span>
                  )}
                </div>
              </div>
              <div className="rounded border border-white/5 p-2">
                <div className="text-[10px] text-[var(--text-muted)] mb-1">H-State (20-to-4)</div>
                <div className="text-[11px] font-mono text-[var(--text-primary)]">
                  {distillationResults[1] ? (
                    distillationResults[1].success ? (
                      <span className="text-[var(--accent-success)]">
                        Fid: {(distillationResults[1].fidelity * 100).toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-[var(--accent-error)]">Failed</span>
                    )
                  ) : (
                    <span className="text-[var(--text-muted)]">—</span>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={handleDistill}
              className="w-full py-1 rounded-md bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 text-[10px] font-medium text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/20 transition-colors"
            >
              Run Distillation
            </button>
          </div>
        </div>

        {/* Run on Real Backend */}
        <div className="space-y-1.5">
          <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Real Backend Execution</label>
          <div className="rounded-md bg-[var(--bg-input)] border border-white/5 p-2 space-y-2">
            <div className="text-[9px] text-[var(--text-muted)]">
              Runs {code.name} on the AbirQu QEC engine
            </div>
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="text-[9px] text-[var(--text-muted)]">Error Rate</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  defaultValue={0.1}
                  id="qec-error-rate"
                  className="w-full px-2 py-1 rounded bg-[var(--bg-primary)] border border-white/5 text-[10px] text-[var(--text-primary)] font-mono"
                />
              </div>
              <div className="flex-1">
                <label className="text-[9px] text-[var(--text-muted)]">Trials</label>
                <input
                  type="number"
                  step="100"
                  min="100"
                  max="10000"
                  defaultValue={1000}
                  id="qec-trials"
                  className="w-full px-2 py-1 rounded bg-[var(--bg-primary)] border border-white/5 text-[10px] text-[var(--text-primary)] font-mono"
                />
              </div>
            </div>
            <button
              onClick={async () => {
                setBackendRunning(true);
                setBackendResult(null);
                try {
                  const errorRate = parseFloat((document.getElementById('qec-error-rate') as HTMLInputElement)?.value || '0.1');
                  const numTrials = parseInt((document.getElementById('qec-trials') as HTMLInputElement)?.value || '1000');
                  const result = await api.runQec({
                    code_type: code.backendType,
                    distance: code.d,
                    error_rate: errorRate,
                    logical_state: 0,
                    num_trials: numTrials,
                  });
                  setBackendResult(result);
                } catch (e) {
                  setBackendResult({ error: String(e) });
                } finally {
                  setBackendRunning(false);
                }
              }}
              disabled={backendRunning}
              className={`w-full py-1.5 rounded-md text-[11px] font-medium border transition-colors ${
                backendRunning
                  ? 'bg-[var(--accent-primary)]/5 border-[var(--accent-primary)]/20 text-[var(--text-muted)] cursor-wait'
                  : 'bg-[var(--accent-success)]/10 border-[var(--accent-success)]/30 text-[var(--accent-success)] hover:bg-[var(--accent-success)]/20'
              }`}
            >
              {backendRunning ? 'Running on QEC Engine...' : 'Run on Real Backend'}
            </button>
            {backendResult && !backendResult.error && (
              <div className="space-y-1.5 mt-1">
                <div className="grid grid-cols-2 gap-1.5">
                  <div className="rounded border border-white/5 p-1.5 text-center">
                    <div className="text-[8px] text-[var(--text-muted)]">Correction Rate</div>
                    <div className="text-[11px] font-mono font-bold text-[var(--accent-success)]">
                      {(backendResult.correction_success * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded border border-white/5 p-1.5 text-center">
                    <div className="text-[8px] text-[var(--text-muted)]">Logical Error Rate</div>
                    <div className="text-[11px] font-mono font-bold text-[var(--accent-error)]">
                      {(backendResult.logical_error_rate * 100).toFixed(3)}%
                    </div>
                  </div>
                  <div className="rounded border border-white/5 p-1.5 text-center">
                    <div className="text-[8px] text-[var(--text-muted)]">Code</div>
                    <div className="text-[11px] font-mono font-bold text-[var(--accent-primary)]">
                      [{backendResult.n},{backendResult.k},{backendResult.distance}]
                    </div>
                  </div>
                  <div className="rounded border border-white/5 p-1.5 text-center">
                    <div className="text-[8px] text-[var(--text-muted)]">Trials</div>
                    <div className="text-[11px] font-mono font-bold text-[var(--text-primary)]">
                      {backendResult.num_trials}
                    </div>
                  </div>
                </div>
              </div>
            )}
            {backendResult?.error && (
              <div className="text-[10px] text-[var(--accent-error)] mt-1">{backendResult.error}</div>
            )}
          </div>
        </div>

        {/* Statistics */}
        <div className="space-y-1.5">
          <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Statistics</label>
          <div className="rounded-md bg-[var(--bg-input)] border border-white/5 p-2 space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <div className="text-[9px] text-[var(--text-muted)]">Total Runs</div>
                <div className="text-[11px] font-mono font-bold text-[var(--text-primary)]">{stats.totalRuns}</div>
              </div>
              <div>
                <div className="text-[9px] text-[var(--text-muted)]">Successful</div>
                <div className="text-[11px] font-mono font-bold text-[var(--accent-success)]">
                  {stats.successfulCorrections}
                </div>
              </div>
              <div>
                <div className="text-[9px] text-[var(--text-muted)]">Logical Error Rate</div>
                <div className="text-[11px] font-mono font-bold text-[var(--accent-error)]">
                  {(stats.logicalErrorRate * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-[9px] text-[var(--text-muted)]">Success Rate</div>
                <div className="text-[11px] font-mono font-bold text-[var(--accent-success)]">
                  {(stats.successRate * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Success Rate Bar */}
            {stats.totalRuns > 0 && (
              <div className="mt-1">
                <div className="w-full h-2 rounded-full bg-[var(--bg-primary)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${stats.successRate * 100}%`,
                      background: `linear-gradient(90deg, var(--accent-success), var(--accent-primary))`,
                    }}
                  />
                </div>
                <div className="flex justify-between mt-0.5">
                  <span className="text-[8px] text-[var(--text-muted)]">0%</span>
                  <span className="text-[8px] text-[var(--text-muted)]">100%</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stabilizer Reference */}
        <div className="space-y-1.5">
          <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Stabilizer Generators</label>
          <div className="rounded-md bg-[var(--bg-input)] border border-white/5 p-2 max-h-24 overflow-auto">
            {code.stabilizers.slice(0, 8).map((stab, i) => (
              <div key={i} className="flex items-center gap-2 py-0.5">
                <span className="text-[9px] text-[var(--text-muted)] w-6">S{i + 1}</span>
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">{stab}</span>
                {syndrome && syndrome.triggeredStabilizers.includes(i) && (
                  <span className="text-[8px] text-[var(--accent-error)] font-bold">TRIGGERED</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-3 py-1.5 border-t border-white/5 text-[9px] text-[var(--text-muted)] flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)]" />
        <span>
          {code.name} · {code.n}q · Decoder: {DECODERS.find((d) => d.id === selectedDecoder)?.name}
        </span>
      </div>
    </div>
  );
}
