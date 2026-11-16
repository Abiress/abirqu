import React, { useState, useEffect, useRef } from 'react';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import { useCircuitStore } from '../../stores/circuitStore';

interface CommandItem {
  id: string;
  title: string;
  category: string;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  onSelectTab?: (tab: string) => void;
  onRun?: () => void;
}

export default function CommandPalette({ onSelectTab, onRun }: CommandPaletteProps) {
  const { commandPaletteOpen, setCommandPaletteOpen, setTheme, theme, restoreFromRecovery } = useWorkspaceStore();
  const { clearCircuit, loadFromTemplate } = useCircuitStore();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: CommandItem[] = [
    {
      id: 'cmd-run',
      title: 'Quantum: Execute Simulation on Active Circuit',
      category: 'Run',
      shortcut: 'Ctrl+Enter',
      action: () => {
        onRun?.();
      },
    },
    {
      id: 'cmd-clear',
      title: 'Circuit: Clear All Gates and Reset Register',
      category: 'Circuit',
      action: () => clearCircuit(),
    },
    {
      id: 'cmd-bell',
      title: 'Insert Template: 2-Qubit Bell State (|00> + |11>)',
      category: 'Templates',
      action: () => {
        loadFromTemplate({
          num_qubits: 2,
          gates: [
            { name: 'H', qubits: [0] },
            { name: 'CNOT', qubits: [0, 1] },
          ],
        });
      },
    },
    {
      id: 'cmd-ghz',
      title: 'Insert Template: 3-Qubit GHZ State (|000> + |111>)',
      category: 'Templates',
      action: () => {
        loadFromTemplate({
          num_qubits: 3,
          gates: [
            { name: 'H', qubits: [0] },
            { name: 'CNOT', qubits: [0, 1] },
            { name: 'CNOT', qubits: [1, 2] },
          ],
        });
      },
    },
    {
      id: 'cmd-view-canvas',
      title: 'View: Open Circuit Canvas Editor',
      category: 'Navigation',
      action: () => onSelectTab?.('circuit'),
    },
    {
      id: 'cmd-view-code',
      title: 'View: Open Python Monaco Editor',
      category: 'Navigation',
      action: () => onSelectTab?.('code'),
    },
    {
      id: 'cmd-view-qasm',
      title: 'View: Open OpenQASM 2/3 Editor',
      category: 'Navigation',
      action: () => onSelectTab?.('qasm'),
    },
    {
      id: 'cmd-theme-dark',
      title: 'Preferences: Switch to Quantum Dark Theme',
      category: 'Appearance',
      action: () => setTheme('dark'),
    },
    {
      id: 'cmd-theme-light',
      title: 'Preferences: Switch to Light Theme',
      category: 'Appearance',
      action: () => setTheme('light'),
    },
    {
      id: 'cmd-theme-contrast',
      title: 'Preferences: Switch to High-Contrast Accessible Theme',
      category: 'Appearance',
      action: () => setTheme('high-contrast'),
    },
    {
      id: 'cmd-restore-recovery',
      title: 'Workspace: Restore Unsaved Recovery Snapshot',
      category: 'Workspace',
      action: () => restoreFromRecovery(),
    },
  ];

  const filtered = commands.filter((c) =>
    `${c.category} ${c.title}`.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'P' || e.key === 'p')) {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      } else if (e.key === 'Escape' && commandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [commandPaletteOpen]);

  const handleSelect = (idx: number) => {
    if (filtered[idx]) {
      filtered[idx].action();
      setCommandPaletteOpen(false);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      handleSelect(selectedIndex);
    }
  };

  if (!commandPaletteOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-black/60 backdrop-blur-sm"
      onClick={() => setCommandPaletteOpen(false)}
    >
      <div
        className="w-full max-w-xl bg-[var(--bg-panel)] border border-[var(--border)] rounded-xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-input)]">
          <span className="text-sm text-[var(--accent-primary)] mr-2">⌘</span>
          <input
            ref={inputRef}
            type="text"
            className="w-full bg-transparent outline-none text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)]"
            placeholder="Type a command or search actions... (e.g. run, theme, bell)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleInputKeyDown}
          />
          <kbd className="text-[10px] bg-[var(--bg-panel)] border border-[var(--border)] px-1.5 py-0.5 rounded text-[var(--text-muted)]">
            ESC
          </kbd>
        </div>

        <div className="max-h-80 overflow-y-auto p-1 divide-y divide-[var(--border)]/30">
          {filtered.length === 0 ? (
            <div className="p-4 text-center text-xs text-[var(--text-muted)]">No matching commands found.</div>
          ) : (
            filtered.map((cmd, idx) => (
              <div
                key={cmd.id}
                onClick={() => handleSelect(idx)}
                className={`flex items-center justify-between px-3 py-2 text-xs rounded-lg cursor-pointer transition-colors ${
                  idx === selectedIndex
                    ? 'bg-[var(--accent-primary)]/20 text-[var(--accent-primary)] font-medium'
                    : 'text-[var(--text-primary)] hover:bg-[var(--bg-input)]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold text-[var(--text-muted)] tracking-wider">
                    {cmd.category}
                  </span>
                  <span>{cmd.title}</span>
                </div>
                {cmd.shortcut && (
                  <kbd className="text-[10px] bg-[var(--bg-panel)] border border-[var(--border)] px-1.5 py-0.5 rounded text-[var(--text-muted)]">
                    {cmd.shortcut}
                  </kbd>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

