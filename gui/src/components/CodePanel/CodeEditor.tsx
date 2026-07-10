import React, { useCallback, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { useCircuitStore } from '../../stores/circuitStore';

const TEMPLATE = `from abirqu import Circuit

# Create a quantum circuit
c = Circuit(2)

# Add gates
c.h(0)          # Hadamard on qubit 0
c.cx(0, 1)      # CNOT: control=0, target=1

# Measure
c.measure_all()

# Execute
result = c.run(shots=1024)
print(result.counts)
`;

const THEME = {
  base: 'vs-dark' as const,
  inherit: true,
  rules: [
    { token: 'comment', foreground: '4a5568', fontStyle: 'italic' },
    { token: 'string', foreground: 'a78bfa' },
    { token: 'keyword', foreground: 'f472b6' },
    { token: 'number', foreground: '34d399' },
    { token: 'type', foreground: '60a5fa' },
    { token: 'function', foreground: 'c084fc' },
    { token: 'variable', foreground: 'fbbf24' },
    { token: 'operator', foreground: '94a3b8' },
  ],
  colors: {
    'editor.background': '#0a0a18',
    'editor.foreground': '#e2e8f0',
    'editor.lineHighlightBackground': '#1a1a3520',
    'editor.selectionBackground': '#8b5cf640',
    'editorCursor.foreground': '#8b5cf6',
    'editorWidget.background': '#141428',
    'editorSuggestWidget.background': '#141428',
    'editorSuggestWidget.selectedBackground': '#1a1a35',
    'editorLineNumber.foreground': '#334155',
    'editorLineNumber.activeForeground': '#8b5cf6',
  },
};

export default function CodePanel() {
  const editorRef = useRef<any>(null);
  const { loadFromTemplate } = useCircuitStore();

  const handleMount = useCallback((_editor: any, monaco: any) => {
    editorRef.current = _editor;

    monaco.languages.register({ id: 'quantum-python' });
    monaco.languages.setMonarchTokensProvider('quantum-python', {
      keywords: ['def', 'class', 'return', 'if', 'else', 'elif', 'for', 'while', 'import', 'from', 'as', 'with', 'try', 'except', 'finally', 'raise', 'pass', 'break', 'continue', 'yield', 'lambda', 'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is'],
      gateKeywords: ['h', 'cx', 'cy', 'cz', 'ccx', 'x', 'y', 'z', 's', 't', 'rx', 'ry', 'rz', 'swap', 'measure', 'measure_all', 'barrier', 'reset', 'run', 'counts', 'statevector'],
      tokenizer: {
        root: [
          [/#.*$/, 'comment'],
          [/"[^"]*"/, 'string'],
          [/'[^']*'/, 'string'],
          [/\d+(\.\d+)?/, 'number'],
          [/[a-zA-Z_]\w*(?=\s*\()/, 'function'],
          [/[A-Z][a-zA-Z0-9_]*/, 'type'],
          [/[a-z][a-z0-9_]*/, { cases: { '@gateKeywords': 'keyword', '@keywords': 'keyword', '@default': 'variable' } }],
          [/[+\-*\/=<>!&|^~@]/, 'operator'],
        ],
      },
    });

    monaco.editor.defineTheme('quantum-dark', THEME);
    monaco.editor.setTheme('quantum-dark');
  }, []);

  const handleParse = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const code = editor.getValue();

    const qubitMatch = code.match(/Circuit\((\d+)\)/);
    const numQubits = qubitMatch ? parseInt(qubitMatch[1]) : 2;
    const gates: any[] = [];
    const patterns = [
      { regex: /\.h\((\d+)\)/g, name: 'H' },
      { regex: /\.x\((\d+)\)/g, name: 'X' },
      { regex: /\.y\((\d+)\)/g, name: 'Y' },
      { regex: /\.z\((\d+)\)/g, name: 'Z' },
      { regex: /\.s\((\d+)\)/g, name: 'S' },
      { regex: /\.t\((\d+)\)/g, name: 'T' },
      { regex: /\.cx\((\d+),\s*(\d+)\)/g, name: 'CNOT' },
      { regex: /\.cz\((\d+),\s*(\d+)\)/g, name: 'CZ' },
      { regex: /\.swap\((\d+),\s*(\d+)\)/g, name: 'SWAP' },
      { regex: /\.rx\((\d+),\s*([\d.]+)\)/g, name: 'Rx' },
      { regex: /\.ry\((\d+),\s*([\d.]+)\)/g, name: 'Ry' },
      { regex: /\.rz\((\d+),\s*([\d.]+)\)/g, name: 'Rz' },
    ];

    for (const p of patterns) {
      let m;
      while ((m = p.regex.exec(code)) !== null) {
        const qubits = [parseInt(m[1])];
        if (m[2] !== undefined) qubits.push(parseInt(m[2]));
        const gate: any = { name: p.name, qubits };
        if (m[3]) gate.params = [parseFloat(m[3])];
        gates.push(gate);
      }
    }

    if (gates.length > 0) {
      loadFromTemplate({ num_qubits: numQubits, gates });
    }
  }, [loadFromTemplate]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-white/5 bg-[var(--bg-panel)]">
        <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">Python</span>
        <div className="flex-1" />
        <button
          onClick={handleParse}
          className="px-3 py-1 rounded-lg text-[11px] font-medium bg-[var(--accent-primary)]/20 text-[var(--accent-primary)] border border-[var(--accent-primary)]/30 hover:bg-[var(--accent-primary)]/30 transition-all"
        >
          ⚡ Parse to Circuit
        </button>
      </div>
      <div className="flex-1">
        <Editor
          defaultLanguage="quantum-python"
          defaultValue={TEMPLATE}
          theme="quantum-dark"
          onMount={handleMount}
          options={{
            fontSize: 13,
            fontFamily: '"SF Mono", "Fira Code", "Cascadia Code", monospace',
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
            smoothScrolling: true,
            renderLineHighlight: 'all',
          }}
        />
      </div>
    </div>
  );
}
