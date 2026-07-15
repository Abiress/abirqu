import React, { useState, useCallback, useMemo } from 'react';
import { api, QECCycleParams, QECCycleResult, QECDistillResult } from '../../api/commands';

// ─────────────────────────────────────────────────────────────────────────
// Real code/decoder catalog. Only combinations verified to actually work
// against the live abirqu.qec module are offered here — "color" and "ldpc"
// codes, and the "belief_propagation"/"surface"/"gpu_bp" decoders, are
// left out deliberately.
// ─────────────────────────────────────────────────────────────────────────

type QECCode = 'repetition' | 'bit_flip' | 'phase_flip' | 'shor' | 'steane' | 'surface';
type DecoderType = 'lookup' | 'mwpm';

interface CodeInfo {
  id: QECCode;
  name: string;
  sizeOptions?: number[];
  defaultSize?: number;
  referenceOverhead: { n: number; k: number; d: number };
}

const CODES: CodeInfo[] = [
  { id: 'repetition', name: 'Repetition', sizeOptions: [3, 5, 7], defaultSize: 3, referenceOverhead: { n: 3, k: 1, d: 2 } },
  { id: 'bit_flip', name: 'Bit-flip [[3,1,1]]', referenceOverhead: { n: 3, k: 1, d: 1 } },
  { id: 'phase_flip', name: 'Phase-flip [[3,1,1]]', referenceOverhead: { n: 3, k: 1, d: 1 } },
  { id: 'shor', name: 'Shor [[9,1,3]]', referenceOverhead: { n: 9, k: 1, d: 3 } },
  { id: 'steane', name: 'Steane [[7,1,3]]', referenceOverhead: { n: 7, k: 1, d: 3 } },
  { id: 'surface', name: 'Rotated Surface', sizeOptions: [3, 5, 7], defaultSize: 3, referenceOverhead: { n: 13, k: 1, d: 3 } },
];

const DECODERS: { id: DecoderType; name: string; description: string; caveat?: string }[] = [
  { id: 'lookup', name: 'Syndrome Lookup', description: 'Direct stabilizer table lookup (abirqu.qec.SyndromeDecoder)' },
  {
    id: 'mwpm',
    name: 'MWPM',
    description: 'Minimum Weight Perfect Matching (abirqu.qec.MWPMDecoder)',
    caveat: 'Verified: MWPM does not correct Repetition/Bit-flip/Phase-flip codes in this SDK version — use Syndrome Lookup for those.',
  },
];

function randomErrorQubits(n: number, count: number): number[] {
  const all = Array.from({ length: n }, (_, i) => i);
  const picked: number[] = [];
  for (let i = 0; i < count && all.length > 0; i++) {
    const idx = Math.floor(Math.random() * all.length);
    picked.push(all.splice(idx, 1)[0]);
  }
  return picked;
}

export default function QECPanel() {
  const [selectedCode, setSelectedCode] = useState<QECCode>('steane');
  const [selectedSize, setSelectedSize] = useState<number | undefined>(undefined);
  const [selectedDecoder, setSelectedDecoder] = useState<DecoderType>('lookup');

  const [errorQubits, setErrorQubits] = useState<number[]>([]);
  const [cycleResult, setCycleResult] = useState<QECCycleResult | null>(null);
  const [hasDecoded, setHasDecoded] = useState(false);

  const [encoding, setEncoding] = useState(false);
  const [decoding, setDecoding] = useState(false);
  const [encodeError, setEncodeError] = useState<string | null>(null);
  const [decodeError, setDecodeError] = useState<string | null>(null);

  const [distillRound, setDistillRound] = useState(1);
  const [distillResults, setDistillResults] = useState<(QECDistillResult | null)[]>([null, null]);
  const [distilling, setDistilling] = useState(false);
  const [distillError, setDistillError] = useState<string | null>(null);

  const [stats, setStats] = useState({ totalRuns: 0, successfulCorrections: 0 });

  const code = useMemo(() => CODES.find((c) => c.id === selectedCode)!, [selectedCode]);
  const displayOverhead = cycleResult?.overhead ?? code.referenceOverhead;
  const n = cycleResult?.n_physical_qubits ?? (displayOverhead as any).n ?? code.referenceOverhead.n;

  const runCycle = useCallback(
    async (qubits: number[], decoder: DecoderType) => {
      const params: QECCycleParams = {
        code: selectedCode,
        decoder,
        logical_state: 0,
        error_qubits: qubits,
      };
      if (code.sizeOptions && selectedSize) params.size = selectedSize;
      return api.runQECCycle(params);
    },
    [selectedCode, selectedSize, code.sizeOptions]
  );

  const handleEncode = useCallback(async () => {
    setEncoding(true);
    setEncodeError(null);
    setHasDecoded(false);
    setCycleResult(null);
    try {
      const errorCount = Math.max(1, Math.round((n || code.referenceOverhead.n) * 0.15));
      const qubits = randomErrorQubits(n || code.referenceOverhead.n, errorCount);
      setErrorQubits(qubits);
      const result = await runCycle(qubits, selectedDecoder);
      setCycleResult(result);
    } catch (e) {
      setEncodeError(String(e));
    } finally {
      setEncoding(false);
    }
  }, [code, selectedSize, selectedDecoder, n, runCycle]);

  const handleDecode = useCallback(async () => {
    if (errorQubits.length === 0) return;
    setDecoding(true);
    setDecodeError(null);
    try {
      const result = await runCycle(errorQubits, selectedDecoder);
      setCycleResult(result);
      setHasDecoded(true);
      setStats((prev) => ({
        totalRuns: prev.totalRuns + 1,
        successfulCorrections: prev.successfulCorrections + (result.corrected_successfully ? 1 : 0),
      }));
    } catch (e) {
      setDecodeError(String(e));
    } finally {
      setDecoding(false);
    }
  }, [errorQubits, selectedDecoder, runCycle]);

  const handleDistill = useCallback(async () => {
    setDistilling(true);
    setDistillError(null);
    try {
      const [t, h] = await Promise.all([
        api.runQECDistill({ state_type: 't', rounds: distillRound }),
        api.runQECDistill({ state_type: 'h', rounds: distillRound }),
      ]);
      setDistillResults([t, h]);
    } catch (e) {
      setDistillError(String(e));
    } finally {
      setDistilling(false);
    }
  }, [distillRound]);

  const successRate = stats.totalRuns > 0 ? stats.successfulCorrections / stats.totalRuns : 0;

  const qubitErrorSet = useMemo(() => new Set(errorQubits), [errorQubits]);
  const correctionSet = useMemo(
    () => new Set((cycleResult?.correction ?? []).map((v, i) => (v ? i : -1)).filter((i) => i >= 0)),
    [cycleResult]
  );
  const residualErrorQubits = useMemo(() => {
    if (!cycleResult) return new Set<number>();
    const residual = new Set<number>();
    for (let i = 0; i < n; i++) {
      const had = qubitErrorSet.has(i) ? 1 : 0;
      const corr = correctionSet.has(i) ? 1 : 0;
      if ((had + corr) % 2 === 1) residual.add(i);
    }
    return residual;
  }, [cycleResult, qubitErrorSet, correctionSet, n]);

  return (
    <div className="h-full flex flex-col text-[var(--text-primary)] overflow-hidden animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-[var(--border)] bg-[var(--bg-panel)]">
        <span className="text-[11px] font-semibold text-[var(--accent-primary)]">QEC Lab</span>
        <span className="text-[9px] text-[var(--text-muted)]">Real abirqu.qec encode → syndrome → decode</span>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        {/* Code Selector */}
        <div className="space-y-1.5">
          <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Error Correcting Code</label>
          <select
            value={selectedCode}
            onChange={(e) => {
              const next = e.target.value as QECCode;
              const nextInfo = CODES.find((c) => c.id === next)!;
              setSelectedCode(next);
              setSelectedSize(nextInfo.defaultSize);
              setCycleResult(null);
              setErrorQubits([]);
              setHasDecoded(false);
              setEncodeError(null);
              setDecodeError(null);
            }}
            className="w-full px-2 py-1.5 rounded-md bg-[var(--bg-input)] border border-[var(--border)] text-[11px] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
          >
            {CODES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <div className="text-[9px] text-[var(--text-muted)] px-0.5">
            Color and LDPC codes aren't offered here — verified incompatible with the current decoder API upstream.
          </div>
        </div>

        {/* Size selector (repetition / surface) */}
        {code.sizeOptions && (
          <div className="space-y-1.5 animate-fade-in">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              {code.id === 'surface' ? 'Distance' : 'n (qubits)'}
            </label>
            <div className="flex gap-1">
              {code.sizeOptions.map((s) => (
                <button
                  key={s}
                  onClick={() => {
                    setSelectedSize(s);
                    setCycleResult(null);
                    setErrorQubits([]);
                    setHasDecoded(false);
                  }}
                  className={`flex-1 px-2 py-1 rounded-md text-[10px] font-mono font-bold border transition-all ${
                    (selectedSize ?? code.defaultSize) === s
                      ? 'bg-[var(--accent-primary)]/10 border-[var(--accent-primary)]/40 text-[var(--accent-primary)]'
                      : 'bg-[var(--bg-input)] border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--border-strong)]'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Code Properties */}
        <div className="flex gap-2 animate-fade-in">
          <div className="flex-1 rounded-md bg-[var(--bg-input)] border border-[var(--border)] px-2 py-1.5 text-center">
            <div className="text-[9px] text-[var(--text-muted)]">n (physical)</div>
            <div className="text-[11px] font-mono font-bold text-[var(--accent-primary)]">{(displayOverhead as any).n}</div>
          </div>
          <div className="flex-1 rounded-md bg-[var(--bg-input)] border border-[var(--border)] px-2 py-1.5 text-center">
            <div className="text-[9px] text-[var(--text-muted)]">k (logical)</div>
            <div className="text-[11px] font-mono font-bold text-[var(--accent-primary)]">{(displayOverhead as any).k}</div>
          </div>
          <div className="flex-1 rounded-md bg-[var(--bg-input)] border border-[var(--border)] px-2 py-1.5 text-center">
            <div className="text-[9px] text-[var(--text-muted)]">d (distance)</div>
            <div className="text-[11px] font-mono font-bold text-[var(--accent-primary)]">{(displayOverhead as any).d}</div>
          </div>
        </div>
        {cycleResult && (
          <div className="text-[9px] text-[var(--accent-success)] px-0.5">✓ Live values from the last real backend run</div>
        )}

        {/* Encode Button */}
        <button
          onClick={handleEncode}
          disabled={encoding}
          className="w-full py-1.5 rounded-md bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 text-[11px] font-medium text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/20 transition-colors disabled:opacity-50"
        >
          {encoding ? (
            <span className="flex items-center justify-center gap-1.5">
              <span className="w-3 h-3 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin" />
              Encoding + computing syndrome...
            </span>
          ) : (
            'Encode (inject random test error)'
          )}
        </button>
        {encodeError && (
          <div className="text-[10px] text-[var(--accent-error)] bg-[var(--accent-error)]/10 rounded-lg p-2 border border-[var(--accent-error)]/20">
            {encodeError}
          </div>
        )}

        {/* Qubit Grid */}
        {cycleResult && (
          <div className="space-y-1.5 animate-fade-in">
            <div className="flex items-center gap-2">
              <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Qubit State</label>
              <div className="flex items-center gap-2 ml-auto">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: 'var(--accent-error)', opacity: 0.3 }} />
                  <span className="text-[8px] text-[var(--text-muted)]">Error</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: 'var(--accent-success)', opacity: 0.3 }} />
                  <span className="text-[8px] text-[var(--text-muted)]">Clean</span>
                </div>
              </div>
            </div>
            <div className="rounded-md bg-[var(--bg-input)] border border-[var(--border)] p-2">
              <div className="flex flex-wrap gap-1 justify-center">
                {Array.from({ length: n }, (_, i) => i).map((qid) => {
                  const hasError = hasDecoded ? residualErrorQubits.has(qid) : qubitErrorSet.has(qid);
                  return (
                    <div
                      key={qid}
                      className="w-8 h-8 rounded-md border border-[var(--border-strong)] flex flex-col items-center justify-center transition-all duration-300"
                      style={{
                        backgroundColor: `${hasError ? 'var(--accent-error)' : 'var(--accent-success)'}15`,
                      }}
                    >
                      <span
                        className="text-[10px] font-mono font-bold"
                        style={{ color: hasError ? 'var(--accent-error)' : 'var(--accent-success)' }}
                      >
                        {hasError ? '✕' : '✓'}
                      </span>
                      <span className="text-[8px] text-[var(--text-muted)]">q{qid}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Syndrome Display */}
        {cycleResult && (
          <div className="space-y-1.5 animate-fade-in">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Syndrome</label>
            <div className="rounded-md bg-[var(--bg-input)] border border-[var(--border)] p-2">
              <div className="flex flex-wrap gap-1 mb-1.5">
                {cycleResult.syndrome.map((bit, i) => (
                  <span
                    key={i}
                    className={`inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-mono font-bold border ${
                      bit === 1
                        ? 'bg-[var(--accent-error)]/15 border-[var(--accent-error)]/40 text-[var(--accent-error)]'
                        : 'bg-[var(--bg-hover)] border-[var(--border)] text-[var(--text-muted)]'
                    }`}
                  >
                    {bit}
                  </span>
                ))}
              </div>
              <div className="text-[9px] text-[var(--text-muted)]">
                {cycleResult.syndrome.some((b) => b === 1) ? (
                  <span>{cycleResult.syndrome.filter((b) => b === 1).length} stabilizer(s) triggered</span>
                ) : (
                  <span className="text-[var(--accent-success)]">No errors detected</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Decoder Selector */}
        {cycleResult && (
          <div className="space-y-1.5 animate-fade-in">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Decoder</label>
            <div className="flex gap-1">
              {DECODERS.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelectedDecoder(d.id)}
                  className={`flex-1 px-2 py-1.5 rounded-md text-[10px] font-medium border transition-all ${
                    selectedDecoder === d.id
                      ? 'bg-[var(--accent-primary)]/15 border-[var(--accent-primary)]/40 text-[var(--accent-primary)]'
                      : 'bg-[var(--bg-input)] border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--border-strong)]'
                  }`}
                >
                  {d.name}
                </button>
              ))}
            </div>
            <div className="text-[9px] text-[var(--text-muted)] px-1">
              {DECODERS.find((d) => d.id === selectedDecoder)?.description}
            </div>
            {DECODERS.find((d) => d.id === selectedDecoder)?.caveat && (
              <div className="text-[9px] text-[var(--accent-warning,#eab308)] px-1">
                ⚠ {DECODERS.find((d) => d.id === selectedDecoder)?.caveat}
              </div>
            )}
          </div>
        )}

        {/* Decode Button */}
        {cycleResult && (
          <button
            onClick={handleDecode}
            disabled={decoding}
            className="w-full py-1.5 rounded-md bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 text-[11px] font-medium text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/20 transition-colors disabled:opacity-50"
          >
            {decoding ? 'Decoding...' : `Decode (${DECODERS.find((d) => d.id === selectedDecoder)?.name})`}
          </button>
        )}
        {decodeError && (
          <div className="text-[10px] text-[var(--accent-error)] bg-[var(--accent-error)]/10 rounded-lg p-2 border border-[var(--accent-error)]/20">
            {decodeError}
          </div>
        )}

        {/* Correction Result */}
        {hasDecoded && cycleResult && (
          <div className="space-y-1.5 animate-fade-in">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Correction Result</label>
            <div className="rounded-md bg-[var(--bg-input)] border border-[var(--border)] p-2">
              <div className="flex items-center gap-2 mb-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    cycleResult.corrected_successfully ? 'bg-[var(--accent-success)]' : 'bg-[var(--accent-error)]'
                  }`}
                />
                <span className="text-[11px] font-medium text-[var(--text-primary)]">
                  {cycleResult.corrected_successfully
                    ? 'All errors corrected'
                    : `${residualErrorQubits.size} residual error(s)`}
                </span>
              </div>
              {!cycleResult.corrected_successfully && (
                <div className="flex flex-wrap gap-1">
                  {Array.from(residualErrorQubits).map((qid) => (
                    <span
                      key={qid}
                      className="px-1.5 py-0.5 rounded bg-[var(--accent-error)]/10 border border-[var(--accent-error)]/30 text-[9px] font-mono text-[var(--accent-error)]"
                    >
                      q{qid}
                    </span>
                  ))}
                </div>
              )}
              {cycleResult.corrected_successfully && (
                <div className="text-[9px] text-[var(--accent-success)] mt-1">✓ Decoding successful</div>
              )}
            </div>
          </div>
        )}

        {/* Magic State Distillation */}
        <div className="space-y-1.5">
          <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Magic State Distillation</label>
          <div className="rounded-md bg-[var(--bg-input)] border border-[var(--border)] p-2 space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[var(--text-secondary)]">Rounds:</span>
              {[1, 2, 3, 4, 5].map((r) => (
                <button
                  key={r}
                  onClick={() => setDistillRound(r)}
                  className={`w-6 h-6 rounded text-[10px] font-mono font-bold border transition-all ${
                    distillRound === r
                      ? 'bg-[var(--accent-primary)]/15 border-[var(--accent-primary)]/40 text-[var(--accent-primary)]'
                      : 'border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--border-strong)]'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="rounded border border-[var(--border)] p-2">
                <div className="text-[10px] text-[var(--text-muted)] mb-1">T-State (abirqu.qec.TStateFactory)</div>
                <div className="text-[11px] font-mono text-[var(--text-primary)]">
                  {distillResults[0] ? (
                    distillResults[0]!.success ? (
                      <span className="text-[var(--accent-success)]">
                        Fid: {(distillResults[0]!.fidelity * 100).toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-[var(--accent-error)]">Failed</span>
                    )
                  ) : (
                    <span className="text-[var(--text-muted)]">—</span>
                  )}
                </div>
              </div>
              <div className="rounded border border-[var(--border)] p-2">
                <div className="text-[10px] text-[var(--text-muted)] mb-1">H-State (abirqu.qec.HStateDistiller)</div>
                <div className="text-[11px] font-mono text-[var(--text-primary)]">
                  {distillResults[1] ? (
                    distillResults[1]!.success ? (
                      <span className="text-[var(--accent-success)]">
                        Fid: {(distillResults[1]!.fidelity * 100).toFixed(2)}%
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
            <div className="text-[9px] text-[var(--text-muted)]">
              ⚠ Verified while wiring this: HStateDistiller consistently returns 50% fidelity regardless of input —
              looks like an upstream SDK issue, not a display bug. Reported as-is.
            </div>

            <button
              onClick={handleDistill}
              disabled={distilling}
              className="w-full py-1 rounded-md bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 text-[10px] font-medium text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/20 transition-colors disabled:opacity-50"
            >
              {distilling ? 'Running...' : 'Run Distillation'}
            </button>
            {distillError && (
              <div className="text-[10px] text-[var(--accent-error)] bg-[var(--accent-error)]/10 rounded-lg p-2 border border-[var(--accent-error)]/20">
                {distillError}
              </div>
            )}
          </div>
        </div>

        {/* Statistics */}
        {stats.totalRuns > 0 && (
          <div className="space-y-1.5">
            <label className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Statistics</label>
            <div className="rounded-md bg-[var(--bg-input)] border border-[var(--border)] p-2">
              <div className="grid grid-cols-3 gap-2 mb-2">
                <div>
                  <div className="text-[9px] text-[var(--text-muted)]">Total Runs</div>
                  <div className="text-[11px] font-mono font-bold text-[var(--text-primary)]">{stats.totalRuns}</div>
                </div>
                <div>
                  <div className="text-[9px] text-[var(--text-muted)]">Logical Error Rate</div>
                  <div className="text-[11px] font-mono font-bold text-[var(--accent-error)]">
                    {((1 - successRate) * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-[9px] text-[var(--text-muted)]">Success Rate</div>
                  <div className="text-[11px] font-mono font-bold text-[var(--accent-success)]">
                    {(successRate * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {stats.totalRuns > 0 && (
                <div className="mt-1">
                  <div className="w-full h-2 rounded-full bg-[var(--bg-primary)] overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${successRate * 100}%`,
                        background: `linear-gradient(90deg, var(--accent-success), var(--accent-primary))`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-1.5 border-t border-[var(--border)] text-[9px] text-[var(--text-muted)] flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)]" />
        <span>
          {code.name} · {n}q · Decoder: {DECODERS.find((d) => d.id === selectedDecoder)?.name} · Live abirqu.qec
        </span>
      </div>
    </div>
  );
}
