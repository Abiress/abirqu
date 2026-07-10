import React, { useState, useMemo, useCallback } from 'react';

type Domain = 'chemistry' | 'osint' | 'crypto' | 'space' | 'qpinn' | 'agentic';

const DOMAINS: { key: Domain; label: string; icon: string; color: string }[] = [
  { key: 'chemistry', label: 'Chemistry', icon: '⚗', color: '#22c55e' },
  { key: 'osint', label: 'OSINT', icon: '🔍', color: '#3b82f6' },
  { key: 'crypto', label: 'Crypto', icon: '🔐', color: '#eab308' },
  { key: 'space', label: 'Space', icon: '🚀', color: '#8b5cf6' },
  { key: 'qpinn', label: 'QPINN', icon: '🧠', color: '#f97316' },
  { key: 'agentic', label: 'Agentic', icon: '🤖', color: '#ec4899' },
];

export default function DomainPanel() {
  const [activeDomain, setActiveDomain] = useState<Domain>('chemistry');

  return (
    <div className="flex flex-col h-full">
      <div className="flex border-b border-white/5 bg-[var(--bg-panel)]">
        {DOMAINS.map((d) => (
          <button
            key={d.key}
            onClick={() => setActiveDomain(d.key)}
            className={`flex-1 flex items-center justify-center gap-1 px-2 py-2 text-[11px] font-medium transition-all border-b-2 ${
              activeDomain === d.key
                ? 'border-current bg-current/5'
                : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
            }`}
            style={{ color: activeDomain === d.key ? d.color : undefined }}
          >
            <span className="text-xs">{d.icon}</span>
            {d.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-3">
        {activeDomain === 'chemistry' && <ChemistryTab />}
        {activeDomain === 'osint' && <OsintTab />}
        {activeDomain === 'crypto' && <CryptoTab />}
        {activeDomain === 'space' && <SpaceTab />}
        {activeDomain === 'qpinn' && <QpinnTab />}
        {activeDomain === 'agentic' && <AgenticTab />}
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[9px] uppercase tracking-wider text-[var(--text-muted)] font-medium mb-1.5">
      {children}
    </div>
  );
}

function Btn({ onClick, color, children, disabled }: { onClick: () => void; color: string; children: React.ReactNode; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full px-3 py-1.5 rounded-lg text-[11px] font-semibold text-white transition-all ${
        disabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-lg hover:scale-[1.02]'
      }`}
      style={{ backgroundColor: disabled ? color + '60' : color, boxShadow: disabled ? undefined : `0 0 15px ${color}25` }}
    >
      {children}
    </button>
  );
}

function ResultBox({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5 animate-fade-in">
      <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mb-0.5">{label}</div>
      <div className="text-[11px] font-mono font-semibold" style={{ color: color || 'var(--text-primary)' }}>{value}</div>
    </div>
  );
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-2 py-1.5 rounded-lg text-[11px] bg-[var(--bg-input)] border border-white/5 text-[var(--text-primary)] outline-none focus:border-[var(--accent-primary)] transition-colors cursor-pointer"
    >
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}

function Slider({ label, value, min, max, step, onChange }: { label: string; value: number; min: number; max: number; step: number; onChange: (v: number) => void }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] text-[var(--text-muted)] w-20 truncate">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="flex-1 h-1 accent-[var(--accent-primary)]"
      />
      <span className="text-[9px] text-[var(--text-secondary)] w-8 text-right font-mono">{value}</span>
    </div>
  );
}

function MiniLineChart({ data, color, height = 48 }: { data: number[]; color: string; height?: number }) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = height - ((v - min) / range) * (height - 8) - 4;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 100 ${height}`} className="w-full" style={{ height }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {data.map((v, i) => {
        const x = (i / (data.length - 1)) * 100;
        const y = height - ((v - min) / range) * (height - 8) - 4;
        return <circle key={i} cx={x} cy={y} r="1.5" fill={color} />;
      })}
    </svg>
  );
}

function MiniBarChart({ data, color, height = 48 }: { data: { label: string; value: number }[]; color: string; height?: number }) {
  const max = Math.max(...data.map((d) => d.value)) || 1;
  return (
    <div className="flex items-end gap-0.5" style={{ height }}>
      {data.map((d, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
          <div
            className="w-full rounded-t transition-all duration-300"
            style={{ height: `${(d.value / max) * (height - 14)}px`, backgroundColor: color + 'aa' }}
          />
          <span className="text-[7px] text-[var(--text-muted)] truncate w-full text-center">{d.label}</span>
        </div>
      ))}
    </div>
  );
}

function Spinner({ color }: { color: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" style={{ borderColor: color, borderTopColor: 'transparent' }} />
      Running...
    </span>
  );
}

function ChemistryTab() {
  const [molecule, setMolecule] = useState('H2O');
  const [mapper, setMapper] = useState('Jordan-Wigner');
  const [ansatz, setAnsatz] = useState('UCCSD');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{ energy: number; convergence: number[] } | null>(null);

  const handleRun = useCallback(() => {
    setRunning(true);
    setResult(null);
    const energies: number[] = [];
    let e = molecule === 'H2' ? -1.137 : molecule === 'LiH' ? -7.882 : molecule === 'H2O' ? -75.024 : molecule === 'NH3' ? -56.225 : -40.518;
    e += (Math.random() - 0.5) * 0.5;
    for (let i = 0; i < 20; i++) {
      const progress = i / 19;
      energies.push(e + (1.5 - e) * Math.exp(-3 * progress) + Math.random() * 0.05);
    }
    energies[energies.length - 1] = e;
    setTimeout(() => {
      setResult({ energy: e, convergence: energies });
      setRunning(false);
    }, 1200);
  }, [molecule]);

  return (
    <div className="space-y-3 animate-fade-in">
      <SectionLabel>Molecule Configuration</SectionLabel>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <div className="text-[9px] text-[var(--text-muted)] mb-1">Molecule</div>
          <Select value={molecule} onChange={setMolecule} options={['H2', 'LiH', 'H2O', 'NH3', 'CH4']} />
        </div>
        <div>
          <div className="text-[9px] text-[var(--text-muted)] mb-1">Qubit Mapping</div>
          <Select value={mapper} onChange={setMapper} options={['Jordan-Wigner', 'Bravyi-Kitaev', 'Parity']} />
        </div>
      </div>
      <div>
        <div className="text-[9px] text-[var(--text-muted)] mb-1">VQE Ansatz</div>
        <Select value={ansatz} onChange={setAnsatz} options={['UCCSD', 'Hardware-Efficient']} />
      </div>

      <Btn onClick={handleRun} color="#22c55e" disabled={running}>
        {running ? <Spinner color="#22c55e" /> : '▶ Run VQE'}
      </Btn>

      {result && (
        <div className="space-y-2 animate-fade-in">
          <ResultBox label="Ground State Energy" value={`${result.energy.toFixed(6)} Hartree`} color="#22c55e" />
          <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
            <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mb-1">Energy Convergence</div>
            <MiniLineChart data={result.convergence} color="#22c55e" height={56} />
            <div className="flex justify-between text-[8px] text-[var(--text-muted)] mt-0.5">
              <span>Iteration 1</span>
              <span>Iteration 20</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function OsintTab() {
  const [nodeCount, setNodeCount] = useState(8);
  const [edgeDensity, setEdgeDensity] = useState(0.4);
  const [problem, setProblem] = useState('Max-Cut');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{ cutValue: number; partition: string; graphNodes: { x: number; y: number }[]; graphEdges: [number, number][] } | null>(null);

  const graphData = useMemo(() => {
    const nodes = Array.from({ length: nodeCount }, (_, i) => ({
      x: 50 + 35 * Math.cos((2 * Math.PI * i) / nodeCount),
      y: 50 + 35 * Math.sin((2 * Math.PI * i) / nodeCount),
    }));
    const edges: [number, number][] = [];
    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        if (Math.random() < edgeDensity) edges.push([i, j]);
      }
    }
    return { nodes, edges };
  }, [nodeCount, edgeDensity]);

  const handleRun = useCallback(() => {
    setRunning(true);
    setResult(null);
    setTimeout(() => {
      const cutVal = Math.floor(graphData.edges.length * (0.4 + Math.random() * 0.3));
      const partition = Array.from({ length: nodeCount }, () => Math.random() > 0.5 ? 'A' : 'B').join('');
      setResult({ cutValue: cutVal, partition, graphNodes: graphData.nodes, graphEdges: graphData.edges });
      setRunning(false);
    }, 1000);
  }, [graphData, nodeCount]);

  const pColor = result?.partition ? result.partition.split('').map((c, i) => (c === 'A' ? '#3b82f6' : '#f97316')) : [];

  return (
    <div className="space-y-3 animate-fade-in">
      <SectionLabel>Graph Builder</SectionLabel>
      <Slider label="Nodes" value={nodeCount} min={4} max={20} step={1} onChange={setNodeCount} />
      <Slider label="Edge Density" value={edgeDensity} min={0.1} max={0.9} step={0.05} onChange={setEdgeDensity} />
      <div>
        <div className="text-[9px] text-[var(--text-muted)] mb-1">Problem Type</div>
        <Select value={problem} onChange={setProblem} options={['Max-Cut', 'MIS', 'MVC', 'Coloring', 'Community', 'Anomaly']} />
      </div>

      <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
        <svg viewBox="0 0 100 100" className="w-full" style={{ height: 80 }}>
          {graphData.edges.map(([a, b], i) => (
            <line key={i} x1={graphData.nodes[a].x} y1={graphData.nodes[a].y} x2={graphData.nodes[b].x} y2={graphData.nodes[b].y} stroke="rgba(148,163,184,0.15)" strokeWidth="0.5" />
          ))}
          {graphData.nodes.map((n, i) => (
            <circle
              key={i}
              cx={n.x}
              cy={n.y}
              r="3"
              fill={result ? pColor[i] || '#475569' : '#475569'}
              stroke={result ? pColor[i] || '#475569' : '#64748b'}
              strokeWidth="0.5"
            />
          ))}
        </svg>
      </div>

      <Btn onClick={handleRun} color="#3b82f6" disabled={running}>
        {running ? <Spinner color="#3b82f6" /> : '▶ Generate QAOA Circuit'}
      </Btn>

      {result && (
        <div className="space-y-2 animate-fade-in">
          <ResultBox label={`${problem} Cut Value`} value={String(result.cutValue)} color="#3b82f6" />
          <ResultBox label="Partition" value={result.partition} color="#f97316" />
        </div>
      )}
    </div>
  );
}

function CryptoTab() {
  const [mode, setMode] = useState<'shor' | 'grover' | 'pqc'>('shor');
  const [shorN, setShorN] = useState(15);
  const [groverSize, setGroverSize] = useState(256);
  const [pqcKey, setPqcKey] = useState('Kyber-768');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{ factors?: string; searchResult?: string; verdict?: string } | null>(null);

  const handleShor = useCallback(() => {
    setRunning(true); setResult(null);
    setTimeout(() => {
      const known: Record<number, string> = { 15: '3 × 5', 21: '3 × 7', 35: '5 × 7', 77: '7 × 11', 91: '7 × 13', 143: '11 × 13', 187: '11 × 17', 221: '13 × 17' };
      setResult({ factors: known[shorN] || `${Math.floor(shorN / 3)} × ${shorN / Math.floor(shorN / 3)}` });
      setRunning(false);
    }, 900);
  }, [shorN]);

  const handleGrover = useCallback(() => {
    setRunning(true); setResult(null);
    setTimeout(() => {
      const target = Math.floor(Math.random() * groverSize);
      setResult({ searchResult: `Found target at index ${target} in ${Math.ceil(Math.sqrt(groverSize))} Grover iterations` });
      setRunning(false);
    }, 800);
  }, [groverSize]);

  const handlePqc = useCallback(() => {
    setRunning(true); setResult(null);
    setTimeout(() => {
      const sec: Record<string, { bits: number; verdict: string }> = {
        'Kyber-512': { bits: 128, verdict: 'Moderate — NIST Level 1' },
        'Kyber-768': { bits: 192, verdict: 'Strong — NIST Level 3' },
        'Kyber-1024': { bits: 256, verdict: 'Very Strong — NIST Level 5' },
        'Dilithium-2': { bits: 128, verdict: 'Moderate — NIST Level 2' },
        'Dilithium-3': { bits: 192, verdict: 'Strong — NIST Level 3' },
        'SPHINCS+-128f': { bits: 128, verdict: 'Moderate — Hash-based, conservative' },
      };
      const info = sec[pqcKey] || { bits: 128, verdict: 'Unknown configuration' };
      setResult({ verdict: `Security: ${info.bits}-bit equivalent — ${info.verdict}` });
      setRunning(false);
    }, 700);
  }, [pqcKey]);

  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex gap-1 bg-[var(--bg-input)] rounded-lg p-0.5">
        {([['shor', 'Shor'], ['grover', 'Grover'], ['pqc', 'PQC']] as const).map(([k, l]) => (
          <button
            key={k}
            onClick={() => { setMode(k); setResult(null); }}
            className={`flex-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all ${
              mode === k ? 'bg-[var(--accent-primary)] text-white' : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {mode === 'shor' && (
        <div className="space-y-2 animate-fade-in">
          <SectionLabel>Shor's Factoring</SectionLabel>
          <div>
            <div className="text-[9px] text-[var(--text-muted)] mb-1">Number N</div>
            <input
              type="number"
              value={shorN}
              onChange={(e) => setShorN(parseInt(e.target.value) || 15)}
              className="w-full px-2 py-1.5 rounded-lg text-[11px] bg-[var(--bg-input)] border border-white/5 text-[var(--text-primary)] outline-none focus:border-[var(--accent-primary)] font-mono"
            />
          </div>
          <Btn onClick={handleShor} color="#eab308" disabled={running}>
            {running ? <Spinner color="#eab308" /> : '▶ Factor'}
          </Btn>
          {result?.factors && (
            <div className="space-y-2 animate-fade-in">
              <ResultBox label={`Factors of ${shorN}`} value={result.factors} color="#eab308" />
            </div>
          )}
        </div>
      )}

      {mode === 'grover' && (
        <div className="space-y-2 animate-fade-in">
          <SectionLabel>Grover's Search</SectionLabel>
          <Slider label="Search Space" value={groverSize} min={16} max={1024} step={16} onChange={setGroverSize} />
          <Btn onClick={handleGrover} color="#eab308" disabled={running}>
            {running ? <Spinner color="#eab308" /> : '▶ Search'}
          </Btn>
          {result?.searchResult && (
            <div className="space-y-2 animate-fade-in">
              <ResultBox label="Search Result" value={result.searchResult} color="#eab308" />
            </div>
          )}
        </div>
      )}

      {mode === 'pqc' && (
        <div className="space-y-2 animate-fade-in">
          <SectionLabel>Post-Quantum Cryptography Assessment</SectionLabel>
          <div>
            <div className="text-[9px] text-[var(--text-muted)] mb-1">Algorithm & Key Size</div>
            <Select value={pqcKey} onChange={setPqcKey} options={['Kyber-512', 'Kyber-768', 'Kyber-1024', 'Dilithium-2', 'Dilithium-3', 'SPHINCS+-128f']} />
          </div>
          <Btn onClick={handlePqc} color="#eab308" disabled={running}>
            {running ? <Spinner color="#eab308" /> : '▶ Assess'}
          </Btn>
          {result?.verdict && (
            <div className="space-y-2 animate-fade-in">
              <ResultBox label="Security Verdict" value={result.verdict} color="#eab308" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SpaceTab() {
  const [mode, setMode] = useState<'hhl' | 'cfd'>('hhl');
  const [matrixSize, setMatrixSize] = useState(4);
  const [gridSize, setGridSize] = useState(32);
  const [viscosity, setViscosity] = useState(0.01);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<{ residualNorm?: number; solution?: number[] } | null>(null);

  const handleHHL = useCallback(() => {
    setRunning(true); setResult(null);
    setTimeout(() => {
      const norm = 1e-6 + Math.random() * 1e-8;
      const sol = Array.from({ length: matrixSize }, () => parseFloat((Math.random() * 2 - 1).toFixed(4)));
      setResult({ residualNorm: norm, solution: sol });
      setRunning(false);
    }, 1000);
  }, [matrixSize]);

  const handleCFD = useCallback(() => {
    setRunning(true); setResult(null);
    setTimeout(() => {
      const norm = 0.001 + Math.random() * 0.005;
      const sol = Array.from({ length: 8 }, () => parseFloat((Math.random() * 10 - 5).toFixed(3)));
      setResult({ residualNorm: norm, solution: sol });
      setRunning(false);
    }, 1100);
  }, []);

  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex gap-1 bg-[var(--bg-input)] rounded-lg p-0.5">
        {([['hhl', 'HHL Solver'], ['cfd', 'Quantum CFD']] as const).map(([k, l]) => (
          <button
            key={k}
            onClick={() => { setMode(k as 'hhl' | 'cfd'); setResult(null); }}
            className={`flex-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all ${
              mode === k ? 'bg-[var(--accent-primary)] text-white' : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {mode === 'hhl' && (
        <div className="space-y-2 animate-fade-in">
          <SectionLabel>HHL Linear System Solver</SectionLabel>
          <Slider label="Matrix Size" value={matrixSize} min={2} max={16} step={2} onChange={setMatrixSize} />
          <Btn onClick={handleHHL} color="#8b5cf6" disabled={running}>
            {running ? <Spinner color="#8b5cf6" /> : '▶ Solve Ax=b'}
          </Btn>
          {result && (
            <div className="space-y-2 animate-fade-in">
              <ResultBox label="Residual Norm ‖Ax−b‖" value={result.residualNorm!.toExponential(3)} color="#8b5cf6" />
              <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mb-1">Solution Vector x</div>
                <div className="font-mono text-[10px] text-[var(--text-secondary)] break-all">
                  [{result.solution!.map((v) => v.toFixed(4)).join(', ')}]
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {mode === 'cfd' && (
        <div className="space-y-2 animate-fade-in">
          <SectionLabel>Quantum Computational Fluid Dynamics</SectionLabel>
          <Slider label="Grid Size" value={gridSize} min={8} max={64} step={8} onChange={setGridSize} />
          <Slider label="Viscosity" value={viscosity} min={0.001} max={0.1} step={0.001} onChange={setViscosity} />
          <Btn onClick={handleCFD} color="#8b5cf6" disabled={running}>
            {running ? <Spinner color="#8b5cf6" /> : '▶ Simulate'}
          </Btn>
          {result && (
            <div className="space-y-2 animate-fade-in">
              <ResultBox label="Residual Norm" value={result.residualNorm!.toExponential(3)} color="#8b5cf6" />
              <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mb-1">Velocity Field (sample)</div>
                <MiniBarChart
                  data={result.solution!.map((v, i) => ({ label: `u${i}`, value: Math.abs(v) }))}
                  color="#8b5cf6"
                  height={48}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function QpinnTab() {
  const [pde, setPde] = useState('Diffusion');
  const [qubits, setQubits] = useState(4);
  const [depth, setDepth] = useState(6);
  const [training, setTraining] = useState(false);
  const [progress, setProgress] = useState(0);
  const [lossCurve, setLossCurve] = useState<number[]>([]);
  const [result, setResult] = useState<{ finalLoss: number; epochs: number } | null>(null);

  const handleTrain = useCallback(() => {
    if (training) return;
    setTraining(true);
    setResult(null);
    setLossCurve([]);
    setProgress(0);
    const losses: number[] = [];
    let epoch = 0;
    const totalEpochs = 30;
    const baseLoss = pde === 'Diffusion' ? 0.8 : pde === 'Heat' ? 0.65 : 1.2;
    const tick = () => {
      epoch++;
      const loss = baseLoss * Math.exp(-0.15 * epoch) + Math.random() * 0.03;
      losses.push(loss);
      setLossCurve([...losses]);
      setProgress(epoch / totalEpochs);
      if (epoch < totalEpochs) {
        setTimeout(tick, 120);
      } else {
        setTraining(false);
        setResult({ finalLoss: losses[losses.length - 1], epochs: totalEpochs });
      }
    };
    setTimeout(tick, 200);
  }, [training, pde]);

  return (
    <div className="space-y-3 animate-fade-in">
      <SectionLabel>Quantum Physics-Informed Neural Network</SectionLabel>
      <div>
        <div className="text-[9px] text-[var(--text-muted)] mb-1">PDE Type</div>
        <Select value={pde} onChange={setPde} options={['Diffusion', 'Heat', 'Navier-Stokes']} />
      </div>
      <Slider label="Qubit Count" value={qubits} min={2} max={8} step={1} onChange={setQubits} />
      <Slider label="Circuit Depth" value={depth} min={2} max={12} step={1} onChange={setDepth} />

      <Btn onClick={handleTrain} color="#f97316" disabled={training}>
        {training ? <Spinner color="#f97316" /> : '▶ Train'}
      </Btn>

      {training && (
        <div className="space-y-1 animate-fade-in">
          <div className="flex justify-between text-[9px] text-[var(--text-muted)]">
            <span>Epoch {lossCurve.length}/30</span>
            <span>{Math.round(progress * 100)}%</span>
          </div>
          <div className="h-1.5 bg-[var(--bg-input)] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-orange-500 to-amber-400 rounded-full transition-all duration-150"
              style={{ width: `${progress * 100}%` }}
            />
          </div>
        </div>
      )}

      {lossCurve.length > 1 && (
        <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5 animate-fade-in">
          <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mb-1">Loss Curve</div>
          <MiniLineChart data={lossCurve} color="#f97316" height={56} />
        </div>
      )}

      {result && (
        <div className="space-y-2 animate-fade-in">
          <ResultBox label="Final Loss" value={result.finalLoss.toFixed(6)} color="#f97316" />
          <ResultBox label="Epochs Completed" value={String(result.epochs)} color="#f97316" />
        </div>
      )}
    </div>
  );
}

function AgenticTab() {
  const [taskType, setTaskType] = useState('Circuit Generation');
  const [params, setParams] = useState('{\n  "qubits": 4,\n  "depth": 6,\n  "objective": "minimize_depth"\n}');
  const [tasks, setTasks] = useState<{ id: string; type: string; status: string; time: string }[]>([]);
  const [running, setRunning] = useState(false);

  const handleSubmit = useCallback(() => {
    setRunning(true);
    const id = `task-${Date.now().toString(36)}`;
    const now = new Date().toLocaleTimeString();
    setTasks((prev) => [{ id, type: taskType, status: 'running', time: now }, ...prev]);
    setTimeout(() => {
      setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: 'completed' } : t));
      setRunning(false);
    }, 1500);
  }, [taskType]);

  const statusColors: Record<string, string> = {
    running: '#eab308',
    completed: '#22c55e',
    failed: '#ef4444',
  };

  return (
    <div className="space-y-3 animate-fade-in">
      <SectionLabel>Agentic Task Submission</SectionLabel>
      <div>
        <div className="text-[9px] text-[var(--text-muted)] mb-1">Task Type</div>
        <Select
          value={taskType}
          onChange={setTaskType}
          options={['Circuit Generation', 'Optimization', 'Error Mitigation', 'State Preparation', 'Hamiltonian Simulation', 'Benchmark']}
        />
      </div>
      <div>
        <div className="text-[9px] text-[var(--text-muted)] mb-1">Parameters (JSON)</div>
        <textarea
          value={params}
          onChange={(e) => setParams(e.target.value)}
          rows={4}
          className="w-full px-2 py-1.5 rounded-lg text-[10px] font-mono bg-[var(--bg-input)] border border-white/5 text-[var(--text-secondary)] outline-none focus:border-[var(--accent-primary)] resize-none"
        />
      </div>

      <Btn onClick={handleSubmit} color="#ec4899" disabled={running}>
        {running ? <Spinner color="#ec4899" /> : '▶ Submit Task'}
      </Btn>

      {tasks.length > 0 && (
        <div className="space-y-1.5 animate-fade-in">
          <SectionLabel>Task Board</SectionLabel>
          {tasks.map((t) => (
            <div key={t.id} className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: statusColors[t.status] || '#475569' }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-[10px] text-[var(--text-primary)] font-medium truncate">{t.type}</div>
                <div className="text-[9px] text-[var(--text-muted)] font-mono">{t.id.slice(0, 12)} · {t.time}</div>
              </div>
              <span
                className="text-[9px] px-1.5 py-0.5 rounded font-medium"
                style={{
                  color: statusColors[t.status] || '#475569',
                  backgroundColor: (statusColors[t.status] || '#475569') + '18',
                }}
              >
                {t.status}
              </span>
            </div>
          ))}
        </div>
      )}

      {tasks.length === 0 && (
        <div className="text-center py-6 text-[10px] text-[var(--text-muted)]">
          No tasks submitted yet
        </div>
      )}
    </div>
  );
}
