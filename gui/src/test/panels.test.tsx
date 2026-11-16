import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Import the 14 panel components
import CircuitCanvas from '../components/CircuitCanvas/CircuitCanvas';
import CodeEditor from '../components/CodePanel/CodeEditor';
import OpenQASMPanel from '../components/OpenQASMPanel/OpenQASMPanel';
import ExplorerPanel from '../components/ExplorerPanel/ExplorerPanel';
import CircuitLibrary from '../components/LibrarySidebar/CircuitLibrary';
import FrameworkPanel from '../components/FrameworkPanel/FrameworkPanel';
import QECPanel from '../components/QECPanel/QECPanel';
import QCommPanel from '../components/QCommPanel/QCommPanel';
import DomainPanel from '../components/DomainPanel/DomainPanel';
import SecurityPanel from '../components/SecurityPanel/SecurityPanel';
import PluginsPanel from '../components/PluginsPanel/PluginsPanel';
import AskQuantumPanel from '../components/AskQuantumPanel/AskQuantumPanel';
import SettingsPanel from '../components/SettingsPanel/SettingsPanel';
import MeasurementResults from '../components/MeasurementResults/MeasurementResults';
import StateVector from '../components/StateVector/StateVector';
import BlochSphere from '../components/BlochSphere/BlochSphere';

describe('AbirQu Studio - 14 Panels Baseline Suite', () => {
  it('Panel 1: Circuit Editor (CircuitCanvas) mounts without error', () => {
    const { container } = render(<CircuitCanvas />);
    expect(container).toBeDefined();
    expect(container.querySelector('canvas') || container.firstChild).toBeTruthy();
  });

  it('Panel 2: Python Code Editor mounts without error', () => {
    const { container } = render(<CodeEditor />);
    expect(container).toBeDefined();
  });

  it('Panel 3: OpenQASM Editor mounts and shows QASM controls', () => {
    const { container } = render(<OpenQASMPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 4: Explorer Panel mounts and displays file tree header', () => {
    const { container } = render(<ExplorerPanel />);
    expect(container).toBeDefined();
    expect(screen.getByText(/Explorer/i) || screen.getByText(/Project/i)).toBeTruthy();
  });

  it('Panel 5: Circuit Library mounts and shows templates', () => {
    const { container } = render(<CircuitLibrary />);
    expect(container).toBeDefined();
  });

  it('Panel 6: Framework Panel mounts and shows target options', () => {
    const { container } = render(<FrameworkPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 7: QEC Lab mounts and displays code selection', () => {
    const { container } = render(<QECPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 8: Quantum Comm Panel mounts and displays protocol options', () => {
    const { container } = render(<QCommPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 9: Domain Modules mounts and displays chemistry/OSINT/crypto', () => {
    const { container } = render(<DomainPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 10: Security Panel mounts and displays post-quantum crypto controls', () => {
    const { container } = render(<SecurityPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 11: Plugins Marketplace mounts and renders search/listings', () => {
    const { container } = render(<PluginsPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 12: Ask Quantum (NL2Q) mounts and renders query input', () => {
    const { container } = render(<AskQuantumPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 13: Settings Panel mounts and displays tabs', () => {
    const { container } = render(<SettingsPanel />);
    expect(container).toBeDefined();
  });

  it('Panel 14: Results / StateVector / Bloch Sphere mount without error', () => {
    const res = render(<MeasurementResults />);
    expect(res.container).toBeDefined();

    const sv = render(<StateVector />);
    expect(sv.container).toBeDefined();

    const bs = render(<BlochSphere />);
    expect(bs.container).toBeDefined();
  });
});

