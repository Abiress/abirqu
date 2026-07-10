import React, { useState, useCallback } from 'react';
import { useCircuitStore } from '../../stores/circuitStore';
import { useJobStore } from '../../stores/jobStore';
import { api } from '../../api/commands';

interface Props {
  open: boolean;
  onClose: () => void;
}

type ExportFormat = 'html' | 'qasm' | 'json' | 'pdf_html';

const FORMATS: { key: ExportFormat; label: string; icon: string; desc: string }[] = [
  { key: 'html', label: 'HTML Report', icon: '📄', desc: 'Full research report with circuit, results, and stats' },
  { key: 'pdf_html', label: 'PDF (via HTML)', icon: '📑', desc: 'Print-ready — opens HTML for browser Print to PDF' },
  { key: 'qasm', label: 'OpenQASM 2.0', icon: '{ }', desc: 'Industry-standard quantum assembly language' },
  { key: 'json', label: 'JSON', icon: '{ }', desc: 'Circuit + results in structured JSON format' },
];

export default function ExportDialog({ open, onClose }: Props) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('html');
  const [exporting, setExporting] = useState(false);
  const [preview, setPreview] = useState('');
  const { getCircuitData } = useCircuitStore();
  const { activeJobId, results } = useJobStore();
  const activeResult = activeJobId ? results[activeJobId] : null;

  const handleExport = useCallback(async () => {
    setExporting(true);
    try {
      const circuit = getCircuitData();
      const result = await api.exportCircuit(circuit, selectedFormat, activeResult);
      if (result?.content) {
        setPreview(result.content);
        if (selectedFormat === 'html' || selectedFormat === 'pdf_html') {
          const blob = new Blob([result.content], { type: 'text/html' });
          const url = URL.createObjectURL(blob);
          const w = window.open(url, '_blank');
          if (selectedFormat === 'pdf_html' && w) {
            setTimeout(() => { w.print(); }, 500);
          }
        } else {
          const blob = new Blob([result.content], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `abirqu-export.${selectedFormat === 'json' ? 'json' : selectedFormat}`;
          a.click();
          URL.revokeObjectURL(url);
        }
      }
    } catch (err) {
      setPreview(`Export error: ${err}`);
    }
    setExporting(false);
  }, [selectedFormat, getCircuitData, activeResult]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-[520px] max-h-[80vh] bg-[var(--bg-panel)] border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-white/5">
          <div>
            <div className="text-sm font-bold text-[var(--text-primary)]">Export Research Report</div>
            <div className="text-[10px] text-[var(--text-muted)]">Circuit + results for publications, sharing, or backup</div>
          </div>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-lg">✕</button>
        </div>

        {/* Format selector */}
        <div className="p-4 space-y-2">
          {FORMATS.map((f) => (
            <button
              key={f.key}
              onClick={() => setSelectedFormat(f.key)}
              className={`w-full flex items-center gap-3 p-3 rounded-xl text-left transition-all ${
                selectedFormat === f.key
                  ? 'bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/30 shadow-sm'
                  : 'border border-white/5 hover:bg-white/[0.02]'
              }`}
            >
              <span className="text-lg">{f.icon}</span>
              <div>
                <div className="text-xs font-semibold text-[var(--text-primary)]">{f.label}</div>
                <div className="text-[10px] text-[var(--text-muted)]">{f.desc}</div>
              </div>
            </button>
          ))}
        </div>

        {/* Preview */}
        {preview && (
          <div className="mx-4 mb-3 p-2 rounded-lg bg-[var(--bg-editor)] border border-white/5 max-h-40 overflow-auto">
            <pre className="text-[10px] text-[var(--text-secondary)] font-mono whitespace-pre-wrap">
              {preview.slice(0, 1000)}
            </pre>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-white/5">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/5 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-5 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent-primary)] text-white hover:shadow-lg hover:shadow-[var(--accent-primary)]/20 transition-all disabled:opacity-50"
          >
            {exporting ? 'Exporting...' : `Export as ${FORMATS.find(f => f.key === selectedFormat)?.label}`}
          </button>
        </div>
      </div>
    </div>
  );
}
