import { create } from 'zustand';
import { CircuitData, GateData } from '../api/commands';

interface CircuitState {
  numQubits: number;
  gates: GateData[];
  selectedGate: string | null;
  selectedQubit: number | null;
  hoveredCell: { qubit: number; col: number } | null;

  setNumQubits: (n: number) => void;
  addGate: (name: string, qubit: number, targetQubit?: number, params?: number[]) => void;
  removeGate: (qubit: number, col: number) => void;
  clearCircuit: () => void;
  selectGate: (name: string | null) => void;
  setHoveredCell: (cell: { qubit: number; col: number } | null) => void;
  loadFromTemplate: (circuit: CircuitData) => void;
  getCircuitData: () => CircuitData;
}

export const useCircuitStore = create<CircuitState>((set, get) => ({
  numQubits: 3,
  gates: [],
  selectedGate: null,
  selectedQubit: null,
  hoveredCell: null,

  setNumQubits: (n) => set({ numQubits: Math.max(1, Math.min(20, n)) }),

  addGate: (name, qubit, targetQubit, params) => {
    const { gates, numQubits } = get();
    const q = qubit % numQubits;
    let target = targetQubit !== undefined ? targetQubit % numQubits : undefined;

    // Find next available column for this qubit
    let col = 0;
    const occupiedCols = new Set(
      gates
        .filter((g) => g.qubits.includes(q) || (target !== undefined && g.qubits.includes(target)))
        .map((g) => {
          // Estimate column from index
          return gates.indexOf(g);
        })
    );
    while (occupiedCols.has(col)) col++;

    const gate: GateData = { name, qubits: target !== undefined ? [q, target] : [q] };
    if (params) gate.params = params;

    set({ gates: [...gates, gate] });
  },

  removeGate: (_qubit, col) => {
    const { gates } = get();
    // Remove gate at approximate position
    const idx = col;
    if (idx >= 0 && idx < gates.length) {
      const newGates = [...gates];
      newGates.splice(idx, 1);
      set({ gates: newGates });
    }
  },

  clearCircuit: () => set({ gates: [], selectedGate: null }),

  selectGate: (name) => set({ selectedGate: name }),

  setHoveredCell: (cell) => set({ hoveredCell: cell }),

  loadFromTemplate: (circuit) =>
    set({ numQubits: circuit.num_qubits, gates: circuit.gates }),

  getCircuitData: () => {
    const { numQubits, gates } = get();
    return { num_qubits: numQubits, gates };
  },
}));
