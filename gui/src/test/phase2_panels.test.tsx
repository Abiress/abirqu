import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RunPanel, { SIMULATOR_ENGINES } from '../components/RunPanel/RunPanel';
import StepDebugger from '../components/Debugger/StepDebugger';
import NoisePanel from '../components/NoisePanel/NoisePanel';
import { useCircuitStore } from '../stores/circuitStore';
import { useHardwareStore } from '../stores/hardwareStore';

describe('Phase 2 Panels Suite (Real Backend Responses)', () => {
  it('Feature 1: RunPanel renders simulator choices and displays qubit limits', () => {
    render(<RunPanel />);

    expect(screen.getByText(/Simulation Engine/i)).toBeInTheDocument();
    expect(screen.getByText('NumPy Statevector')).toBeInTheDocument();
    expect(screen.getByText('Clifford Tableau')).toBeInTheDocument();
    expect(screen.getByText('MPS Tensor Network')).toBeInTheDocument();

    // Check qubit limit tags
    expect(screen.getByText('Limit: ≤28q')).toBeInTheDocument();
    expect(screen.getByText('Limit: ≤1000q')).toBeInTheDocument();
    expect(screen.getByText('Limit: ≤100q')).toBeInTheDocument();
  });

  it('Feature 1: RunPanel warns and refuses execution when circuit exceeds engine limit', () => {
    // Set 30 qubits
    useCircuitStore.getState().setNumQubits(30);
    render(<RunPanel />);

    // Qubit limit warning banner
    expect(screen.getByText(/Qubit Limit Exceeded/i)).toBeInTheDocument();
    expect(screen.getByText(/exceeding NumPy Statevector's limit of/i)).toBeInTheDocument();

    // Run button is disabled
    const runBtn = screen.getByRole('button', { name: /Run on NumPy Statevector/i });
    expect(runBtn).toBeDisabled();

    // Reset back to 2 qubits
    useCircuitStore.getState().setNumQubits(2);
  });

  it('Feature 2: StepDebugger renders amplitude table, phase-colored bars, and entanglement metrics', async () => {
    // Setup 2-qubit Bell circuit
    useCircuitStore.getState().setNumQubits(2);
    useCircuitStore.getState().loadFromTemplate({
      num_qubits: 2,
      gates: [
        { name: 'H', qubits: [0] },
        { name: 'CNOT', qubits: [0, 1] },
      ],
    });

    render(<StepDebugger />);

    // Check Step counter and controls
    expect(screen.getByText(/Statevector Amplitudes & Phase/i)).toBeInTheDocument();
    expect(screen.getByText(/Per-Qubit Reduced States & Bloch Vectors/i)).toBeInTheDocument();

    await waitFor(() => {
      // Check Bell state basis elements |00⟩ and |11⟩
      expect(screen.getByText('|00⟩')).toBeInTheDocument();
      expect(screen.getByText('|11⟩')).toBeInTheDocument();
    });

    // Check analytic amplitude alpha = +0.7071
    expect(screen.getAllByText(/α = \+0\.7071/i).length).toBeGreaterThan(0);

    // Check entanglement metrics
    expect(screen.getAllByText(/Purity: 50.0%/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Entanglement: 100.0%/i).length).toBeGreaterThan(0);
  });

  it('Feature 3: NoisePanel displays Total Variation Distance and calibration metrics', async () => {
    useHardwareStore.getState().setNoiseConfig({
      enabled: true,
      depolarizing: 0.05,
      amplitudeDamping: 0.01,
      phaseDamping: 0.01,
      readoutError: 0.02,
    });

    render(<NoisePanel />);

    await waitFor(() => {
      expect(screen.getByText(/Total Variation Distance/i)).toBeInTheDocument();
      expect(screen.getByText(/TVD = 0.0950/i)).toBeInTheDocument();
    });

    // Check calibration metrics
    expect(screen.getByText(/F_gate/i)).toBeInTheDocument();
    expect(screen.getByText(/F_readout/i)).toBeInTheDocument();
    expect(screen.getByText(/Ideal vs Noisy Probabilities/i)).toBeInTheDocument();
  });
});
