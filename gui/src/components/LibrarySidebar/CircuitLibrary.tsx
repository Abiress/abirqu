import React, { useEffect, useState } from 'react';
import { useCircuitStore } from '../../stores/circuitStore';
import { api, CircuitTemplate } from '../../api/commands';

const DIFF_COLORS: Record<string, string> = {
  beginner: 'text-[var(--accent-success)] bg-[var(--accent-success)]/10',
  intermediate: 'text-[var(--accent-warning)] bg-[var(--accent-warning)]/10',
  advanced: 'text-[var(--accent-error)] bg-[var(--accent-error)]/10',
};

interface Props {
  serverReady?: boolean;
}

export default function LibrarySidebar({ serverReady = false }: Props) {
  const [templates, setTemplates] = useState<CircuitTemplate[]>([]);
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { loadFromTemplate } = useCircuitStore();

  useEffect(() => {
    if (!serverReady) return;
    let cancelled = false;
    const load = async () => {
      for (let i = 0; i < 5; i++) {
        try {
          const data = await api.listLibraryCircuits();
          if (!cancelled) {
            setTemplates(data);
            setLoading(false);
          }
          return;
        } catch {
          await new Promise((r) => setTimeout(r, 800));
        }
      }
      if (!cancelled) setLoading(false);
    };
    load();
    return () => { cancelled = true; };
  }, [serverReady]);

  const categories = [...new Set(templates.map((t) => t.category))];

  const filtered = templates.filter((t) => {
    if (selectedCat && t.category !== selectedCat) return false;
    if (search) {
      const q = search.toLowerCase();
      return t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q) ||
        t.tags.some((tag) => tag.toLowerCase().includes(q));
    }
    return true;
  });

  const handleLoad = async (t: CircuitTemplate) => {
    try {
      const circuit = await api.loadCircuitFromLibrary(t.template_id);
      loadFromTemplate(circuit);
    } catch {
      loadFromTemplate({ num_qubits: t.num_qubits, gates: t.gates });
    }
  };

  if (!serverReady) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[var(--text-muted)] p-4">
        <span className="text-2xl mb-2 opacity-30">📚</span>
        <span className="text-[11px] font-medium text-[var(--text-secondary)] mb-1">Server not connected</span>
        <span className="text-[10px] text-center opacity-60">The Python backend is starting up. Library templates will appear once connected.</span>
      </div>
    );
  }

  if (loading && serverReady) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-muted)]">
        <span className="w-3 h-3 border-2 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin mr-2" />
        <span className="text-[10px]">Loading library...</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-2 border-b border-[var(--border)]">
        <div className="relative">
          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-xs">🔍</span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search circuits..."
            className="w-full pl-7 pr-2 py-1.5 rounded-lg text-xs bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border)] focus:border-[var(--border-focus)] focus:outline-none transition-colors placeholder:text-[var(--text-muted)]"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="flex gap-1 px-2 py-1.5 border-b border-[var(--border)] overflow-x-auto">
        <CatBtn active={!selectedCat} onClick={() => setSelectedCat(null)} label="All" count={templates.length} />
        {categories.map((cat) => (
          <CatBtn
            key={cat}
            active={selectedCat === cat}
            onClick={() => setSelectedCat(cat === selectedCat ? null : cat)}
            label={cat}
            count={templates.filter((t) => t.category === cat).length}
          />
        ))}
      </div>

      {/* Templates */}
      <div className="flex-1 overflow-auto p-2 space-y-1.5">
        {filtered.map((t) => (
          <button
            key={t.template_id}
            onClick={() => handleLoad(t)}
            className="w-full text-left p-2.5 rounded-lg panel-hover border border-transparent group transition-all"
          >
            <div className="flex items-start justify-between">
              <span className="font-medium text-xs text-[var(--text-primary)] group-hover:text-[var(--accent-primary)] transition-colors">
                {t.name}
              </span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${DIFF_COLORS[t.difficulty] || ''}`}>
                {t.difficulty}
              </span>
            </div>
            <div className="mt-1 text-[10px] text-[var(--text-muted)] line-clamp-2">{t.description}</div>
            <div className="mt-1.5 flex items-center gap-2 text-[10px] text-[var(--text-secondary)]">
              <span>{t.num_qubits} qubits</span>
              <span>·</span>
              <span>depth {t.depth}</span>
              <span>·</span>
              <span>{t.gates.length} gates</span>
            </div>
            <div className="mt-1.5 flex gap-1 flex-wrap">
              {t.tags.slice(0, 4).map((tag) => (
                <span key={tag} className="px-1.5 py-0.5 rounded-full bg-[var(--bg-input)] text-[9px] text-[var(--text-muted)]">
                  {tag}
                </span>
              ))}
            </div>
          </button>
        ))}
        {filtered.length === 0 && (
          <div className="text-center py-8 text-[var(--text-muted)]">
            <span className="text-2xl block mb-2 opacity-30">📚</span>
            <span className="text-[10px]">No circuits found</span>
          </div>
        )}
      </div>
    </div>
  );
}

function CatBtn({ active, onClick, label, count }: { active: boolean; onClick: () => void; label: string; count: number }) {
  return (
    <button
      onClick={onClick}
      className={`px-2 py-0.5 rounded-full text-[10px] font-medium whitespace-nowrap transition-all ${
        active
          ? 'bg-[var(--accent-primary)] text-white'
          : 'bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
      }`}
    >
      {label} ({count})
    </button>
  );
}
