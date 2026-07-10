import React, { useState, useRef, useEffect, useCallback } from 'react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
}

interface PipelineStep {
  id: number;
  title: string;
  status: 'pending' | 'running' | 'done';
  content: React.ReactNode;
  editable?: boolean;
  hasRunButton?: boolean;
}

const EXAMPLE_QUESTIONS = [
  "What's the ground-state energy of H2?",
  'Factor 91',
  'Find Max-Cut for a 6-node graph',
  'Is 2048-bit RSA quantum-safe?',
];

function generatePipeline(question: string): PipelineStep[] {
  const q = question.toLowerCase();

  if (q.includes('h2') || q.includes('ground') || q.includes('hydrogen') || q.includes('energy')) {
    return [
      {
        id: 1,
        title: 'Intent Classification',
        status: 'pending',
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Domain</span><span className="text-[var(--accent-primary)]">Quantum Chemistry</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Sub-domain</span><span className="text-[var(--text-secondary)]">Molecular Ground State</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Confidence</span><span className="text-[var(--accent-success)]">96.2%</span></div>
          </div>
        ),
      },
      {
        id: 2,
        title: 'Problem Formalization',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">Hamiltonian (STO-3G, 4 qubits):</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2 break-all">
              H = -0.81261 IIII - 0.17121 ZIII - 0.22279 IZII - 0.22279 IIZI
              <br />+ 0.17121 ZIZI + 0.04532 ZIII - 0.04532 IZII + 0.12091 ZZII
            </div>
            <div className="text-[var(--text-muted)]">Method: VQE (UCCSD ansatz)</div>
          </div>
        ),
      },
      {
        id: 3,
        title: 'Circuit Synthesis',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Qubits</span><span className="text-[var(--text-primary)]">4</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Depth</span><span className="text-[var(--text-primary)]">12</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Gates</span><span className="text-[var(--text-primary)]">67</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Gate breakdown</span><span className="text-[var(--text-secondary)]">Rx: 14 · Ry: 14 · Rz: 8 · CNOT: 31</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Entangling gates</span><span className="text-[var(--text-secondary)]">31 CNOT</span></div>
          </div>
        ),
      },
      {
        id: 4,
        title: 'Execution Plan',
        status: 'pending',
        hasRunButton: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Backend</span><span className="text-[var(--text-primary)]">ibm_brisbane</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Shots</span><span className="text-[var(--text-primary)]">8192</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Est. runtime</span><span className="text-[var(--text-secondary)]">~4.2s (simulator)</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Est. cost</span><span className="text-[var(--accent-primary)]">$0.00 (local)</span></div>
          </div>
        ),
      },
      {
        id: 5,
        title: 'Raw Result',
        status: 'pending',
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">VQE convergence: 28 iterations</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2">
              <div>Eigenvalue: <span className="text-[var(--accent-primary)]">-1.1372 Ha</span></div>
              <div>State: <span className="text-[var(--text-secondary)]">0.997 |1100⟩ + 0.071 |0011⟩ + ...</span></div>
              <div>Convergence: <span className="text-[var(--accent-success)]">converged</span></div>
            </div>
          </div>
        ),
      },
      {
        id: 6,
        title: 'Final Answer',
        status: 'pending',
        content: (
          <div className="space-y-2">
            <div className="text-[var(--text-primary)] text-[11px] leading-relaxed">
              The ground-state energy of H₂ is <span className="text-[var(--accent-primary)] font-semibold">−1.1372 Hartree</span> (≈ −30.96 eV).
              This was computed using VQE with a UCCSD ansatz on 4 qubits in the STO-3G basis.
            </div>
            <div className="text-[9px] text-[var(--text-muted)] border-t border-white/5 pt-1">
              Citations: [1] Peruzzo et al., Nature Comm. 5, 4213 (2014) · [2] IBM Qiskit Nature tutorial
            </div>
          </div>
        ),
      },
    ];
  }

  if (q.includes('factor') || q.includes('91') || q.includes('integer')) {
    return [
      {
        id: 1,
        title: 'Intent Classification',
        status: 'pending',
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Domain</span><span className="text-[var(--accent-primary)]">Quantum Computing</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Sub-domain</span><span className="text-[var(--text-secondary)]">Integer Factorization</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Confidence</span><span className="text-[var(--accent-success)]">98.1%</span></div>
          </div>
        ),
      },
      {
        id: 2,
        title: 'Problem Formalization',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">Target: N = 91</div>
            <div className="text-[var(--text-muted)]">Algorithm: Shor's (period-finding)</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2">
              1. Pick random a = 5 (gcd(5,91) = 1 ✓)<br />
              2. Find r such that 5^r ≡ 1 (mod 91)<br />
              3. r = 6 → factors from gcd(5³ ± 1, 91)
            </div>
          </div>
        ),
      },
      {
        id: 3,
        title: 'Circuit Synthesis',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Qubits</span><span className="text-[var(--text-primary)]">12</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Depth</span><span className="text-[var(--text-primary)]">48</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Gates</span><span className="text-[var(--text-primary)]">196</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Gate breakdown</span><span className="text-[var(--text-secondary)]">H: 12 · CNOT: 78 · Modular-Mult: 106</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">QFT width</span><span className="text-[var(--text-secondary)]">8 qubits</span></div>
          </div>
        ),
      },
      {
        id: 4,
        title: 'Execution Plan',
        status: 'pending',
        hasRunButton: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Backend</span><span className="text-[var(--text-primary)]">simulator_stabilizer</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Shots</span><span className="text-[var(--text-primary)]">1024</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Est. runtime</span><span className="text-[var(--text-secondary)]">~2.1s</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Est. cost</span><span className="text-[var(--accent-primary)]">$0.00 (local)</span></div>
          </div>
        ),
      },
      {
        id: 5,
        title: 'Raw Result',
        status: 'pending',
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">Top measurement outcomes (period r):</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2">
              <div>|00000000⟩ → <span className="text-[var(--accent-primary)]">phase = 0.000 (r=1, trivial)</span></div>
              <div>|00101000⟩ → <span className="text-[var(--accent-primary)]">phase = 1/6 → r = 6</span> <span className="text-[var(--accent-success)]">★</span></div>
              <div>|01010000⟩ → <span className="text-[var(--text-muted)]">phase = 2/6 → r = 6</span></div>
              <div>|01111000⟩ → <span className="text-[var(--text-muted)]">phase = 3/6 → r = 6</span></div>
              <div>|10000000⟩ → <span className="text-[var(--text-muted)]">phase = 4/6 → r = 6</span></div>
            </div>
            <div className="text-[var(--text-muted)]">Recovered period: r = 6</div>
          </div>
        ),
      },
      {
        id: 6,
        title: 'Final Answer',
        status: 'pending',
        content: (
          <div className="space-y-2">
            <div className="text-[var(--text-primary)] text-[11px] leading-relaxed">
              91 = <span className="text-[var(--accent-primary)] font-semibold">7 × 13</span>.
              Shor's algorithm found period r = 6 for a = 5 mod 91, yielding factors gcd(5³+1, 91) = 14 and gcd(5³−1, 91) = 42, then gcd(14, 91) = 7 and gcd(42, 91) = 13.
            </div>
            <div className="text-[9px] text-[var(--text-muted)] border-t border-white/5 pt-1">
              Citations: [1] Shor, SIAM J. Comp. 26(5), 1484 (1997)
            </div>
          </div>
        ),
      },
    ];
  }

  if (q.includes('max-cut') || q.includes('maxcut') || q.includes('graph')) {
    return [
      {
        id: 1,
        title: 'Intent Classification',
        status: 'pending',
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Domain</span><span className="text-[var(--accent-primary)]">Quantum Optimization</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Sub-domain</span><span className="text-[var(--text-secondary)]">Max-Cut (Combinatorial)</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Confidence</span><span className="text-[var(--accent-success)]">97.8%</span></div>
          </div>
        ),
      },
      {
        id: 2,
        title: 'Problem Formalization',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">Graph: 6 nodes, 9 edges (Erdős–Rényi p=0.6)</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2">
              {'Edges: (0,1), (0,2), (0,4), (1,2), (1,3), (2,3), (2,5), (3,4), (4,5)'}
              <br />{'QUBO: H_C = Σ_{(i,j)∈E} (1 − Z_i Z_j) / 4'}
              <br />Method: QAOA with p = 3
            </div>
          </div>
        ),
      },
      {
        id: 3,
        title: 'Circuit Synthesis',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Qubits</span><span className="text-[var(--text-primary)]">6</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Depth</span><span className="text-[var(--text-primary)]">30</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Gates</span><span className="text-[var(--text-primary)]">84</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Gate breakdown</span><span className="text-[var(--text-secondary)]">H: 6 · Rx: 6 · CNOT: 54 · Rz: 18</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">QAOA layers (p)</span><span className="text-[var(--text-secondary)]">3</span></div>
          </div>
        ),
      },
      {
        id: 4,
        title: 'Execution Plan',
        status: 'pending',
        hasRunButton: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Backend</span><span className="text-[var(--text-primary)]">simulator_statevector</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Shots</span><span className="text-[var(--text-primary)]">4096</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Est. runtime</span><span className="text-[var(--text-secondary)]">~1.8s</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Optimizer</span><span className="text-[var(--text-secondary)]">COBYLA, max 100 iters</span></div>
          </div>
        ),
      },
      {
        id: 5,
        title: 'Raw Result',
        status: 'pending',
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">QAOA optimal angles: γ = [0.89, 1.12, 0.67], β = [0.41, 0.53, 0.32]</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2">
              <div>|011010⟩ → <span className="text-[var(--accent-primary)]">prob = 0.342</span> <span className="text-[var(--accent-success)]">★ cut=7</span></div>
              <div>|100101⟩ → prob = 0.298 → cut = 7</div>
              <div>|100110⟩ → prob = 0.121 → cut = 6</div>
              <div>|011001⟩ → prob = 0.108 → cut = 6</div>
            </div>
          </div>
        ),
      },
      {
        id: 6,
        title: 'Final Answer',
        status: 'pending',
        content: (
          <div className="space-y-2">
            <div className="text-[var(--text-primary)] text-[11px] leading-relaxed">
              The Max-Cut of the 6-node graph is <span className="text-[var(--accent-primary)] font-semibold">7 edges</span>.
              Partition: {'S = {0, 3, 5}, T̄ = {1, 2, 4}'}.
              QAOA (p=3) found this with probability 64% across 4096 shots.
            </div>
            <div className="text-[9px] text-[var(--text-muted)] border-t border-white/5 pt-1">
              Citations: [1] Farhi et al., arXiv:1411.4028 (2014) · [2] Google Quantum AI, Nature 574, 505 (2019)
            </div>
          </div>
        ),
      },
    ];
  }

  if (q.includes('rsa') || q.includes('2048') || q.includes('safe') || q.includes('quantum-safe') || q.includes('security')) {
    return [
      {
        id: 1,
        title: 'Intent Classification',
        status: 'pending',
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Domain</span><span className="text-[var(--accent-primary)]">Quantum Security</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Sub-domain</span><span className="text-[var(--text-secondary)]">Post-Quantum Cryptography</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Confidence</span><span className="text-[var(--accent-success)]">99.1%</span></div>
          </div>
        ),
      },
      {
        id: 2,
        title: 'Problem Formalization',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">Question type: Analysis (not execution)</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2">
              Evaluate quantum threat against RSA-2048:<br />
              • Shor's algorithm complexity: O((log N)³) quantum gates<br />
              • RSA-2048 modulus: N ≈ 2²⁰⁴⁸<br />
              • Required logical qubits: ~4096<br />
              • Required T-gates: ~10¹²
            </div>
          </div>
        ),
      },
      {
        id: 3,
        title: 'Circuit Synthesis',
        status: 'pending',
        editable: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Status</span><span className="text-[var(--accent-error)]">Exceeds current capability</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Logical qubits needed</span><span className="text-[var(--text-primary)]">4,096</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Physical qubits (w/ error correction)</span><span className="text-[var(--text-primary)]">~17.6M</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Current largest QPU</span><span className="text-[var(--text-secondary)]">~1,200 qubits (IBM Condor)</span></div>
            <div className="text-[9px] text-[var(--accent-error)] mt-1">⚠ No current quantum computer can run this circuit.</div>
          </div>
        ),
      },
      {
        id: 4,
        title: 'Execution Plan',
        status: 'pending',
        hasRunButton: true,
        content: (
          <div className="space-y-1">
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Execution type</span><span className="text-[var(--text-secondary)]">Analytical estimate</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Model</span><span className="text-[var(--text-primary)]">Resource estimation (no runtime)</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Est. timeline</span><span className="text-[var(--accent-primary)]">10–20+ years</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-muted)]">Est. cost</span><span className="text-[var(--text-primary)]">N/A (analytical)</span></div>
          </div>
        ),
      },
      {
        id: 5,
        title: 'Raw Result',
        status: 'pending',
        content: (
          <div className="space-y-1 font-mono text-[10px]">
            <div className="text-[var(--text-muted)]">Threat assessment data points:</div>
            <div className="text-[var(--text-secondary)] bg-[var(--bg-input)] rounded p-2">
              <div>Shor's on RSA-2048 requires ~4096 logical qubits</div>
              <div>Surface code overhead: ~1000× → 4.1M physical qubits</div>
              <div>With magic state distillation: ~17.6M physical qubits</div>
              <div>Current record: 1,200 qubits (IBM, 2023)</div>
              <div>Grover's speedup: √N → 2¹⁰²⁴ still infeasible</div>
            </div>
          </div>
        ),
      },
      {
        id: 6,
        title: 'Final Answer',
        status: 'pending',
        content: (
          <div className="space-y-2">
            <div className="text-[var(--text-primary)] text-[11px] leading-relaxed">
              <span className="font-semibold text-[var(--accent-error)]">No, RSA-2048 is NOT quantum-safe.</span>{' '}
              Shor's algorithm can break it in polynomial time, but it requires ~4,096 logical qubits and ~17.6M physical qubits — far beyond current technology.
              Timeline estimate: <span className="text-[var(--accent-primary)]">10–20+ years</span> before a cryptographically relevant quantum computer exists.
              <br /><br />
              <span className="font-semibold">Recommendation:</span> Migrate to NIST-approved post-quantum algorithms (CRYSTALS-Kyber, CRYSTALS-Dilithium) now, as "harvest now, decrypt later" attacks are a real threat.
            </div>
            <div className="text-[9px] text-[var(--text-muted)] border-t border-white/5 pt-1">
              Citations: [1] Gidney & Ekerå, Quantum 5, 433 (2021) · [2] NIST SP 800-208 · [3] Mosca, Cybersecurity 2018
            </div>
          </div>
        ),
      },
    ];
  }

  // Default / generic fallback
  return [
    {
      id: 1,
      title: 'Intent Classification',
      status: 'pending',
      content: (
        <div className="space-y-1">
          <div className="flex justify-between"><span className="text-[var(--text-muted)]">Domain</span><span className="text-[var(--accent-primary)]">General Quantum</span></div>
          <div className="flex justify-between"><span className="text-[var(--text-muted)]">Sub-domain</span><span className="text-[var(--text-secondary)]">Unclassified</span></div>
          <div className="flex justify-between"><span className="text-[var(--text-muted)]">Confidence</span><span className="text-[var(--accent-success)]">62.0%</span></div>
        </div>
      ),
    },
    {
      id: 2,
      title: 'Problem Formalization',
      status: 'pending',
      editable: true,
      content: (
        <div className="text-[10px] text-[var(--text-muted)]">
          Unable to automatically formalize. Please refine your query or use an example question above.
        </div>
      ),
    },
    {
      id: 3,
      title: 'Circuit Synthesis',
      status: 'pending',
      editable: true,
      content: (
        <div className="text-[10px] text-[var(--text-muted)]">
          Skipped — problem not formalized.
        </div>
      ),
    },
    {
      id: 4,
      title: 'Execution Plan',
      status: 'pending',
      hasRunButton: true,
      content: (
        <div className="text-[10px] text-[var(--text-muted)]">
          No execution plan available for this query.
        </div>
      ),
    },
    {
      id: 5,
      title: 'Raw Result',
      status: 'pending',
      content: (
        <div className="text-[10px] text-[var(--text-muted)]">
          No results — execution was not performed.
        </div>
      ),
    },
    {
      id: 6,
      title: 'Final Answer',
      status: 'pending',
      content: (
        <div className="space-y-2">
          <div className="text-[var(--text-primary)] text-[11px] leading-relaxed">
            I couldn't fully process that question. Try one of the example queries above, or rephrase using quantum-specific terminology (e.g., "Find the ground state of...", "Factor the integer...", "Optimize...").
          </div>
        </div>
      ),
    },
  ];
}

export default function AskQuantumPanel() {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [activePipeline, setActivePipeline] = useState<PipelineStep[] | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});
  const [runningSteps, setRunningSteps] = useState<Set<number>>(new Set());
  const [executedSteps, setExecutedSteps] = useState<Set<number>>(new Set());
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, activePipeline]);

  const toggleStep = useCallback((id: number) => {
    setExpandedSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  const simulateStep = useCallback((stepId: number) => {
    setRunningSteps((prev) => new Set([...prev, stepId]));
    setTimeout(() => {
      setRunningSteps((prev) => {
        const next = new Set(prev);
        next.delete(stepId);
        return next;
      });
      setExecutedSteps((prev) => new Set([...prev, stepId]));
      setExpandedSteps((prev) => ({ ...prev, [stepId]: true }));
    }, 600 + Math.random() * 400);
  }, []);

  const runStepsFrom = useCallback(
    (startStepId: number) => {
      if (!activePipeline) return;
      const step = activePipeline.find((s) => s.id === startStepId);
      if (!step) return;

      const runChain = (currentId: number) => {
        if (currentId > 6) return;
        simulateStep(currentId);
        setTimeout(() => {
          runChain(currentId + 1);
        }, 800);
      };

      runChain(startStepId);
    },
    [activePipeline, simulateStep],
  );

  const handleSubmit = useCallback(
    (text?: string) => {
      const q = (text || inputValue).trim();
      if (!q) return;

      const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: q };
      setChatHistory((prev) => [...prev, userMsg]);
      setInputValue('');

      const pipeline = generatePipeline(q);
      setActivePipeline(pipeline);
      setExpandedSteps({});
      setRunningSteps(new Set());
      setExecutedSteps(new Set());

      setTimeout(() => {
        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: `Processing: "${q}"`,
        };
        setChatHistory((prev) => [...prev, assistantMsg]);
        pipeline.forEach((step, i) => {
          setTimeout(() => {
            simulateStep(step.id);
          }, 400 + i * 700);
        });
      }, 200);
    },
    [inputValue, simulateStep],
  );

  const copyAnswer = useCallback(() => {
    if (!activePipeline) return;
    const finalStep = activePipeline.find((s) => s.id === 6);
    if (!finalStep) return;
    const el = document.getElementById('aq-final-answer');
    if (el) {
      navigator.clipboard.writeText(el.innerText).catch(() => {});
    }
  }, [activePipeline]);

  const exportReport = useCallback(() => {
    if (!activePipeline) return;
    const lines: string[] = ['=== Ask Quantum Report ===', ''];
    activePipeline.forEach((step) => {
      lines.push(`Step ${step.id}: ${step.title}`);
      lines.push(`Status: ${executedSteps.has(step.id) ? 'Completed' : 'Pending'}`);
      lines.push('');
    });
    lines.push('Generated by AskQuantumPanel · AbirQu');
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ask-quantum-report.txt';
    a.click();
    URL.revokeObjectURL(url);
  }, [activePipeline, executedSteps]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  const allStepsDone = activePipeline && executedSteps.size === 6;

  return (
    <div className="flex flex-col h-full bg-[var(--bg-panel)]">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 bg-[var(--bg-panel)]">
        <span className="text-[var(--accent-primary)] text-sm font-bold">Q</span>
        <span className="text-[11px] font-medium text-[var(--text-primary)]">Ask Quantum</span>
        <span className="text-[9px] text-[var(--text-muted)] bg-[var(--bg-input)] px-1.5 py-0.5 rounded-full">NL2Q</span>
        <div className="flex-1" />
        {activePipeline && (
          <button
            onClick={exportReport}
            className="px-2 py-0.5 rounded text-[9px] font-medium bg-[var(--bg-input)] border border-white/5 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-white/10 transition-all"
          >
            Export Report
          </button>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {chatHistory.length === 0 && !activePipeline && (
          <div className="flex flex-col items-center justify-center h-full animate-fade-in">
            <div className="w-12 h-12 rounded-2xl bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20 flex items-center justify-center mb-3">
              <span className="text-[var(--accent-primary)] text-xl font-bold">Q</span>
            </div>
            <div className="text-[11px] text-[var(--text-primary)] font-medium mb-1">Ask a quantum question</div>
            <div className="text-[9px] text-[var(--text-muted)] text-center max-w-[240px] mb-4">
              Type in natural language and get a full trace pipeline — from intent classification to final answer.
            </div>
            <div className="flex flex-wrap gap-1.5 justify-center max-w-[320px]">
              {EXAMPLE_QUESTIONS.map((eq) => (
                <button
                  key={eq}
                  onClick={() => handleSubmit(eq)}
                  className="px-2.5 py-1 rounded-lg text-[9px] font-medium bg-[var(--bg-input)] border border-white/5 text-[var(--text-secondary)] hover:text-[var(--accent-primary)] hover:border-[var(--accent-primary)]/30 hover:bg-[var(--accent-primary)]/5 transition-all"
                >
                  {eq}
                </button>
              ))}
            </div>
          </div>
        )}

        {chatHistory.map((msg) => (
          <div key={msg.id} className={`flex animate-fade-in ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-xl px-3 py-2 text-[11px] ${
                msg.role === 'user'
                  ? 'bg-[var(--accent-primary)] text-white rounded-br-sm'
                  : 'bg-[var(--bg-input)] text-[var(--text-primary)] border border-white/5 rounded-bl-sm'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {/* Pipeline steps */}
        {activePipeline && (
          <div className="space-y-1.5 animate-fade-in">
            {activePipeline.map((step) => {
              const isExpanded = expandedSteps[step.id] ?? false;
              const isRunning = runningSteps.has(step.id);
              const isDone = executedSteps.has(step.id);
              const showContent = isExpanded || isDone;

              return (
                <div
                  key={step.id}
                  className={`border rounded-xl overflow-hidden transition-all ${
                    isRunning
                      ? 'border-[var(--accent-primary)]/30 bg-[var(--accent-primary)]/5'
                      : isDone
                      ? 'border-white/5 bg-[var(--bg-input)]'
                      : 'border-white/5 bg-[var(--bg-panel)]'
                  }`}
                >
                  <button
                    onClick={() => toggleStep(step.id)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-white/[0.02] transition-colors"
                  >
                    <span
                      className={`w-5 h-5 rounded flex items-center justify-center text-[9px] font-bold ${
                        isRunning
                          ? 'bg-[var(--accent-primary)] text-white animate-pulse'
                          : isDone
                          ? 'bg-[var(--accent-success)] text-white'
                          : 'bg-[var(--bg-input)] text-[var(--text-muted)] border border-white/5'
                      }`}
                    >
                      {isRunning ? '...' : isDone ? '✓' : step.id}
                    </span>
                    <span className={`text-[11px] font-medium ${isDone ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}`}>
                      {step.title}
                    </span>
                    {step.editable && isDone && (
                      <button
                        onClick={(e) => { e.stopPropagation(); }}
                        className="ml-1 px-1.5 py-0.5 rounded text-[8px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-all"
                      >
                        Edit
                      </button>
                    )}
                    {step.hasRunButton && isDone && !allStepsDone && step.id === 4 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          runStepsFrom(5);
                        }}
                        className="ml-1 px-2 py-0.5 rounded text-[8px] font-medium bg-[var(--accent-success)]/10 text-[var(--accent-success)] border border-[var(--accent-success)]/20 hover:bg-[var(--accent-success)]/20 transition-all"
                      >
                        ▶ Run
                      </button>
                    )}
                    <div className="flex-1" />
                    <span className="text-[9px] text-[var(--text-muted)]">{isExpanded ? '▾' : '▸'}</span>
                  </button>

                  {showContent && (
                    <div className="px-3 pb-2.5 animate-fade-in" id={step.id === 6 ? 'aq-final-answer' : undefined}>
                      {isRunning ? (
                        <div className="flex items-center gap-1 py-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)] animate-bounce" style={{ animationDelay: '0ms' }} />
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)] animate-bounce" style={{ animationDelay: '150ms' }} />
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)] animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      ) : (
                        step.content
                      )}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Copy answer button */}
            {allStepsDone && (
              <div className="flex justify-center pt-1 animate-fade-in">
                <button
                  onClick={copyAnswer}
                  className="px-3 py-1 rounded-lg text-[10px] font-medium bg-[var(--bg-input)] border border-white/5 text-[var(--text-muted)] hover:text-[var(--accent-primary)] hover:border-[var(--accent-primary)]/30 transition-all"
                >
                  Copy Answer
                </button>
              </div>
            )}
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-white/5 bg-[var(--bg-panel)] p-2">
        <div className="flex items-center gap-2 bg-[var(--bg-input)] rounded-xl border border-white/5 px-3 py-1.5 focus-within:border-[var(--accent-primary)]/30 transition-colors">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a quantum question..."
            className="flex-1 bg-transparent text-[11px] text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none"
          />
          <button
            onClick={() => handleSubmit()}
            disabled={!inputValue.trim()}
            className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
              inputValue.trim()
                ? 'bg-[var(--accent-primary)] text-white hover:shadow-lg hover:scale-105'
                : 'bg-[var(--bg-input)] text-[var(--text-muted)] border border-white/5'
            }`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
