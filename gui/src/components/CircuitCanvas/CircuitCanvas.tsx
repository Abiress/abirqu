import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useCircuitStore } from '../../stores/circuitStore';

const GATE_COLORS: Record<string, string> = {
  H: '#a855f7', X: '#ef4444', Y: '#eab308', Z: '#22c55e',
  CNOT: '#3b82f6', CX: '#3b82f6', CZ: '#3b82f6',
  S: '#a855f7', Sdg: '#a855f7', T: '#f97316', Tdg: '#f97316',
  Rx: '#ef4444', Ry: '#eab308', Rz: '#22c55e',
  SWAP: '#ef4444', Toffoli: '#c084fc', CCX: '#c084fc',
  Measure: '#f97316', Barrier: '#6b7280',
};

const GATE_PALETTE = [
  { name: 'H', desc: 'Hadamard' },
  { name: 'X', desc: 'Pauli-X' },
  { name: 'Y', desc: 'Pauli-Y' },
  { name: 'Z', desc: 'Pauli-Z' },
  { name: 'S', desc: 'S Gate' },
  { name: 'T', desc: 'T Gate' },
  { name: 'Rx', desc: 'Rx Rotation' },
  { name: 'Ry', desc: 'Ry Rotation' },
  { name: 'Rz', desc: 'Rz Rotation' },
  { name: 'CNOT', desc: 'CNOT' },
  { name: 'CZ', desc: 'CZ Gate' },
  { name: 'SWAP', desc: 'SWAP' },
  { name: 'Toffoli', desc: 'Toffoli' },
  { name: 'Measure', desc: 'Measure' },
];

const COL_W = 72;
const ROW_H = 52;
const GATE_W = 46;
const GATE_H = 36;
const PAD_L = 64;
const PAD_T = 28;

export default function CircuitCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const {
    numQubits, gates, selectedGate, selectGate,
    addGate, removeGate, hoveredCell, setHoveredCell,
  } = useCircuitStore();
  const [dragOver, setDragOver] = useState(false);
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; gateIdx: number } | null>(null);

  const numCols = Math.max(gates.length + 3, 10);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const w = PAD_L + numCols * COL_W + 60;
    const h = PAD_T + numQubits * ROW_H + 50;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.scale(dpr, dpr);

    // Background
    const bg = getComputedStyle(document.documentElement).getPropertyValue('--bg-editor').trim();
    ctx.fillStyle = bg || '#0d1117';
    ctx.fillRect(0, 0, w, h);

    // Grid dots
    ctx.fillStyle = '#1e293b';
    for (let q = 0; q < numQubits; q++) {
      for (let c = 0; c < numCols; c++) {
        const x = PAD_L + c * COL_W + COL_W / 2;
        const y = PAD_T + q * ROW_H + ROW_H / 2;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Qubit wires
    for (let q = 0; q < numQubits; q++) {
      const y = PAD_T + q * ROW_H + ROW_H / 2;

      // Label background
      ctx.fillStyle = '#0f172a';
      roundRect(ctx, 4, y - 12, PAD_L - 12, 24, 6);
      ctx.fill();

      // Label
      ctx.fillStyle = '#94a3b8';
      ctx.font = 'bold 12px "SF Mono", "Fira Code", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`q${q}`, PAD_L / 2, y);

      // Wire
      const grad = ctx.createLinearGradient(PAD_L, y, PAD_L + numCols * COL_W, y);
      grad.addColorStop(0, '#334155');
      grad.addColorStop(0.5, '#475569');
      grad.addColorStop(1, '#334155');
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.moveTo(PAD_L, y);
      ctx.lineTo(PAD_L + numCols * COL_W, y);
      ctx.stroke();
    }

    // Draw gates
    gates.forEach((gate, idx) => {
      const col = idx;
      const q = gate.qubits[0];
      const x = PAD_L + col * COL_W + COL_W / 2;
      const y = PAD_T + q * ROW_H + ROW_H / 2;
      const color = GATE_COLORS[gate.name] || '#64748b';

      // Multi-qubit connection line
      if (gate.qubits.length > 1) {
        const targetQ = gate.qubits[1];
        const ty = PAD_T + targetQ * ROW_H + ROW_H / 2;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x, ty);
        ctx.stroke();

        // Target circle (⊕)
        ctx.beginPath();
        ctx.arc(x, ty, 13, 0, Math.PI * 2);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
        // Cross
        ctx.beginPath();
        ctx.moveTo(x, ty - 13);
        ctx.lineTo(x, ty + 13);
        ctx.moveTo(x - 13, ty);
        ctx.lineTo(x + 13, ty);
        ctx.stroke();
      }

      // Gate glow
      ctx.shadowColor = color;
      ctx.shadowBlur = 12;

      // Gate box
      ctx.fillStyle = color;
      const rx = x - GATE_W / 2;
      const ry = y - GATE_H / 2;
      roundRect(ctx, rx, ry, GATE_W, GATE_H, 6);
      ctx.fill();

      ctx.shadowBlur = 0;

      // Gate label
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 12px "SF Mono", "Fira Code", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(gate.name, x, y);

      // Control dot for CNOT/CZ
      if (['CNOT', 'CX', 'CZ'].includes(gate.name) && gate.qubits.length > 1) {
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Hover highlight
    if (hoveredCell) {
      const x = PAD_L + hoveredCell.col * COL_W;
      const y = PAD_T + hoveredCell.qubit * ROW_H;
      ctx.fillStyle = 'rgba(139, 92, 246, 0.08)';
      roundRect(ctx, x + 2, y + 2, COL_W - 4, ROW_H - 4, 4);
      ctx.fill();
      ctx.strokeStyle = 'rgba(139, 92, 246, 0.25)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      roundRect(ctx, x + 2, y + 2, COL_W - 4, ROW_H - 4, 4);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Drop indicator
    if (dragOver && hoveredCell && selectedGate) {
      const x = PAD_L + hoveredCell.col * COL_W + COL_W / 2;
      const y = PAD_T + hoveredCell.qubit * ROW_H + ROW_H / 2;
      const color = GATE_COLORS[selectedGate] || '#64748b';
      ctx.globalAlpha = 0.4;
      ctx.fillStyle = color;
      roundRect(ctx, x - GATE_W / 2, y - GATE_H / 2, GATE_W, GATE_H, 6);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }, [numQubits, gates, hoveredCell, selectedGate, dragOver, numCols]);

  useEffect(() => { draw(); }, [draw]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const col = Math.floor((x - PAD_L) / COL_W);
    const qubit = Math.floor((y - PAD_T) / ROW_H);
    if (col >= 0 && col < numCols && qubit >= 0 && qubit < numQubits) {
      setHoveredCell({ qubit, col });
    } else {
      setHoveredCell(null);
    }
  }, [numQubits, numCols, setHoveredCell]);

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    setCtxMenu(null);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const col = Math.floor((x - PAD_L) / COL_W);
    const qubit = Math.floor((y - PAD_T) / ROW_H);

    if (col >= 0 && qubit >= 0 && qubit < numQubits) {
      const gateIdx = col;
      if (gateIdx >= 0 && gateIdx < gates.length && gates[gateIdx].qubits.includes(qubit)) {
        removeGate(qubit, col);
      } else if (selectedGate) {
        const isMulti = ['CNOT', 'CX', 'CZ', 'SWAP', 'Toffoli', 'CCX'].includes(selectedGate);
        const target = isMulti ? (qubit + 1) % numQubits : undefined;
        addGate(selectedGate, qubit, target);
      }
    }
  }, [selectedGate, numQubits, gates, addGate, removeGate]);

  const handleContextMenu = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const col = Math.floor((x - PAD_L) / COL_W);
    const qubit = Math.floor((y - PAD_T) / ROW_H);
    if (col >= 0 && col < gates.length) {
      setCtxMenu({ x: e.clientX, y: e.clientY, gateIdx: col });
    }
  }, [gates.length]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const gateName = e.dataTransfer.getData('gate');
    if (!gateName) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const qubit = Math.floor((y - PAD_T) / ROW_H);
    if (qubit >= 0 && qubit < numQubits) {
      const isMulti = ['CNOT', 'CX', 'CZ', 'SWAP', 'Toffoli', 'CCX'].includes(gateName);
      addGate(gateName, qubit, isMulti ? (qubit + 1) % numQubits : undefined);
    }
  }, [numQubits, addGate]);

  return (
    <div className="flex flex-col h-full relative">
      {/* Gate Palette */}
      <div className="flex flex-wrap items-center gap-1.5 px-3 py-2 border-b border-white/5 bg-gradient-to-r from-slate-900/80 to-slate-800/50 backdrop-blur-sm">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider mr-1">Gates</span>
        {GATE_PALETTE.map((g) => (
          <div
            key={g.name}
            draggable
            onDragStart={(e) => e.dataTransfer.setData('gate', g.name)}
            onClick={() => selectGate(selectedGate === g.name ? null : g.name)}
            title={g.desc}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-bold cursor-grab active:cursor-grabbing select-none transition-all duration-150 hover:scale-110 hover:shadow-lg ${
              selectedGate === g.name
                ? 'ring-2 ring-white/40 scale-110 shadow-lg'
                : 'opacity-80 hover:opacity-100'
            }`}
            style={{
              backgroundColor: GATE_COLORS[g.name] || '#64748b',
              color: '#fff',
              textShadow: '0 1px 2px rgba(0,0,0,0.3)',
            }}
          >
            {g.name}
          </div>
        ))}
      </div>

      {/* Canvas */}
      <div className="flex-1 overflow-auto bg-[var(--bg-editor)]">
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredCell(null)}
          onClick={handleClick}
          onContextMenu={handleContextMenu}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className="cursor-crosshair"
        />
      </div>

      {/* Context menu */}
      {ctxMenu && (
        <div
          className="fixed z-50 bg-slate-800 border border-slate-600 rounded-lg shadow-2xl py-1 min-w-[140px]"
          style={{ left: ctxMenu.x, top: ctxMenu.y }}
          onMouseLeave={() => setCtxMenu(null)}
        >
          <button
            className="w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 hover:text-white"
            onClick={() => { removeGate(0, ctxMenu.gateIdx); setCtxMenu(null); }}
          >
            🗑 Delete Gate
          </button>
          <button
            className="w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 hover:text-white"
            onClick={() => {
              if (ctxMenu.gateIdx >= 0 && ctxMenu.gateIdx < gates.length) {
                const gate = gates[ctxMenu.gateIdx];
                navigator.clipboard.writeText(`${gate.name} q${gate.qubits.join(',q')}`).catch(() => {});
              }
              setCtxMenu(null);
            }}
          >
            📋 Copy Gate
          </button>
        </div>
      )}
    </div>
  );
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}
