import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useJobStore } from '../../stores/jobStore';

export default function BlochSphere() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rotRef = useRef({ x: -0.4, y: 0.6 });
  const [dragging, setDragging] = useState(false);
  const { activeJobId, results } = useJobStore();
  const data = activeJobId ? results[activeJobId] : null;

  // Extract theta/phi from results
  let theta = Math.PI / 4;
  let phi = 0;
  if (data?.counts) {
    const counts = data.counts as Record<string, number>;
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    if (total > 0) {
      // For multi-qubit states (e.g. "00", "01", "10", "11"),
      // compute the probability of qubit 0 being |0⟩ by summing
      // all basis states whose first character is '0'.
      let p0 = 0;
      for (const [state, count] of Object.entries(counts)) {
        if (state.length > 0 && state[0] === '0') {
          p0 += count / total;
        }
      }
      theta = 2 * Math.acos(Math.min(1, Math.sqrt(Math.max(0, p0))));
      // Compute phi from qubit 0's off-diagonal coherence:
      // average phase of |0⟩-starting states weighted by amplitude.
      // For a simple estimate, use the ratio of |01⟩ to |00⟩ amplitudes.
      const n = Object.keys(counts)[0]?.length || 1;
      if (n >= 2) {
        let sumIm = 0;
        let sumRe = 0;
        for (const [state, count] of Object.entries(counts)) {
          if (state.length >= 2 && state[0] === '0' && state[1] === '1') {
            sumRe += count / total;
          }
          if (state.length >= 2 && state[0] === '0' && state[1] === '0') {
            sumIm += count / total;
          }
        }
        if (sumRe + sumIm > 0) {
          phi = Math.atan2(sumRe, sumIm);
        }
      }
    }
  }

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const w = 280;
    const h = 280;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.scale(dpr, dpr);

    const cx = w / 2;
    const cy = h / 2;
    const r = 100;
    const rx = rotRef.current.x;
    const ry = rotRef.current.y;
    const cosX = Math.cos(rx), sinX = Math.sin(rx);
    const cosY = Math.cos(ry), sinY = Math.sin(ry);

    const project = (x: number, y: number, z: number): [number, number] => {
      const y1 = y * cosX - z * sinX;
      const z1 = y * sinX + z * cosX;
      const x1 = x * cosY + z1 * sinY;
      const z2 = -x * sinY + z1 * cosY;
      return [cx + x1 * r, cy - z2 * r];
    };

    // Clear
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg-editor').trim() || '#0a0a18';
    ctx.fillRect(0, 0, w, h);

    // Sphere glow
    const glowGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r * 1.5);
    glowGrad.addColorStop(0, 'rgba(139, 92, 246, 0.05)');
    glowGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = glowGrad;
    ctx.fillRect(0, 0, w, h);

    // Great circles
    const planes = [
      { gen: (t: number) => [Math.cos(t), Math.sin(t), 0], color: 'rgba(34, 197, 94, 0.15)' },
      { gen: (t: number) => [Math.cos(t), 0, Math.sin(t)], color: 'rgba(239, 68, 68, 0.15)' },
      { gen: (t: number) => [0, Math.cos(t), Math.sin(t)], color: 'rgba(59, 130, 246, 0.15)' },
    ];

    for (const plane of planes) {
      ctx.strokeStyle = plane.color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i <= 64; i++) {
        const t = (2 * Math.PI * i) / 64;
        const [px, py] = project(...plane.gen(t) as [number, number, number]);
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.stroke();
    }

    // Axes
    const axes = [
      { dir: [1.2, 0, 0], color: '#ef4444', label: 'X' },
      { dir: [0, 1.2, 0], color: '#22c55e', label: 'Y' },
      { dir: [0, 0, 1.2], color: '#3b82f6', label: 'Z' },
    ];

    for (const axis of axes) {
      const [x1, y1] = project(...axis.dir as [number, number, number]);
      const [x2, y2] = project(...axis.dir.map((v) => -v) as [number, number, number]);
      ctx.strokeStyle = axis.color + '40';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      ctx.setLineDash([]);

      const [lx, ly] = project(...axis.dir.map((v) => v * 1.15) as [number, number, number]);
      ctx.fillStyle = axis.color;
      ctx.font = 'bold 10px monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(axis.label, lx, ly);
    }

    // State labels
    const labels = [
      { pos: [0, 0, 1.3], text: '|0⟩', color: '#3b82f6' },
      { pos: [0, 0, -1.3], text: '|1⟩', color: '#ef4444' },
      { pos: [1.3, 0, 0], text: '|+⟩', color: '#22c55e' },
      { pos: [-1.3, 0, 0], text: '|−⟩', color: '#22c55e' },
    ];

    for (const label of labels) {
      const [lx, ly] = project(...label.pos as [number, number, number]);
      ctx.fillStyle = label.color + '80';
      ctx.font = '9px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(label.text, lx, ly);
    }

    // State vector arrow
    const sx = Math.sin(theta) * Math.cos(phi);
    const sy = Math.sin(theta) * Math.sin(phi);
    const sz = Math.cos(theta);
    const [ax, ay] = project(sx, sy, sz);

    // Arrow glow
    ctx.shadowColor = '#8b5cf6';
    ctx.shadowBlur = 15;

    // Arrow line
    const grad = ctx.createLinearGradient(cx, cy, ax, ay);
    grad.addColorStop(0, '#8b5cf680');
    grad.addColorStop(1, '#8b5cf6');
    ctx.strokeStyle = grad;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(ax, ay);
    ctx.stroke();

    // Arrow tip
    ctx.fillStyle = '#8b5cf6';
    ctx.beginPath();
    ctx.arc(ax, ay, 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.shadowBlur = 0;

    // Inner dot
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(ax, ay, 2.5, 0, Math.PI * 2);
    ctx.fill();
  }, [theta, phi]);

  useEffect(() => { draw(); }, [draw]);

  // Slow auto-rotate
  useEffect(() => {
    if (dragging) return;
    let frame: number;
    const animate = () => {
      rotRef.current.y += 0.002;
      draw();
      frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [draw, dragging]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setDragging(true);
    const startX = e.clientX;
    const startY = e.clientY;
    const startRot = { ...rotRef.current };

    const onMove = (e: MouseEvent) => {
      rotRef.current.y = startRot.y + (e.clientX - startX) * 0.008;
      rotRef.current.x = startRot.x + (e.clientY - startY) * 0.008;
    };
    const onUp = () => {
      setDragging(false);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, []);

  return (
    <div className="flex flex-col h-full items-center">
      <div className="flex-1 flex items-center justify-center">
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          className="cursor-grab active:cursor-grabbing"
        />
      </div>
      <div className="px-3 py-2 border-t border-[var(--border)] w-full">
        <div className="flex justify-between text-[10px] text-[var(--text-muted)] font-mono">
          <span>θ = {theta.toFixed(3)}</span>
          <span>φ = {phi.toFixed(3)}</span>
        </div>
        <div className="text-center text-[9px] text-[var(--text-muted)] mt-1 opacity-50">
          Drag to rotate
        </div>
      </div>
    </div>
  );
}
