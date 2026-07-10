import React, { useState, useCallback, useRef, useEffect } from 'react';

interface Props {
  direction: 'horizontal' | 'vertical';
  initialSize: number;
  minSize?: number;
  maxSize?: number;
  children: [React.ReactNode, React.ReactNode];
  className?: string;
}

export default function ResizablePanel({
  direction,
  initialSize,
  minSize = 100,
  maxSize = Infinity,
  children,
  className = '',
}: Props) {
  const [size, setSize] = useState(initialSize);
  const [dragging, setDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const startPos = useRef(0);
  const startSize = useRef(0);

  const isHorizontal = direction === 'horizontal';

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setDragging(true);
    startPos.current = isHorizontal ? e.clientX : e.clientY;
    startSize.current = size;
  }, [isHorizontal, size]);

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: MouseEvent) => {
      const delta = (isHorizontal ? e.clientX : e.clientY) - startPos.current;
      const newSize = Math.max(minSize, Math.min(maxSize, startSize.current + delta));
      setSize(newSize);
    };
    const onUp = () => setDragging(false);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [dragging, isHorizontal, minSize, maxSize]);

  const panelStyle = isHorizontal
    ? { width: size, minWidth: minSize, maxWidth: maxSize }
    : { height: size, minHeight: minSize, maxHeight: maxSize };

  const handleStyle = isHorizontal
    ? { width: 4, cursor: 'col-resize' }
    : { height: 4, cursor: 'row-resize' };

  return (
    <div
      ref={containerRef}
      className={`flex ${isHorizontal ? 'flex-row' : 'flex-col'} ${className}`}
    >
      <div style={panelStyle} className="overflow-hidden flex-shrink-0">
        {children[0]}
      </div>
      <div
        onMouseDown={handleMouseDown}
        className={`flex-shrink-0 group transition-colors ${
          isHorizontal ? 'w-1 hover:w-1.5' : 'h-1 hover:h-1.5'
        } ${dragging ? 'bg-[var(--accent-primary)]/40' : 'bg-white/5 hover:bg-[var(--accent-primary)]/20'}`}
        style={handleStyle}
      >
        <div className={`${
          isHorizontal ? 'w-full h-8' : 'h-full w-8'
        } mx-auto my-auto flex items-center justify-center`}>
          <div className={`${
            isHorizontal ? 'w-0.5 h-4' : 'h-0.5 w-4'
          } rounded-full bg-[var(--text-muted)]/30 group-hover:bg-[var(--accent-primary)]/50 transition-colors`} />
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        {children[1]}
      </div>
    </div>
  );
}
