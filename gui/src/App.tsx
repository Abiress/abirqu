import React, { useEffect, useState } from 'react';
import Toolbar from './components/Toolbar';
import StatusBar from './components/StatusBar';
import CircuitCanvas from './components/CircuitCanvas/CircuitCanvas';
import CodePanel from './components/CodePanel/CodeEditor';
import OpenQASMPanel from './components/OpenQASMPanel/OpenQASMPanel';
import BlochSphere from './components/BlochSphere/BlochSphere';
import StateVector from './components/StateVector/StateVector';
import MeasurementResults from './components/MeasurementResults/MeasurementResults';
import HardwareSidebar from './components/HardwareSidebar/HardwarePanel';
import JobDashboard from './components/JobDashboard/JobPanel';
import LibrarySidebar from './components/LibrarySidebar/CircuitLibrary';
import Console from './components/Console/Console';
import FrameworkPanel from './components/FrameworkPanel/FrameworkPanel';
import ExportDialog from './components/ExportDialog/ExportDialog';
import NoisePanel from './components/NoisePanel/NoisePanel';
import ExplorerPanel from './components/ExplorerPanel/ExplorerPanel';
import QECPanel from './components/QECPanel/QECPanel';
import QCommPanel from './components/QCommPanel/QCommPanel';
import DomainPanel from './components/DomainPanel/DomainPanel';
import SecurityPanel from './components/SecurityPanel/SecurityPanel';
import PluginsPanel from './components/PluginsPanel/PluginsPanel';
import AskQuantumPanel from './components/AskQuantumPanel/AskQuantumPanel';
import SettingsPanel from './components/SettingsPanel/SettingsPanel';
import { useJobStore } from './stores/jobStore';
import { api } from './api/commands';

type LeftTab = 'circuit' | 'code' | 'qasm' | 'library' | 'framework' | 'explorer' | 'qec' | 'qcomm' | 'domain' | 'security' | 'plugins' | 'askq' | 'settings';
type RightPanel = 'measurement' | 'state' | 'bloch';
type SideTab = 'hardware' | 'jobs' | 'noise';
type BottomTab = 'console' | 'results';

export default function App() {
  const [leftTab, setLeftTab] = useState<LeftTab>('circuit');
  const [rightPanel, setRightPanel] = useState<RightPanel>('measurement');
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [sideTab, setSideTab] = useState<SideTab>('hardware');
  const [bottomTab, setBottomTab] = useState<BottomTab>('console');
  const [sidebarWidth, setSidebarWidth] = useState(220);
  const [rightWidth, setRightWidth] = useState(320);
  const [bottomHeight, setBottomHeight] = useState(140);
  const [exportOpen, setExportOpen] = useState(false);
  const [noiseConfig, setNoiseConfig] = useState({
    depolarizing: 0, amplitudeDamping: 0, phaseDamping: 0, readoutError: 0, enabled: false,
  });
  const { activeJobId } = useJobStore();

  useEffect(() => {
    api.startServer().catch(console.error);
  }, []);

  const handleDrag = (e: React.MouseEvent, setter: (v: number) => void, min: number, max: number, axis: 'x' | 'y') => {
    e.preventDefault();
    const start = axis === 'x' ? e.clientX : e.clientY;
    const onMove = (ev: MouseEvent) => {
      const delta = (axis === 'x' ? ev.clientX : ev.clientY) - start;
      setter(Math.max(min, Math.min(max, start + delta)));
    };
    const onUp = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-primary)] text-[var(--text-primary)] select-none">
      <Toolbar onExport={() => setExportOpen(true)} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 flex overflow-hidden min-h-0">

          {/* Left Sidebar */}
          <div className="flex flex-col border-r border-white/5 bg-[var(--bg-panel)]" style={{ width: sidebarWidth }}>
            <div className="flex border-b border-white/5">
              <SideTabBtn active={sideTab === 'hardware'} onClick={() => setSideTab('hardware')} icon="⚡" label="HW" />
              <SideTabBtn active={sideTab === 'jobs'} onClick={() => setSideTab('jobs')} icon="📋" label="Jobs" />
              <SideTabBtn active={sideTab === 'noise'} onClick={() => setSideTab('noise')} icon="〰" label="Noise" />
            </div>
            <div className="flex-1 overflow-hidden">
              {sideTab === 'hardware' && <HardwareSidebar />}
              {sideTab === 'jobs' && <JobDashboard />}
              {sideTab === 'noise' && (
                <div className="p-2">
                  <NoisePanel config={noiseConfig} onChange={setNoiseConfig} />
                </div>
              )}
            </div>
          </div>

          <div
            onMouseDown={(e) => handleDrag(e, setSidebarWidth, 160, 400, 'x')}
            className="w-1 flex-shrink-0 cursor-col-resize group hover:bg-[var(--accent-primary)]/20 bg-white/5 transition-colors"
          />

          {/* Center Editor */}
          <div className="flex-1 flex flex-col overflow-hidden min-w-0">
            <div className="flex items-center border-b border-white/5 bg-[var(--bg-panel)] overflow-x-auto">
              <EditorTab active={leftTab === 'circuit'} onClick={() => setLeftTab('circuit')} icon="⚡" label="Circuit" />
              <EditorTab active={leftTab === 'code'} onClick={() => setLeftTab('code')} icon="{ }" label="Python" />
              <EditorTab active={leftTab === 'qasm'} onClick={() => setLeftTab('qasm')} icon="⟨⟩" label="QASM" />
              <EditorTab active={leftTab === 'library'} onClick={() => setLeftTab('library')} icon="📚" label="Library" />
              <EditorTab active={leftTab === 'framework'} onClick={() => setLeftTab('framework')} icon="🔗" label="Frameworks" />
              <EditorTab active={leftTab === 'explorer'} onClick={() => setLeftTab('explorer')} icon="📁" label="Explorer" />
              <EditorTab active={leftTab === 'qec'} onClick={() => setLeftTab('qec')} icon="🛡" label="QEC" />
              <EditorTab active={leftTab === 'qcomm'} onClick={() => setLeftTab('qcomm')} icon="📡" label="Q-Comm" />
              <EditorTab active={leftTab === 'domain'} onClick={() => setLeftTab('domain')} icon="🧪" label="Domains" />
              <EditorTab active={leftTab === 'security'} onClick={() => setLeftTab('security')} icon="🔐" label="Security" />
              <EditorTab active={leftTab === 'plugins'} onClick={() => setLeftTab('plugins')} icon="🧩" label="Plugins" />
              <EditorTab active={leftTab === 'askq'} onClick={() => setLeftTab('askq')} icon="💬" label="Ask Q" />
              <EditorTab active={leftTab === 'settings'} onClick={() => setLeftTab('settings')} icon="⚙" label="Settings" />
              <div className="flex-1" />
              <div className="px-3 text-[10px] text-[var(--text-muted)] flex items-center gap-2">
                {noiseConfig.enabled && (
                  <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[9px]">
                    Noise ON
                  </span>
                )}
                {activeJobId && (
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)] animate-pulse" />
                    {activeJobId.slice(0, 8)}
                  </span>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-hidden animate-fade-in">
              {leftTab === 'circuit' && <CircuitCanvas />}
              {leftTab === 'code' && <CodePanel />}
              {leftTab === 'qasm' && <OpenQASMPanel />}
              {leftTab === 'library' && <LibrarySidebar />}
              {leftTab === 'framework' && <FrameworkPanel />}
              {leftTab === 'explorer' && <ExplorerPanel />}
              {leftTab === 'qec' && <QECPanel />}
              {leftTab === 'qcomm' && <QCommPanel />}
              {leftTab === 'domain' && <DomainPanel />}
              {leftTab === 'security' && <SecurityPanel />}
              {leftTab === 'plugins' && <PluginsPanel />}
              {leftTab === 'askq' && <AskQuantumPanel />}
              {leftTab === 'settings' && <SettingsPanel />}
            </div>
          </div>

          {!rightCollapsed && (
            <div
              onMouseDown={(e) => handleDrag(e, setRightWidth, 200, 600, 'x')}
              className="w-1 flex-shrink-0 cursor-col-resize group hover:bg-[var(--accent-primary)]/20 bg-white/5 transition-colors"
            />
          )}

          {!rightCollapsed ? (
            <div className="flex flex-col border-l border-white/5 bg-[var(--bg-panel)] animate-slide-in" style={{ width: rightWidth }}>
              <div className="flex items-center border-b border-white/5">
                <RightTab active={rightPanel === 'measurement'} onClick={() => setRightPanel('measurement')} label="Results" />
                <RightTab active={rightPanel === 'state'} onClick={() => setRightPanel('state')} label="States" />
                <RightTab active={rightPanel === 'bloch'} onClick={() => setRightPanel('bloch')} label="Bloch" />
                <button
                  onClick={() => setRightCollapsed(true)}
                  className="ml-auto px-2 py-1 text-[10px] text-[var(--text-muted)] hover:text-[var(--accent-error)]"
                >
                  ✕
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                {rightPanel === 'measurement' && <MeasurementResults />}
                {rightPanel === 'state' && <StateVector />}
                {rightPanel === 'bloch' && <BlochSphere />}
              </div>
            </div>
          ) : (
            <button
              onClick={() => setRightCollapsed(false)}
              className="w-6 flex items-center justify-center border-l border-white/5 bg-[var(--bg-panel)] hover:bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs transition-colors"
            >
              ⟨
            </button>
          )}
        </div>

        <div
          onMouseDown={(e) => handleDrag(e, setBottomHeight, 60, 400, 'y')}
          className="h-1 flex-shrink-0 cursor-row-resize group hover:bg-[var(--accent-primary)]/20 bg-white/5 transition-colors"
        />

        <div className="flex flex-col border-t border-white/5 bg-[var(--bg-panel)]" style={{ height: bottomHeight }}>
          <div className="flex items-center border-b border-white/5 px-2">
            <BottomTab active={bottomTab === 'console'} onClick={() => setBottomTab('console')} label="Console" />
            <BottomTab active={bottomTab === 'results'} onClick={() => setBottomTab('results')} label="Results" />
          </div>
          <div className="flex-1 overflow-hidden">
            {bottomTab === 'console' ? <Console /> : <MeasurementResults compact />}
          </div>
        </div>
      </div>

      <StatusBar />
      <ExportDialog open={exportOpen} onClose={() => setExportOpen(false)} />
    </div>
  );
}

function SideTabBtn({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: string; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-[10px] transition-all ${
        active
          ? 'text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)] bg-[var(--accent-primary)]/5'
          : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
      }`}
    >
      <span>{icon}</span>
      {label}
    </button>
  );
}

function EditorTab({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: string; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-all whitespace-nowrap ${
        active
          ? 'text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)] bg-[var(--accent-primary)]/5'
          : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-white/[0.02]'
      }`}
    >
      <span className="text-[11px]">{icon}</span>
      {label}
    </button>
  );
}

function RightTab({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 text-[11px] font-medium transition-all ${
        active
          ? 'text-[var(--accent-primary)] border-b-2 border-[var(--accent-primary)]'
          : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
      }`}
    >
      {label}
    </button>
  );
}

function BottomTab({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 text-[11px] font-medium transition-all ${
        active
          ? 'text-[var(--accent-primary)] border-b border-[var(--accent-primary)]'
          : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
      }`}
    >
      {label}
    </button>
  );
}
