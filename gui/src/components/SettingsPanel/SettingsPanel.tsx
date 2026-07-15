import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../api/commands';

type Tab = 'general' | 'simulation' | 'hardware' | 'appearance' | 'about';
type SimulationEngine = 'numpy' | 'gpu' | 'clifford' | 'mps' | 'montecarlo';
type ThemeOption = 'dark' | 'light' | 'system';
type AccentColor = 'blue' | 'green' | 'purple' | 'amber' | 'rose';

interface GeneralSettings {
  defaultShots: number;
  defaultBackend: string;
  autoSave: boolean;
  projectDirectory: string;
}

interface SimulationSettings {
  engine: SimulationEngine;
  maxQubits: number;
  threadCount: number;
  memoryLimit: string;
}

interface HardwareSettings {
  ibmToken: string;
  awsAccessKey: string;
  awsSecretKey: string;
  awsRegion: string;
  azureResourceId: string;
  ionqApiKey: string;
  connectionStatus: Record<string, 'idle' | 'testing' | 'connected' | 'error'>;
}

interface AppearanceSettings {
  theme: ThemeOption;
  fontSize: number;
  accentColor: AccentColor;
  showGrid: boolean;
}

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: 'general', label: 'General', icon: '⚙' },
  { key: 'simulation', label: 'Simulation', icon: '⚡' },
  { key: 'hardware', label: 'Hardware', icon: '🔌' },
  { key: 'appearance', label: 'Appearance', icon: '🎨' },
  { key: 'about', label: 'About', icon: 'ℹ' },
];

const ENGINES: { key: SimulationEngine; label: string; desc: string }[] = [
  { key: 'numpy', label: 'NumPy', desc: 'CPU-based state vector simulation' },
  { key: 'gpu', label: 'GPU', desc: 'CUDA-accelerated simulation' },
  { key: 'clifford', label: 'Clifford', desc: 'Stabilizer-based Clifford simulation' },
  { key: 'mps', label: 'MPS', desc: 'Matrix Product State for low-entanglement circuits' },
  { key: 'montecarlo', label: 'Monte Carlo', desc: 'Shot-based density matrix sampling' },
];

const ACCENT_COLORS: { key: AccentColor; label: string; value: string }[] = [
  { key: 'blue', label: 'Blue', value: '#3b82f6' },
  { key: 'green', label: 'Green', value: '#22c55e' },
  { key: 'purple', label: 'Purple', value: '#8b5cf6' },
  { key: 'amber', label: 'Amber', value: '#f59e0b' },
  { key: 'rose', label: 'Rose', value: '#f43f5e' },
];

const THEMES: { key: ThemeOption; label: string; desc: string }[] = [
  { key: 'dark', label: 'Dark', desc: 'Dark theme for reduced eye strain' },
  { key: 'light', label: 'Light', desc: 'Light theme for bright environments' },
  { key: 'system', label: 'System', desc: 'Follow operating system preference' },
];

const STORAGE_KEY = 'abirqu-settings';

function loadSettings<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const all = JSON.parse(raw);
      if (key in all) return all[key] as T;
    }
  } catch {}
  return fallback;
}

function saveSettings(key: string, value: unknown) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const all = raw ? JSON.parse(raw) : {};
    all[key] = value;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
  } catch {}
}

export default function SettingsPanel() {
  const [activeTab, setActiveTab] = useState<Tab>('general');

  const [general, setGeneral] = useState<GeneralSettings>(() =>
    loadSettings('general', {
      defaultShots: 1024,
      defaultBackend: 'local_simulator',
      autoSave: true,
      projectDirectory: '~/abirqu-projects',
    })
  );

  const [simulation, setSimulation] = useState<SimulationSettings>(() =>
    loadSettings('simulation', {
      engine: 'numpy',
      maxQubits: 30,
      threadCount: 4,
      memoryLimit: '4096',
    })
  );

  const [hardware, setHardware] = useState<HardwareSettings>(() =>
    loadSettings('hardware', {
      ibmToken: '',
      awsAccessKey: '',
      awsSecretKey: '',
      awsRegion: 'us-east-1',
      azureResourceId: '',
      ionqApiKey: '',
      connectionStatus: {},
    })
  );

  const [appearance, setAppearance] = useState<AppearanceSettings>(() =>
    loadSettings('appearance', {
      theme: 'dark',
      fontSize: 13,
      accentColor: 'purple',
      showGrid: true,
    })
  );

  useEffect(() => { saveSettings('general', general); }, [general]);
  useEffect(() => { saveSettings('simulation', simulation); }, [simulation]);
  useEffect(() => { saveSettings('hardware', hardware); }, [hardware]);
  useEffect(() => { saveSettings('appearance', appearance); }, [appearance]);

  useEffect(() => {
    const root = document.documentElement;
    if (appearance.theme === 'dark') {
      root.removeAttribute('data-theme');
    } else if (appearance.theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.removeAttribute('data-theme');
      if (!prefersDark) root.setAttribute('data-theme', 'light');
    }
  }, [appearance.theme]);

  const updateGeneral = useCallback((patch: Partial<GeneralSettings>) => {
    setGeneral((prev) => ({ ...prev, ...patch }));
  }, []);

  const updateSimulation = useCallback((patch: Partial<SimulationSettings>) => {
    setSimulation((prev) => ({ ...prev, ...patch }));
  }, []);

  const updateHardware = useCallback((patch: Partial<HardwareSettings>) => {
    setHardware((prev) => ({ ...prev, ...patch }));
  }, []);

  const updateAppearance = useCallback((patch: Partial<AppearanceSettings>) => {
    setAppearance((prev) => ({ ...prev, ...patch }));
  }, []);

  const testConnection = useCallback(async (provider: string) => {
    updateHardware({ connectionStatus: { ...hardware.connectionStatus, [provider]: 'testing' } });
    try {
      const backends = await api.listHardware();
      const providerLower = provider.toLowerCase();
      const found = backends.some(
        (b) => b.provider.toLowerCase().includes(providerLower) || b.name.toLowerCase().includes(providerLower)
      );
      updateHardware({
        connectionStatus: {
          ...hardware.connectionStatus,
          [provider]: found ? 'connected' : 'error',
        },
      });
    } catch {
      updateHardware({
        connectionStatus: {
          ...hardware.connectionStatus,
          [provider]: 'error',
        },
      });
    }
  }, [hardware, updateHardware]);

  const resetAllSettings = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setGeneral({
      defaultShots: 1024,
      defaultBackend: 'local_simulator',
      autoSave: true,
      projectDirectory: '~/abirqu-projects',
    });
    setSimulation({
      engine: 'numpy',
      maxQubits: 30,
      threadCount: 4,
      memoryLimit: '4096',
    });
    setHardware({
      ibmToken: '',
      awsAccessKey: '',
      awsSecretKey: '',
      awsRegion: 'us-east-1',
      azureResourceId: '',
      ionqApiKey: '',
      connectionStatus: {},
    });
    setAppearance({
      theme: 'dark',
      fontSize: 13,
      accentColor: 'purple',
      showGrid: true,
    });
  }, []);

  return (
    <div className="flex flex-col h-full animate-fade-in">
      {/* Tab bar */}
      <div className="flex border-b border-white/5 bg-[var(--bg-panel)]">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-3 py-2 text-[11px] font-medium transition-all border-b-2 ${
              activeTab === tab.key
                ? 'border-[var(--accent-primary)] text-[var(--accent-primary)] bg-[var(--accent-primary)]/5'
                : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
            }`}
          >
            <span className="text-xs">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {activeTab === 'general' && (
          <GeneralTab settings={general} onUpdate={updateGeneral} />
        )}
        {activeTab === 'simulation' && (
          <SimulationTab settings={simulation} onUpdate={updateSimulation} />
        )}
        {activeTab === 'hardware' && (
          <HardwareTab settings={hardware} onUpdate={updateHardware} onTest={testConnection} />
        )}
        {activeTab === 'appearance' && (
          <AppearanceTab settings={appearance} onUpdate={updateAppearance} />
        )}
        {activeTab === 'about' && (
          <AboutTab onReset={resetAllSettings} />
        )}
      </div>
    </div>
  );
}

function GeneralTab({
  settings,
  onUpdate,
}: {
  settings: GeneralSettings;
  onUpdate: (patch: Partial<GeneralSettings>) => void;
}) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Default shots */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-medium text-[var(--text-primary)]">Default Shots</label>
          <span className="text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-input)] px-2 py-0.5 rounded">
            {settings.defaultShots}
          </span>
        </div>
        <input
          type="range"
          min={64}
          max={8192}
          step={64}
          value={settings.defaultShots}
          onChange={(e) => onUpdate({ defaultShots: parseInt(e.target.value, 10) })}
          className="w-full h-1 accent-[var(--accent-primary)]"
        />
        <div className="flex justify-between text-[9px] text-[var(--text-muted)]">
          <span>64</span>
          <span>8192</span>
        </div>
      </div>

      {/* Default backend */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-[var(--text-primary)]">Default Backend</label>
        <select
          value={settings.defaultBackend}
          onChange={(e) => onUpdate({ defaultBackend: e.target.value })}
          className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-[var(--text-primary)] text-[11px] outline-none focus:border-[var(--accent-primary)] transition-colors"
        >
          <option value="local_simulator">Local Simulator (AbirQu)</option>
          <option value="qiskit_aer">Qiskit Aer</option>
          <option value="cirq_sim">Cirq Simulator</option>
          <option value="ibm_brisbane">IBM Quantum — Brisbane</option>
          <option value="ibm_osaka">IBM Quantum — Osaka</option>
          <option value="ionq_harmony">IonQ Harmony</option>
          <option value="aws_braket">AWS Braket</option>
          <option value="azure_quantum">Azure Quantum</option>
        </select>
      </div>

      {/* Auto-save toggle */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] font-medium text-[var(--text-primary)]">Auto-Save</div>
            <div className="text-[9px] text-[var(--text-muted)]">Automatically save circuit changes</div>
          </div>
          <button
            onClick={() => onUpdate({ autoSave: !settings.autoSave })}
            className={`relative w-10 h-5 rounded-full transition-colors ${
              settings.autoSave ? 'bg-[var(--accent-primary)]' : 'bg-[var(--bg-input)]'
            }`}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                settings.autoSave ? 'translate-x-5' : 'translate-x-0.5'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Project directory */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-[var(--text-primary)]">Project Directory</label>
        <div className="flex items-center gap-2">
          <div className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-[10px] font-mono text-[var(--text-secondary)] truncate">
            {settings.projectDirectory}
          </div>
          <button className="px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-[10px] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-white/10 transition-all">
            Browse
          </button>
        </div>
      </div>
    </div>
  );
}

function SimulationTab({
  settings,
  onUpdate,
}: {
  settings: SimulationSettings;
  onUpdate: (patch: Partial<SimulationSettings>) => void;
}) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Engine selector */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-[var(--text-primary)]">Simulation Engine</label>
        <div className="grid grid-cols-1 gap-1.5">
          {ENGINES.map((eng) => (
            <button
              key={eng.key}
              onClick={() => onUpdate({ engine: eng.key })}
              className={`w-full flex items-center gap-3 p-2.5 rounded-lg text-left transition-all ${
                settings.engine === eng.key
                  ? 'bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 shadow-sm'
                  : 'bg-[var(--bg-input)] border border-white/5 hover:bg-white/[0.03]'
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full transition-colors ${
                  settings.engine === eng.key ? 'bg-[var(--accent-primary)]' : 'bg-[var(--text-muted)]'
                }`}
              />
              <div>
                <div className="text-[11px] font-medium text-[var(--text-primary)]">{eng.label}</div>
                <div className="text-[9px] text-[var(--text-muted)]">{eng.desc}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Max qubits */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-medium text-[var(--text-primary)]">Max Qubits</label>
          <span className="text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-input)] px-2 py-0.5 rounded">
            {settings.maxQubits}
          </span>
        </div>
        <input
          type="range"
          min={4}
          max={40}
          step={1}
          value={settings.maxQubits}
          onChange={(e) => onUpdate({ maxQubits: parseInt(e.target.value, 10) })}
          className="w-full h-1 accent-[var(--accent-primary)]"
        />
        <div className="flex justify-between text-[9px] text-[var(--text-muted)]">
          <span>4</span>
          <span>40</span>
        </div>
      </div>

      {/* Thread count */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-medium text-[var(--text-primary)]">Thread Count</label>
          <span className="text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-input)] px-2 py-0.5 rounded">
            {settings.threadCount}
          </span>
        </div>
        <input
          type="range"
          min={1}
          max={16}
          step={1}
          value={settings.threadCount}
          onChange={(e) => onUpdate({ threadCount: parseInt(e.target.value, 10) })}
          className="w-full h-1 accent-[var(--accent-primary)]"
        />
        <div className="flex justify-between text-[9px] text-[var(--text-muted)]">
          <span>1</span>
          <span>16</span>
        </div>
      </div>

      {/* Memory limit */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-[var(--text-primary)]">Memory Limit (MB)</label>
        <input
          type="number"
          min={256}
          max={65536}
          step={256}
          value={settings.memoryLimit}
          onChange={(e) => onUpdate({ memoryLimit: e.target.value })}
          className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-[11px] text-[var(--text-primary)] outline-none focus:border-[var(--accent-primary)] transition-colors font-mono"
        />
        <div className="text-[9px] text-[var(--text-muted)]">
          Recommended: 4096 MB for circuits up to 20 qubits
        </div>
      </div>
    </div>
  );
}

function HardwareTab({
  settings,
  onUpdate,
  onTest,
}: {
  settings: HardwareSettings;
  onUpdate: (patch: Partial<HardwareSettings>) => void;
  onTest: (provider: string) => void;
}) {
  const [showIbmToken, setShowIbmToken] = useState(false);
  const [showAwsSecret, setShowAwsSecret] = useState(false);
  const [showIonqKey, setShowIonqKey] = useState(false);

  const providers = [
    {
      id: 'IBM Quantum',
      fields: [
        {
          label: 'IBM Quantum Token',
          value: settings.ibmToken,
          onChange: (v: string) => onUpdate({ ibmToken: v }),
          show: showIbmToken,
          toggleShow: () => setShowIbmToken(!showIbmToken),
          isPassword: true,
          placeholder: 'IBM Quantum API token',
        },
      ],
    },
    {
      id: 'AWS',
      fields: [
        {
          label: 'Access Key ID',
          value: settings.awsAccessKey,
          onChange: (v: string) => onUpdate({ awsAccessKey: v }),
          isPassword: false,
          placeholder: 'AKIA...',
        },
        {
          label: 'Secret Access Key',
          value: settings.awsSecretKey,
          onChange: (v: string) => onUpdate({ awsSecretKey: v }),
          show: showAwsSecret,
          toggleShow: () => setShowAwsSecret(!showAwsSecret),
          isPassword: true,
          placeholder: 'AWS secret access key',
        },
        {
          label: 'Region',
          value: settings.awsRegion,
          onChange: (v: string) => onUpdate({ awsRegion: v }),
          isPassword: false,
          placeholder: 'us-east-1',
        },
      ],
    },
    {
      id: 'Azure Quantum',
      fields: [
        {
          label: 'Resource ID',
          value: settings.azureResourceId,
          onChange: (v: string) => onUpdate({ azureResourceId: v }),
          isPassword: false,
          placeholder: '/subscriptions/.../resourceGroups/.../providers/Microsoft.Quantum/Workspaces/...',
        },
      ],
    },
    {
      id: 'IonQ',
      fields: [
        {
          label: 'API Key',
          value: settings.ionqApiKey,
          onChange: (v: string) => onUpdate({ ionqApiKey: v }),
          show: showIonqKey,
          toggleShow: () => setShowIonqKey(!showIonqKey),
          isPassword: true,
          placeholder: 'IonQ API key',
        },
      ],
    },
  ];

  return (
    <div className="space-y-5 animate-fade-in">
      {providers.map((provider) => {
        const status = settings.connectionStatus[provider.id] || 'idle';
        return (
          <div key={provider.id} className="space-y-3">
            {/* Provider header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold text-[var(--text-primary)]">{provider.id}</span>
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    status === 'connected'
                      ? 'bg-[var(--accent-success)]'
                      : status === 'testing'
                      ? 'bg-[var(--accent-warning)] animate-pulse'
                      : status === 'error'
                      ? 'bg-[var(--accent-error)]'
                      : 'bg-[var(--text-muted)]'
                  }`}
                />
                <span className="text-[9px] text-[var(--text-muted)] capitalize">
                  {status === 'idle' ? 'Not configured' : status}
                </span>
              </div>
            </div>

            {/* Fields */}
            {provider.fields.map((field) => (
              <div key={field.label} className="space-y-1">
                <label className="text-[10px] text-[var(--text-muted)]">{field.label}</label>
                <div className="relative">
                  <input
                    type={field.isPassword && !field.show ? 'password' : 'text'}
                    value={field.value}
                    onChange={(e) => field.onChange(e.target.value)}
                    placeholder={field.placeholder}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-[11px] text-[var(--text-primary)] outline-none focus:border-[var(--accent-primary)] transition-colors font-mono"
                  />
                  {field.isPassword && field.toggleShow && (
                    <button
                      onClick={field.toggleShow}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                    >
                      {field.show ? 'Hide' : 'Show'}
                    </button>
                  )}
                </div>
              </div>
            ))}

            {/* Test connection button */}
            <button
              onClick={() => onTest(provider.id)}
              disabled={status === 'testing'}
              className={`w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-medium border transition-all ${
                status === 'testing'
                  ? 'border-[var(--accent-warning)]/30 bg-[var(--accent-warning)]/5 text-[var(--accent-warning)] cursor-wait'
                  : status === 'connected'
                  ? 'border-[var(--accent-success)]/30 bg-[var(--accent-success)]/5 text-[var(--accent-success)]'
                  : 'border-white/5 bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-white/10'
              }`}
            >
              {status === 'testing' ? (
                <>
                  <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  Testing Connection...
                </>
              ) : status === 'connected' ? (
                <>Connected</>
              ) : (
                'Test Connection'
              )}
            </button>

            {/* Divider */}
            <div className="border-b border-white/5 pt-2" />
          </div>
        );
      })}
    </div>
  );
}

function AppearanceTab({
  settings,
  onUpdate,
}: {
  settings: AppearanceSettings;
  onUpdate: (patch: Partial<AppearanceSettings>) => void;
}) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* Theme selector */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-[var(--text-primary)]">Theme</label>
        <div className="grid grid-cols-3 gap-1.5">
          {THEMES.map((t) => (
            <button
              key={t.key}
              onClick={() => onUpdate({ theme: t.key })}
              className={`flex flex-col items-center gap-1 p-2.5 rounded-lg text-center transition-all ${
                settings.theme === t.key
                  ? 'bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 shadow-sm'
                  : 'bg-[var(--bg-input)] border border-white/5 hover:bg-white/[0.03]'
              }`}
            >
              <span
                className={`w-6 h-6 rounded-full border-2 transition-colors ${
                  settings.theme === t.key
                    ? 'border-[var(--accent-primary)] bg-[var(--accent-primary)]/20'
                    : 'border-white/10 bg-[var(--bg-primary)]'
                }`}
              />
              <span className="text-[10px] font-medium text-[var(--text-primary)]">{t.label}</span>
              <span className="text-[9px] text-[var(--text-muted)] leading-tight">{t.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Font size */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-[11px] font-medium text-[var(--text-primary)]">Font Size</label>
          <span className="text-[10px] font-mono text-[var(--text-secondary)] bg-[var(--bg-input)] px-2 py-0.5 rounded">
            {settings.fontSize}px
          </span>
        </div>
        <input
          type="range"
          min={10}
          max={18}
          step={1}
          value={settings.fontSize}
          onChange={(e) => onUpdate({ fontSize: parseInt(e.target.value, 10) })}
          className="w-full h-1 accent-[var(--accent-primary)]"
        />
        <div className="flex justify-between text-[9px] text-[var(--text-muted)]">
          <span>10px</span>
          <span>18px</span>
        </div>
      </div>

      {/* Accent color picker */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-[var(--text-primary)]">Accent Color</label>
        <div className="flex gap-2">
          {ACCENT_COLORS.map((c) => (
            <button
              key={c.key}
              onClick={() => onUpdate({ accentColor: c.key })}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-all ${
                settings.accentColor === c.key
                  ? 'bg-white/5 ring-2 ring-white/20'
                  : 'hover:bg-white/[0.03]'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full transition-transform ${
                  settings.accentColor === c.key ? 'scale-110' : ''
                }`}
                style={{ backgroundColor: c.value }}
              />
              <span className="text-[9px] text-[var(--text-muted)]">{c.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Circuit canvas grid toggle */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] font-medium text-[var(--text-primary)]">Circuit Canvas Grid</div>
            <div className="text-[9px] text-[var(--text-muted)]">Show alignment grid on the circuit canvas</div>
          </div>
          <button
            onClick={() => onUpdate({ showGrid: !settings.showGrid })}
            className={`relative w-10 h-5 rounded-full transition-colors ${
              settings.showGrid ? 'bg-[var(--accent-primary)]' : 'bg-[var(--bg-input)]'
            }`}
          >
            <div
              className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
                settings.showGrid ? 'translate-x-5' : 'translate-x-0.5'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Preview */}
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-[var(--text-primary)]">Preview</label>
        <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-white/5 space-y-2">
          <div className="text-[11px] text-[var(--text-primary)]" style={{ fontSize: settings.fontSize }}>
            Sample text at {settings.fontSize}px
          </div>
          <div className="text-[10px] text-[var(--text-secondary)]" style={{ fontSize: settings.fontSize - 1 }}>
            Secondary text for comparison
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: ACCENT_COLORS.find((c) => c.key === settings.accentColor)?.value }} />
            <span className="text-[9px] text-[var(--text-muted)]">Accent color preview</span>
          </div>
          {settings.showGrid && (
            <div className="h-12 rounded border border-white/5 bg-[var(--bg-primary)]" style={{ backgroundImage: 'linear-gradient(rgba(148,163,184,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.05) 1px, transparent 1px)', backgroundSize: '10px 10px' }} />
          )}
        </div>
      </div>
    </div>
  );
}

function AboutTab({ onReset }: { onReset: () => void }) {
  return (
    <div className="space-y-5 animate-fade-in">
      {/* App info */}
      <div className="text-center py-4">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20 mb-3">
          <span className="text-2xl font-black text-[var(--accent-primary)]">Q</span>
        </div>
        <div className="text-sm font-bold text-[var(--text-primary)]">AbirQu</div>
        <div className="text-[10px] text-[var(--text-muted)] mt-0.5">Quantum Computing IDE</div>
      </div>

      {/* Version info */}
      <div className="bg-[var(--bg-input)] rounded-lg border border-white/5 divide-y divide-white/5">
        <div className="flex items-center justify-between px-3 py-2">
          <span className="text-[11px] text-[var(--text-muted)]">Version</span>
          <span className="text-[11px] font-mono text-[var(--text-secondary)]">1.2.3</span>
        </div>
        <div className="flex items-center justify-between px-3 py-2">
          <span className="text-[11px] text-[var(--text-muted)]">Build Date</span>
          <span className="text-[11px] font-mono text-[var(--text-secondary)]">2026-07-10</span>
        </div>
        <div className="flex items-center justify-between px-3 py-2">
          <span className="text-[11px] text-[var(--text-muted)]">License</span>
          <span className="text-[11px] font-mono text-[var(--accent-primary)]">MIT</span>
        </div>
        <div className="flex items-center justify-between px-3 py-2">
          <span className="text-[11px] text-[var(--text-muted)]">Platform</span>
          <span className="text-[11px] font-mono text-[var(--text-secondary)]">Desktop</span>
        </div>
      </div>

      {/* Links */}
      <div className="space-y-1">
        <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold px-1 mb-1">
          Links
        </div>
        {[
          { label: 'GitHub Repository', href: 'https://github.com/abirqu/abirqu' },
          { label: 'Documentation', href: 'https://docs.abirqu.dev' },
          { label: 'Report Issue', href: 'https://github.com/abirqu/abirqu/issues' },
        ].map((link) => (
          <a
            key={link.label}
            href={link.href}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-[11px] text-[var(--text-secondary)] hover:text-[var(--accent-primary)] hover:border-[var(--accent-primary)]/20 transition-all"
          >
            <span>{link.label}</span>
            <span className="text-[9px] text-[var(--text-muted)]">↗</span>
          </a>
        ))}
      </div>

      {/* Credits */}
      <div className="text-center py-3 space-y-1">
        <div className="text-[11px] text-[var(--text-secondary)] font-medium">
          Built by Abir Maheshwari
        </div>
        <div className="text-[9px] text-[var(--text-muted)]">
          Powered by the OpenCode agentic platform
        </div>
      </div>

      {/* Reset */}
      <div className="pt-2 border-t border-white/5">
        <button
          onClick={() => {
            if (window.confirm('Reset all settings to defaults? This cannot be undone.')) {
              onReset();
            }
          }}
          className="w-full px-3 py-2 rounded-lg text-[11px] font-medium text-[var(--accent-error)] bg-[var(--accent-error)]/5 border border-[var(--accent-error)]/20 hover:bg-[var(--accent-error)]/10 transition-all"
        >
          Reset All Settings
        </button>
      </div>
    </div>
  );
}
