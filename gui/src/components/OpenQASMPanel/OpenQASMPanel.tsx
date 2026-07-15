import React, { useCallback, useRef, useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { useCircuitStore } from '../../stores/circuitStore';
import { api } from '../../api/commands';

const QASM_TEMPLATE = `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];

h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];`;

export default function OpenQASMPanel() {
  const editorRef = useRef<any>(null);
  const [qasmCode, setQasmCode] = useState(QASM_TEMPLATE);
  const [converting, setConverting] = useState(false);
  const { loadFromTemplate, getCircuitData } = useCircuitStore();

  const parseQasmToCircuit = useCallback(() => {
    const code = qasmCode;
    const qubitsMatch = code.match(/qreg\s+q\[(\d+)\]/);
    const numQubits = qubitsMatch ? parseInt(qubitsMatch[1]) : 2;
    const gates: any[] = [];

    const lines = code.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('h ')) {
        const m = trimmed.match(/h\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'H', qubits: [parseInt(m[1])] });
      } else if (trimmed.startsWith('x ')) {
        const m = trimmed.match(/x\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'X', qubits: [parseInt(m[1])] });
      } else if (trimmed.startsWith('y ')) {
        const m = trimmed.match(/y\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'Y', qubits: [parseInt(m[1])] });
      } else if (trimmed.startsWith('z ')) {
        const m = trimmed.match(/z\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'Z', qubits: [parseInt(m[1])] });
      } else if (trimmed.startsWith('s ')) {
        const m = trimmed.match(/s\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'S', qubits: [parseInt(m[1])] });
      } else if (trimmed.startsWith('t ')) {
        const m = trimmed.match(/t\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'T', qubits: [parseInt(m[1])] });
      } else if (trimmed.startsWith('cx ')) {
        const m = trimmed.match(/cx\s+q\[(\d+)\],\s*q\[(\d+)\]/);
        if (m) gates.push({ name: 'CNOT', qubits: [parseInt(m[1]), parseInt(m[2])] });
      } else if (trimmed.startsWith('cz ')) {
        const m = trimmed.match(/cz\s+q\[(\d+)\],\s*q\[(\d+)\]/);
        if (m) gates.push({ name: 'CZ', qubits: [parseInt(m[1]), parseInt(m[2])] });
      } else if (trimmed.startsWith('swap ')) {
        const m = trimmed.match(/swap\s+q\[(\d+)\],\s*q\[(\d+)\]/);
        if (m) gates.push({ name: 'SWAP', qubits: [parseInt(m[1]), parseInt(m[2])] });
      } else if (trimmed.startsWith('ccx ')) {
        const m = trimmed.match(/ccx\s+q\[(\d+)\],\s*q\[(\d+)\],\s*q\[(\d+)\]/);
        if (m) gates.push({ name: 'Toffoli', qubits: [parseInt(m[1]), parseInt(m[2]), parseInt(m[3])] });
      } else if (trimmed.startsWith('rx(')) {
        const m = trimmed.match(/rx\(([\d.]+)\)\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'Rx', qubits: [parseInt(m[2])], params: [parseFloat(m[1])] });
      } else if (trimmed.startsWith('ry(')) {
        const m = trimmed.match(/ry\(([\d.]+)\)\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'Ry', qubits: [parseInt(m[2])], params: [parseFloat(m[1])] });
      } else if (trimmed.startsWith('rz(')) {
        const m = trimmed.match(/rz\(([\d.]+)\)\s+q\[(\d+)\]/);
        if (m) gates.push({ name: 'Rz', qubits: [parseInt(m[2])], params: [parseFloat(m[1])] });
      }
    }
    if (gates.length > 0) {
      loadFromTemplate({ num_qubits: numQubits, gates });
    }
  }, [qasmCode, loadFromTemplate]);

  const handleConvertToQasm = useCallback(async () => {
    setConverting(true);
    try {
      const circuit = getCircuitData();
      const result = await api.convertCircuit(circuit, 'openqasm');
      if (result?.code) {
        setQasmCode(result.code);
      } else if (result?.content) {
        setQasmCode(result.content);
      }
    } catch {}
    setConverting(false);
  }, [getCircuitData]);

  const handleMount = useCallback((_editor: any, monaco: any) => {
    editorRef.current = _editor;
    monaco.languages.register({ id: 'openqasm' });
    monaco.languages.setMonarchTokensProvider('openqasm', {
      keywords: ['OPENQASM', 'include', 'qreg', 'creg', 'measure', 'barrier', 'reset', 'if', 'else'],
      gateKeywords: ['h', 'x', 'y', 'z', 's', 't', 'sdg', 'tdg', 'rx', 'ry', 'rz', 'cx', 'cz', 'swap', 'ccx', 'u3', 'u2', 'u1', 'id', 'u'],
      tokenizer: {
        root: [
          [/#.*$/, 'comment'],
          [/"[^"]*"/, 'string'],
          [/\d+(\.\d+)?/, 'number'],
          [/[a-zA-Z_]\w*(?=\s*\()/, 'function'],
          [/[A-Z][a-zA-Z0-9_]*/, 'type'],
          [/[a-z][a-z0-9_]*/, { cases: { '@gateKeywords': 'keyword', '@keywords': 'keyword', '@default': 'variable' } }],
          [/[+\-*\/=<>!&|^~@\[\];,.]/, 'operator'],
        ],
      },
    });
    monaco.editor.defineTheme('qasm-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '4a5568', fontStyle: 'italic' },
        { token: 'keyword', foreground: 'f472b6' },
        { token: 'number', foreground: '34d399' },
        { token: 'type', foreground: '60a5fa' },
        { token: 'function', foreground: 'c084fc' },
      ],
      colors: {
        'editor.background': '#0a0a18',
        'editor.foreground': '#e2e8f0',
        'editorCursor.foreground': '#8b5cf6',
      },
    });
    monaco.editor.setTheme('qasm-dark');
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-[var(--border)] bg-[var(--bg-panel)]">
        <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">OpenQASM 2.0</span>
        <div className="flex-1" />
        <button
          onClick={handleConvertToQasm}
          disabled={converting}
          className="px-3 py-1 rounded-lg text-[11px] font-medium bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/30 transition-all disabled:opacity-50"
        >
          ← Import from Circuit
        </button>
        <button
          onClick={parseQasmToCircuit}
          className="px-3 py-1 rounded-lg text-[11px] font-medium bg-[var(--accent-primary)]/20 text-[var(--accent-primary)] border border-[var(--accent-primary)]/30 hover:bg-[var(--accent-primary)]/30 transition-all"
        >
          Parse to Circuit →
        </button>
      </div>
      <div className="flex-1">
        <Editor
          language="openqasm"
          value={qasmCode}
          onChange={(v) => setQasmCode(v || '')}
          onMount={handleMount}
          theme="qasm-dark"
          options={{
            fontSize: 13,
            fontFamily: '"SF Mono", "Fira Code", monospace',
            fontLigatures: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
            roundedSelection: true,
            padding: { top: 12, bottom: 12 },
            wordWrap: 'on',
            automaticLayout: true,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
          }}
        />
      </div>
    </div>
  );
}
