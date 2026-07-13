import React, { useState, useMemo, useEffect } from 'react';
import { runPluginList } from '../../api/commands';

type PluginStatus = 'installed' | 'available' | 'update';

interface Plugin {
  id: string;
  name: string;
  icon: string;
  description: string;
  fullDescription: string;
  author: string;
  version: string;
  status: PluginStatus;
  rating: number;
  downloads: number;
  tags: string[];
  configFields: ConfigField[];
  enabled: boolean;
}

interface ConfigField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'toggle';
  value: string | boolean;
  placeholder?: string;
}

type Tab = 'marketplace' | 'installed';

const INITIAL_PLUGINS: Plugin[] = [
  {
    id: 'abirqu-chemistry',
    name: 'AbirQu Chemistry',
    icon: '⚗',
    description: 'Molecular simulation tools for quantum chemistry',
    fullDescription: 'Full suite of quantum chemistry simulation tools. Supports molecular orbital calculations, bond dissociation energies, and potential energy surface mapping. Includes built-in basis sets (STO-3G, 6-31G*, cc-pVDZ) and integration with OpenFermion for fermion-to-qubit mappings.',
    author: 'AbirQu Team',
    version: '1.2.0',
    status: 'installed',
    rating: 4.7,
    downloads: 12400,
    tags: ['chemistry', 'simulation', 'molecular'],
    configFields: [
      { key: 'max_atoms', label: 'Max Atoms', type: 'number', value: '20', placeholder: '20' },
      { key: 'basis_set', label: 'Default Basis Set', type: 'text', value: 'sto-3g', placeholder: 'sto-3g' },
      { key: 'auto_optimize', label: 'Auto Optimize', type: 'toggle', value: true },
    ],
    enabled: true,
  },
  {
    id: 'abirqu-osint',
    name: 'AbirQu OSINT',
    icon: '🔍',
    description: 'Intelligence analysis with quantum-enhanced pattern matching',
    fullDescription: 'Quantum-enhanced Open Source Intelligence toolkit. Uses Grover search for rapid database lookups, quantum annealing for network analysis, and amplitude amplification for anomaly detection. Ideal for cybersecurity research and threat intelligence.',
    author: 'AbirQu Team',
    version: '1.1.0',
    status: 'installed',
    rating: 4.3,
    downloads: 8200,
    tags: ['intelligence', 'security', 'analysis'],
    configFields: [
      { key: 'search_depth', label: 'Search Depth', type: 'number', value: '5', placeholder: '5' },
      { key: 'use_quantum_search', label: 'Quantum Search', type: 'toggle', value: true },
    ],
    enabled: true,
  },
  {
    id: 'qiskit-backend',
    name: 'Qiskit Backend',
    icon: 'Q',
    description: 'IBM Qiskit integration for real quantum hardware',
    fullDescription: 'Full integration with IBM Quantum backends via Qiskit Runtime. Supports pulse-level control, dynamic circuits, and error mitigation primitives. Connect to IBM Quantum Network devices or run on Aer simulators. Requires IBM Quantum API token.',
    author: 'IBM Quantum',
    version: '0.45.0',
    status: 'available',
    rating: 4.8,
    downloads: 45600,
    tags: ['ibm', 'hardware', 'cloud'],
    configFields: [
      { key: 'api_token', label: 'IBM API Token', type: 'text', value: '', placeholder: 'Paste your IBM Quantum token' },
      { key: 'default_backend', label: 'Default Backend', type: 'text', value: 'ibm_brisbane', placeholder: 'ibm_brisbane' },
    ],
    enabled: false,
  },
  {
    id: 'cirq-backend',
    name: 'Cirq Backend',
    icon: 'C',
    description: 'Google Cirq integration for Sycamore-class processors',
    fullDescription: 'Integration with Google Quantum AI hardware via Cirq. Supports Sycamore and beyond, including Floquet calibration and noise-adaptive compilation. Direct access to Google Quantum Cloud for circuit execution.',
    author: 'Google Quantum AI',
    version: '1.3.0',
    status: 'available',
    rating: 4.5,
    downloads: 23100,
    tags: ['google', 'hardware', 'sycamore'],
    configFields: [
      { key: 'project_id', label: 'Google Cloud Project ID', type: 'text', value: '', placeholder: 'your-gcp-project-id' },
      { key: 'processor', label: 'Processor', type: 'text', value: 'Rainbow', placeholder: 'Rainbow' },
    ],
    enabled: false,
  },
  {
    id: 'dwave-sampler',
    name: 'D-Wave Sampler',
    icon: 'D',
    description: 'D-Wave quantum annealing for optimization problems',
    fullDescription: 'Direct access to D-Wave quantum annealers. Solve QUBO, Ising model, and constrained optimization problems. Includes hybrid classical-quantum solvers for problems up to 1 million variables. Supports embedding visualization and chain strength analysis.',
    author: 'D-Wave Systems',
    version: '2.0.0',
    status: 'update',
    rating: 4.6,
    downloads: 18900,
    tags: ['annealing', 'optimization', 'quantum'],
    configFields: [
      { key: 'api_key', label: 'D-Wave API Key', type: 'text', value: 'dwave_key_***', placeholder: 'Paste your D-Wave token' },
      { key: 'solver', label: 'Solver', type: 'text', value: 'Advantage_system6.4', placeholder: 'Advantage_system6.4' },
      { key: 'chain_strength', label: 'Chain Strength', type: 'number', value: '1.0', placeholder: '1.0' },
    ],
    enabled: true,
  },
  {
    id: 'error-mitigation-pro',
    name: 'Error Mitigation Pro',
    icon: '🛡',
    description: 'Advanced error mitigation for NISQ circuits',
    fullDescription: 'Production-grade error mitigation suite. Includes zero-noise extrapolation, probabilistic error cancellation, Clifford data regression, and measurement error mitigation. Reduces effective error rates by 2-10x on noisy hardware.',
    author: 'Quantum Research Labs',
    version: '1.0.0',
    status: 'available',
    rating: 4.4,
    downloads: 9700,
    tags: ['mitigation', 'noise', 'nisq'],
    configFields: [
      { key: 'method', label: 'Method', type: 'text', value: 'zne', placeholder: 'zne, pec, cdr' },
      { key: 'noise_levels', label: 'Noise Levels', type: 'text', value: '1.0,1.5,2.0,2.5', placeholder: 'comma-separated' },
      { key: 'auto_apply', label: 'Auto Apply', type: 'toggle', value: true },
    ],
    enabled: false,
  },
];

function Stars({ rating, size = 'text-[10px]' }: { rating: number; size?: string }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return (
    <span className={`${size} text-amber-400 tracking-tight`}>
      {'★'.repeat(full)}
      {half && '½'}
      {'☆'.repeat(empty)}
      <span className="text-[var(--text-muted)] ml-1">{rating.toFixed(1)}</span>
    </span>
  );
}

function StatusBadge({ status }: { status: PluginStatus }) {
  if (status === 'installed') {
    return (
      <span className="px-1.5 py-0.5 rounded-full text-[9px] font-medium text-emerald-400 bg-emerald-400/10 border border-emerald-500/20">
        Installed
      </span>
    );
  }
  if (status === 'update') {
    return (
      <span className="px-1.5 py-0.5 rounded-full text-[9px] font-medium text-amber-400 bg-amber-400/10 border border-amber-500/20">
        Update
      </span>
    );
  }
  return (
    <span className="px-1.5 py-0.5 rounded-full text-[9px] font-medium text-[var(--text-muted)] bg-[var(--bg-input)] border border-white/5">
      Available
    </span>
  );
}

function PluginCard({
  plugin,
  onSelect,
  onToggleInstall,
}: {
  plugin: Plugin;
  onSelect: (p: Plugin) => void;
  onToggleInstall: (p: Plugin) => void;
}) {
  return (
    <button
      onClick={() => onSelect(plugin)}
      className="w-full text-left p-2.5 rounded-xl border border-white/5 hover:bg-white/[0.03] hover:border-white/10 transition-all animate-fade-in"
    >
      <div className="flex items-start gap-2.5">
        <span className="w-9 h-9 rounded-lg bg-[var(--bg-input)] border border-white/5 flex items-center justify-center text-base flex-shrink-0">
          {plugin.icon}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold text-[var(--text-primary)] truncate">{plugin.name}</span>
            <StatusBadge status={plugin.status} />
          </div>
          <div className="text-[10px] text-[var(--text-muted)] mt-0.5 line-clamp-2">{plugin.description}</div>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-[9px] text-[var(--text-muted)]">{plugin.author}</span>
            <span className="text-[9px] text-[var(--text-muted)]">·</span>
            <span className="text-[9px] text-[var(--text-secondary)] font-mono">v{plugin.version}</span>
          </div>
          <div className="flex items-center gap-3 mt-1">
            <Stars rating={plugin.rating} />
            <span className="text-[9px] text-[var(--text-muted)]">{(plugin.downloads / 1000).toFixed(1)}k downloads</span>
          </div>
        </div>
        <div className="flex-shrink-0">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleInstall(plugin);
            }}
            className={`px-3 py-1 rounded-lg text-[10px] font-semibold transition-all ${
              plugin.status === 'installed'
                ? 'text-red-400 bg-red-400/10 border border-red-500/20 hover:bg-red-400/20'
                : plugin.status === 'update'
                ? 'text-amber-400 bg-amber-400/10 border border-amber-500/20 hover:bg-amber-400/20'
                : 'text-white bg-[var(--accent-primary)] hover:shadow-lg hover:shadow-[var(--accent-primary)]/20'
            }`}
          >
            {plugin.status === 'installed' ? 'Uninstall' : plugin.status === 'update' ? 'Update' : 'Install'}
          </button>
        </div>
      </div>
    </button>
  );
}

function PluginDetail({
  plugin,
  onBack,
  onToggleInstall,
  onToggleEnabled,
  onConfigChange,
}: {
  plugin: Plugin;
  onBack: () => void;
  onToggleInstall: (p: Plugin) => void;
  onToggleEnabled: (id: string) => void;
  onConfigChange: (id: string, key: string, value: string | boolean) => void;
}) {
  return (
    <div className="flex flex-col h-full animate-fade-in">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5">
        <button
          onClick={onBack}
          className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors text-sm"
        >
          ← Back
        </button>
        <span className="flex-1" />
        <StatusBadge status={plugin.status} />
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        <div className="flex items-center gap-3">
          <span className="w-12 h-12 rounded-xl bg-[var(--bg-input)] border border-white/5 flex items-center justify-center text-xl flex-shrink-0">
            {plugin.icon}
          </span>
          <div>
            <div className="text-xs font-bold text-[var(--text-primary)]">{plugin.name}</div>
            <div className="text-[10px] text-[var(--text-muted)]">{plugin.author} · v{plugin.version}</div>
            <div className="mt-0.5"><Stars rating={plugin.rating} /></div>
          </div>
        </div>

        <div className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
          {plugin.fullDescription}
        </div>

        <div className="flex flex-wrap gap-1">
          {plugin.tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 rounded-full text-[9px] font-medium bg-[var(--bg-input)] border border-white/5 text-[var(--text-muted)]"
            >
              {tag}
            </span>
          ))}
        </div>

        {plugin.status === 'installed' && (
          <div className="space-y-2 border-t border-white/5 pt-3">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
              Configuration
            </div>

            <label className="flex items-center justify-between py-1.5">
              <span className="text-[11px] text-[var(--text-secondary)]">Enabled</span>
              <div
                onClick={() => onToggleEnabled(plugin.id)}
                className={`w-8 h-4 rounded-full transition-colors relative cursor-pointer ${
                  plugin.enabled ? 'bg-[var(--accent-success)]' : 'bg-[var(--bg-input)]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
                    plugin.enabled ? 'translate-x-4' : 'translate-x-0.5'
                  }`}
                />
              </div>
            </label>

            {plugin.configFields.map((field) => (
              <div key={field.key} className="space-y-1">
                <label className="text-[10px] text-[var(--text-muted)]">{field.label}</label>
                {field.type === 'toggle' ? (
                  <div className="flex items-center justify-between py-1">
                    <span className="text-[10px] text-[var(--text-secondary)]">{field.label}</span>
                    <div
                      onClick={() => onConfigChange(plugin.id, field.key, !field.value)}
                      className={`w-8 h-4 rounded-full transition-colors relative cursor-pointer ${
                        field.value ? 'bg-[var(--accent-primary)]' : 'bg-[var(--bg-input)]'
                      }`}
                    >
                      <div
                        className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
                          field.value ? 'translate-x-4' : 'translate-x-0.5'
                        }`}
                      />
                    </div>
                  </div>
                ) : (
                  <input
                    type={field.type}
                    value={String(field.value)}
                    placeholder={field.placeholder}
                    onChange={(e) => onConfigChange(plugin.id, field.key, field.type === 'number' ? e.target.value : e.target.value)}
                    className="w-full px-2 py-1.5 rounded-lg text-[11px] bg-[var(--bg-input)] border border-white/5 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none focus:border-[var(--accent-primary)]/50 transition-colors font-mono"
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="px-3 py-2 border-t border-white/5">
        <button
          onClick={() => onToggleInstall(plugin)}
          className={`w-full py-2 rounded-xl text-[11px] font-semibold transition-all ${
            plugin.status === 'installed'
              ? 'text-red-400 bg-red-400/10 border border-red-500/20 hover:bg-red-400/20'
              : plugin.status === 'update'
              ? 'text-amber-400 bg-amber-400/10 border border-amber-500/20 hover:bg-amber-400/20'
              : 'text-white bg-[var(--accent-primary)] hover:shadow-lg hover:shadow-[var(--accent-primary)]/20'
          }`}
        >
          {plugin.status === 'installed' ? 'Uninstall Plugin' : plugin.status === 'update' ? 'Update Plugin' : 'Install Plugin'}
        </button>
      </div>
    </div>
  );
}

export default function PluginsPanel() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('marketplace');
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await runPluginList();
        if (cancelled) return;
        const installed: Plugin[] = (resp.installed || []).map((p: any, i: number) => ({
          id: p.name || `installed-${i}`,
          name: p.name || 'Unknown',
          icon: '📦',
          description: p.description || 'Installed plugin',
          fullDescription: p.description || 'Installed plugin',
          author: 'AbirQu',
          version: p.version || '1.0.0',
          status: 'installed' as PluginStatus,
          rating: 0,
          downloads: 0,
          tags: p.tags || [],
          configFields: [],
          enabled: true,
        }));
        const marketplace: Plugin[] = (resp.marketplace || []).map((p: any, i: number) => ({
          id: p.name || `market-${i}`,
          name: p.name || 'Unknown',
          icon: '📦',
          description: p.description || '',
          fullDescription: p.description || '',
          author: 'Community',
          version: p.version || '1.0.0',
          status: p.installed ? 'installed' as PluginStatus : 'available' as PluginStatus,
          rating: 0,
          downloads: p.downloads || 0,
          tags: p.tags || [],
          configFields: [],
          enabled: false,
        }));
        // Merge: installed plugins that aren't in marketplace get added
        const marketplaceNames = new Set(marketplace.map(p => p.name));
        const extraInstalled = installed.filter(p => !marketplaceNames.has(p.name));
        setPlugins([...extraInstalled, ...marketplace]);
      } catch {
        if (!cancelled) setPlugins([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    let list = plugins;
    if (activeTab === 'installed') {
      list = list.filter((p) => p.status === 'installed');
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.author.toLowerCase().includes(q) ||
          p.tags.some((t) => t.includes(q))
      );
    }
    return list;
  }, [plugins, activeTab, search]);

  const installedCount = plugins.filter((p) => p.status === 'installed').length;
  const availableCount = plugins.filter((p) => p.status !== 'installed').length;

  const handleToggleInstall = (plugin: Plugin) => {
    setPlugins((prev) =>
      prev.map((p) => {
        if (p.id !== plugin.id) return p;
        if (p.status === 'installed') {
          return { ...p, status: 'available' as PluginStatus, enabled: false };
        }
        return { ...p, status: 'installed' as PluginStatus };
      })
    );
    if (selectedPlugin?.id === plugin.id) {
      setSelectedPlugin((prev) => {
        if (!prev) return null;
        if (prev.status === 'installed') {
          return { ...prev, status: 'available', enabled: false };
        }
        return { ...prev, status: 'installed' };
      });
    }
  };

  const handleToggleEnabled = (id: string) => {
    setPlugins((prev) =>
      prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p))
    );
    setSelectedPlugin((prev) => {
      if (!prev || prev.id !== id) return prev;
      return { ...prev, enabled: !prev.enabled };
    });
  };

  const handleConfigChange = (id: string, key: string, value: string | boolean) => {
    setPlugins((prev) =>
      prev.map((p) => {
        if (p.id !== id) return p;
        return {
          ...p,
          configFields: p.configFields.map((f) =>
            f.key === key ? { ...f, value } : f
          ),
        };
      })
    );
    setSelectedPlugin((prev) => {
      if (!prev || prev.id !== id) return prev;
      return {
        ...prev,
        configFields: prev.configFields.map((f) =>
          f.key === key ? { ...f, value } : f
        ),
      };
    });
  };

  if (selectedPlugin) {
    return (
      <div className="flex flex-col h-full">
        <PluginDetail
          plugin={selectedPlugin}
          onBack={() => setSelectedPlugin(null)}
          onToggleInstall={handleToggleInstall}
          onToggleEnabled={handleToggleEnabled}
          onConfigChange={handleConfigChange}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-2 border-b border-white/5">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search plugins..."
          className="w-full px-2.5 py-1.5 rounded-lg text-[11px] bg-[var(--bg-input)] border border-white/5 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none focus:border-[var(--accent-primary)]/50 transition-colors"
        />
      </div>

      <div className="flex border-b border-white/5 bg-[var(--bg-panel)]">
        <button
          onClick={() => setActiveTab('marketplace')}
          className={`flex-1 px-3 py-2 text-[11px] font-medium transition-all border-b-2 ${
            activeTab === 'marketplace'
              ? 'border-[var(--accent-primary)] text-[var(--text-primary)] bg-[var(--accent-primary)]/5'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
          }`}
        >
          Marketplace
          <span className="ml-1 text-[9px] text-[var(--text-muted)]">({availableCount})</span>
        </button>
        <button
          onClick={() => setActiveTab('installed')}
          className={`flex-1 px-3 py-2 text-[11px] font-medium transition-all border-b-2 ${
            activeTab === 'installed'
              ? 'border-[var(--accent-success)] text-[var(--text-primary)] bg-[var(--accent-success)]/5'
              : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
          }`}
        >
          Installed
          <span className="ml-1 text-[9px] text-[var(--text-muted)]">({installedCount})</span>
        </button>
      </div>

      <div className="flex-1 overflow-auto p-2 space-y-1.5">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)]">
            <span className="w-4 h-4 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mb-2" />
            <span className="text-[11px]">Loading plugins...</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)]">
            <span className="text-2xl mb-2 opacity-30">📦</span>
            <span className="text-[11px]">
              {activeTab === 'installed' ? 'No plugins installed' : 'No plugins found'}
            </span>
            <span className="text-[10px] opacity-50 mt-0.5">
              {search ? 'Try a different search term' : 'No plugins available'}
            </span>
          </div>
        ) : (
          filtered.map((plugin) => (
            <PluginCard
              key={plugin.id}
              plugin={plugin}
              onSelect={setSelectedPlugin}
              onToggleInstall={handleToggleInstall}
            />
          ))
        )}
      </div>
    </div>
  );
}
