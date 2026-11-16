import { create } from 'zustand';

export interface WorkspaceFile {
  id: string;
  name: string;
  path: string;
  content: string;
  language: 'python' | 'qasm' | 'json' | 'text';
  isDirty: boolean;
  lastSavedAt?: number;
}

interface WorkspaceState {
  files: WorkspaceFile[];
  activeFileId: string | null;
  commandPaletteOpen: boolean;
  theme: 'dark' | 'light' | 'high-contrast';
  recoveryAvailable: boolean;

  openFile: (file: Omit<WorkspaceFile, 'isDirty'>) => void;
  closeFile: (id: string) => boolean; // returns false if prompt needed
  setActiveFile: (id: string) => void;
  updateFileContent: (id: string, content: string) => void;
  markFileSaved: (id: string, path?: string) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setTheme: (theme: 'dark' | 'light' | 'high-contrast') => void;
  saveRecoverySnapshot: () => void;
  restoreFromRecovery: () => void;
  getActiveFile: () => WorkspaceFile | undefined;
}

const AUTOSAVE_KEY = 'abirqu_studio_recovery_snapshot';

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  files: [
    {
      id: 'default-python',
      name: 'circuit.py',
      path: 'circuit.py',
      language: 'python',
      isDirty: false,
      content: `from abirqu import Circuit, StatevectorSimulator

# 2-qubit Bell State
circuit = Circuit(2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure_all()

sim = StatevectorSimulator()
result = sim.run(circuit, shots=1024)
print("Counts:", result.get_counts())
`,
    },
    {
      id: 'default-qasm',
      name: 'bell.qasm',
      path: 'bell.qasm',
      language: 'qasm',
      isDirty: false,
      content: `OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];

h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
`,
    },
  ],
  activeFileId: 'default-python',
  commandPaletteOpen: false,
  theme: 'dark',
  recoveryAvailable: typeof localStorage !== 'undefined' && !!localStorage.getItem(AUTOSAVE_KEY),

  openFile: (file) => {
    const { files } = get();
    const existing = files.find((f) => f.path === file.path || f.id === file.id);
    if (existing) {
      set({ activeFileId: existing.id });
      return;
    }
    const newFile: WorkspaceFile = { ...file, isDirty: false };
    set({ files: [...files, newFile], activeFileId: newFile.id });
  },

  closeFile: (id: string) => {
    const { files, activeFileId } = get();
    const target = files.find((f) => f.id === id);
    if (target?.isDirty) {
      const confirmClose = window.confirm(`File "${target.name}" has unsaved changes. Close anyway?`);
      if (!confirmClose) return false;
    }
    const remaining = files.filter((f) => f.id !== id);
    let nextActive = activeFileId;
    if (activeFileId === id) {
      nextActive = remaining.length > 0 ? remaining[0].id : null;
    }
    set({ files: remaining, activeFileId: nextActive });
    return true;
  },

  setActiveFile: (id) => set({ activeFileId: id }),

  updateFileContent: (id, content) => {
    const { files } = get();
    const updated = files.map((f) => (f.id === id ? { ...f, content, isDirty: true } : f));
    set({ files: updated });
    get().saveRecoverySnapshot();
  },

  markFileSaved: (id, path) => {
    const { files } = get();
    const updated = files.map((f) =>
      f.id === id ? { ...f, isDirty: false, path: path || f.path, lastSavedAt: Date.now() } : f
    );
    set({ files: updated });
    get().saveRecoverySnapshot();
  },

  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),

  setTheme: (theme) => {
    if (typeof document !== 'undefined') {
      if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
      } else if (theme === 'high-contrast') {
        document.documentElement.setAttribute('data-theme', 'high-contrast');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
    }
    set({ theme });
  },

  saveRecoverySnapshot: () => {
    if (typeof localStorage === 'undefined') return;
    try {
      const snapshot = JSON.stringify(get().files);
      localStorage.setItem(AUTOSAVE_KEY, snapshot);
      set({ recoveryAvailable: true });
    } catch {
      // Ignore storage errors in constrained contexts
    }
  },

  restoreFromRecovery: () => {
    if (typeof localStorage === 'undefined') return;
    try {
      const raw = localStorage.getItem(AUTOSAVE_KEY);
      if (raw) {
        const parsed: WorkspaceFile[] = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          set({ files: parsed, activeFileId: parsed[0].id });
        }
      }
    } catch {
      // Ignore recovery parse errors
    }
  },

  getActiveFile: () => {
    const { files, activeFileId } = get();
    return files.find((f) => f.id === activeFileId);
  },
}));

