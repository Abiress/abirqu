import React, { useState, useCallback } from 'react';
import { api, runCVQKD, runDIQKD, runSatelliteQKD, runRepeater, runNetwork } from '../../api/commands';

type Protocol =
  | 'BB84'
  | 'E91'
  | 'CV-QKD'
  | 'DI-QKD'
  | 'Satellite QKD'
  | 'Repeater Chains'
  | 'Quantum Network';

interface ProtocolParams {
  bb84Bits: number;
  bb84Eavesdrop: boolean;
  e91Pairs: number;
  e91CHSH: number;
  cvqkdLoss: number;
  cvqkdModVar: number;
  diqkdRounds: number;
  satAltitude: number;
  satAtmLoss: number;
  repeaterHops: number;
  networkNodes: number;
  networkTopology: 'star' | 'ring' | 'mesh';
}

interface SimulationResult {
  siftedKeyLength: number;
  qber: number;
  chshSValue: number;
  secure: boolean;
  keyMaterial: string;
  timestamp: number;
  backendResult?: any;
}

const PROTOCOLS: Protocol[] = [
  'BB84',
  'E91',
  'CV-QKD',
  'DI-QKD',
  'Satellite QKD',
  'Repeater Chains',
  'Quantum Network',
];

const DEFAULT_PARAMS: ProtocolParams = {
  bb84Bits: 1024,
  bb84Eavesdrop: false,
  e91Pairs: 2048,
  e91CHSH: 2.828,
  cvqkdLoss: 0.2,
  cvqkdModVar: 16,
  diqkdRounds: 512,
  satAltitude: 550,
  satAtmLoss: 0.3,
  repeaterHops: 3,
  networkNodes: 6,
  networkTopology: 'star',
};

function NetworkTopologySVG({ topology, nodeCount }: { topology: string; nodeCount: number }) {
  const cx = 100;
  const cy = 75;
  const r = 50;

  const getPositions = (): { x: number; y: number }[] => {
    if (topology === 'star') {
      const positions = [{ x: cx, y: cy }];
      for (let i = 0; i < nodeCount; i++) {
        const angle = (2 * Math.PI * i) / nodeCount - Math.PI / 2;
        positions.push({ x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) });
      }
      return positions;
    }
    const positions: { x: number; y: number }[] = [];
    for (let i = 0; i < nodeCount; i++) {
      const angle = (2 * Math.PI * i) / nodeCount - Math.PI / 2;
      positions.push({ x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) });
    }
    return positions;
  };

  const positions = getPositions();

  const edges: [number, number][] = [];
  if (topology === 'star') {
    for (let i = 1; i < positions.length; i++) {
      edges.push([0, i]);
    }
  } else if (topology === 'ring') {
    for (let i = 0; i < positions.length; i++) {
      edges.push([i, (i + 1) % positions.length]);
    }
  } else {
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        edges.push([i, j]);
      }
    }
  }

  return (
    <svg viewBox="0 0 200 150" className="w-full h-full">
      {edges.map(([a, b], i) => (
        <line
          key={i}
          x1={positions[a].x}
          y1={positions[a].y}
          x2={positions[b].x}
          y2={positions[b].y}
          stroke="var(--accent-primary)"
          strokeWidth="1"
          strokeOpacity="0.3"
        />
      ))}
      {positions.map((pos, i) => (
        <g key={i}>
          <circle
            cx={pos.x}
            cy={pos.y}
            r={i === 0 && topology === 'star' ? 6 : 4}
            fill={i === 0 && topology === 'star' ? 'var(--accent-primary)' : 'var(--bg-input)'}
            stroke="var(--accent-primary)"
            strokeWidth="1.5"
          />
          <text
            x={pos.x}
            y={pos.y + 3}
            textAnchor="middle"
            fill="var(--text-primary)"
            fontSize="6"
            fontFamily="monospace"
          >
            {topology === 'star' && i === 0 ? 'C' : i}
          </text>
        </g>
      ))}
    </svg>
  );
}

function QBERBar({ value }: { value: number }) {
  const percentage = Math.min(value * 100, 100);
  const color =
    value < 0.05
      ? 'bg-emerald-400'
      : value < 0.1
        ? 'bg-amber-400'
        : 'bg-red-400';

  return (
    <div className="w-full h-2 bg-[var(--bg-input)] rounded-full overflow-hidden">
      <div
        className={`h-full ${color} rounded-full transition-all duration-500`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

function SecurityIndicator({ secure }: { secure: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <div
        className={`w-2 h-2 rounded-full ${
          secure ? 'bg-emerald-400' : 'bg-red-400'
        }`}
      />
      <span
        className={`text-[10px] font-semibold ${
          secure ? 'text-[var(--accent-success)]' : 'text-[var(--accent-error)]'
        }`}
      >
        {secure ? 'SECURE' : 'INSECURE'}
      </span>
    </div>
  );
}

export default function QCommPanel() {
  const [protocol, setProtocol] = useState<Protocol>('BB84');
  const [params, setParams] = useState<ProtocolParams>(DEFAULT_PARAMS);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = useCallback(async () => {
    setRunning(true);
    setResult(null);
    setError(null);
    try {
      if (protocol === 'BB84' || protocol === 'E91') {
        const resp = await api.runQkd({
          protocol: protocol,
          num_bits: protocol === 'BB84' ? params.bb84Bits : params.e91Pairs,
          eavesdrop: protocol === 'BB84' ? params.bb84Eavesdrop : false,
        });
        const backendRes = resp;
        const keyBytes = (backendRes.final_key || []).map((b: number) => b.toString(16).padStart(2, '0')).join('');
        setResult({
          siftedKeyLength: backendRes.sifted_length || 0,
          qber: backendRes.error_rate || 0,
          chshSValue: backendRes.bell_violation || 0,
          secure: backendRes.secure || false,
          keyMaterial: keyBytes || '',
          timestamp: Date.now(),
          backendResult: backendRes,
        });
      } else if (protocol === 'CV-QKD') {
        const resp = await runCVQKD({
          excess_noise: params.cvqkdLoss,
          modulation_variance: params.cvqkdModVar,
        });
        const keyBytes = '';
        setResult({
          siftedKeyLength: resp.final_key_length,
          qber: 1 - resp.channel_transmittance,
          chshSValue: 0,
          secure: resp.secure,
          keyMaterial: keyBytes,
          timestamp: Date.now(),
          backendResult: resp,
        });
      } else if (protocol === 'DI-QKD') {
        const resp = await runDIQKD({
          num_rounds: params.diqkdRounds,
        });
        const keyBytes = '';
        setResult({
          siftedKeyLength: resp.final_key_length,
          qber: resp.error_rate,
          chshSValue: resp.chsh_parameter,
          secure: resp.secure,
          keyMaterial: keyBytes,
          timestamp: Date.now(),
          backendResult: resp,
        });
      } else if (protocol === 'Satellite QKD') {
        const resp = await runSatelliteQKD({
          altitude_km: params.satAltitude,
          detector_efficiency: 0.9,
        });
        const keyBytes = '';
        setResult({
          siftedKeyLength: resp.key_length,
          qber: resp.channel_loss_db / 100,
          chshSValue: 0,
          secure: resp.secure,
          keyMaterial: keyBytes,
          timestamp: Date.now(),
          backendResult: resp,
        });
      } else if (protocol === 'Repeater Chains') {
        const resp = await runRepeater({
          total_distance_km: params.repeaterHops * 100,
          num_segments: params.repeaterHops,
        });
        const keyBytes = '';
        setResult({
          siftedKeyLength: resp.key_length,
          qber: 1 - resp.end_to_end_fidelity,
          chshSValue: 0,
          secure: resp.end_to_end_fidelity > 0.8,
          keyMaterial: keyBytes,
          timestamp: Date.now(),
          backendResult: resp,
        });
      } else if (protocol === 'Quantum Network') {
        const resp = await runNetwork({
          topology: params.networkTopology,
          num_nodes: params.networkNodes,
        });
        const keyBytes = '';
        setResult({
          siftedKeyLength: Math.floor(resp.total_key_rate),
          qber: 1 - resp.average_fidelity,
          chshSValue: 0,
          secure: resp.average_fidelity > 0.8,
          keyMaterial: keyBytes,
          timestamp: Date.now(),
          backendResult: resp,
        });
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  }, [protocol, params]);

  const updateParams = (partial: Partial<ProtocolParams>) => {
    setParams((prev) => ({ ...prev, ...partial }));
  };

  const renderProtocolParams = () => {
    switch (protocol) {
      case 'BB84':
        return (
          <>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Number of bits</span>
              <input
                type="number"
                value={params.bb84Bits}
                onChange={(e) => updateParams({ bb84Bits: parseInt(e.target.value) || 1024 })}
                className="w-20 text-[10px] text-right bg-[var(--bg-input)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-primary)] font-mono"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Eavesdropper present</span>
              <div
                onClick={() => updateParams({ bb84Eavesdrop: !params.bb84Eavesdrop })}
                className={`w-8 h-4 rounded-full transition-colors relative cursor-pointer ${
                  params.bb84Eavesdrop ? 'bg-[var(--accent-error)]' : 'bg-[var(--bg-input)]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
                    params.bb84Eavesdrop ? 'translate-x-4' : 'translate-x-0.5'
                  }`}
                />
              </div>
            </div>
          </>
        );
      case 'E91':
        return (
          <>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Entangled pairs</span>
              <input
                type="number"
                value={params.e91Pairs}
                onChange={(e) => updateParams({ e91Pairs: parseInt(e.target.value) || 2048 })}
                className="w-20 text-[10px] text-right bg-[var(--bg-input)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-primary)] font-mono"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Target CHSH S-value</span>
              <span className="text-[10px] text-[var(--accent-primary)] font-mono">
                {params.e91CHSH.toFixed(3)}
              </span>
            </div>
          </>
        );
      case 'CV-QKD':
        return (
          <>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Channel loss</span>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={params.cvqkdLoss}
                  onChange={(e) => updateParams({ cvqkdLoss: parseFloat(e.target.value) })}
                  className="w-16 h-1 accent-[var(--accent-primary)]"
                />
                <span className="text-[9px] text-[var(--text-secondary)] w-8 text-right font-mono">
                  {(params.cvqkdLoss * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Modulation variance</span>
              <input
                type="number"
                value={params.cvqkdModVar}
                onChange={(e) => updateParams({ cvqkdModVar: parseInt(e.target.value) || 16 })}
                className="w-20 text-[10px] text-right bg-[var(--bg-input)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-primary)] font-mono"
              />
            </div>
          </>
        );
      case 'DI-QKD':
        return (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[var(--text-secondary)]">Test rounds</span>
            <input
              type="number"
              value={params.diqkdRounds}
              onChange={(e) => updateParams({ diqkdRounds: parseInt(e.target.value) || 512 })}
              className="w-20 text-[10px] text-right bg-[var(--bg-input)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-primary)] font-mono"
            />
          </div>
        );
      case 'Satellite QKD':
        return (
          <>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Orbital altitude (km)</span>
              <input
                type="number"
                value={params.satAltitude}
                onChange={(e) => updateParams({ satAltitude: parseInt(e.target.value) || 550 })}
                className="w-20 text-[10px] text-right bg-[var(--bg-input)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-primary)] font-mono"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Atmospheric loss</span>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={params.satAtmLoss}
                  onChange={(e) => updateParams({ satAtmLoss: parseFloat(e.target.value) })}
                  className="w-16 h-1 accent-[var(--accent-primary)]"
                />
                <span className="text-[9px] text-[var(--text-secondary)] w-8 text-right font-mono">
                  {(params.satAtmLoss * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </>
        );
      case 'Repeater Chains':
        return (
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[var(--text-secondary)]">Number of hops</span>
            <input
              type="number"
              value={params.repeaterHops}
              onChange={(e) => updateParams({ repeaterHops: parseInt(e.target.value) || 3 })}
              className="w-20 text-[10px] text-right bg-[var(--bg-input)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-primary)] font-mono"
            />
          </div>
        );
      case 'Quantum Network':
        return (
          <>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Number of nodes</span>
              <input
                type="number"
                value={params.networkNodes}
                onChange={(e) => updateParams({ networkNodes: Math.max(2, parseInt(e.target.value) || 6) })}
                className="w-20 text-[10px] text-right bg-[var(--bg-input)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-primary)] font-mono"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Topology</span>
              <div className="flex gap-1">
                {(['star', 'ring', 'mesh'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => updateParams({ networkTopology: t })}
                    className={`px-1.5 py-0.5 rounded text-[9px] transition-all ${
                      params.networkTopology === t
                        ? 'bg-[var(--accent-primary)] text-white'
                        : 'bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full p-2 gap-2 animate-fade-in">
      {/* Protocol selector */}
      <div className="space-y-1.5">
        <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest font-semibold px-1">
          Protocol
        </span>
        <div className="flex flex-wrap gap-1">
          {PROTOCOLS.map((p) => (
            <button
              key={p}
              onClick={() => {
                setProtocol(p);
                setResult(null);
              }}
              className={`px-2 py-1 rounded text-[10px] font-medium transition-all ${
                protocol === p
                  ? 'bg-[var(--accent-primary)] text-white shadow-sm'
                  : 'bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-[var(--border)]'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Parameters */}
      <div className="space-y-2">
        <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest font-semibold px-1">
          Parameters
        </span>
        <div className="space-y-2 p-2 bg-[var(--bg-panel)] rounded-lg border border-[var(--border)]">
          {renderProtocolParams()}
        </div>
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={running}
        className={`w-full py-2 rounded-lg text-[11px] font-semibold transition-all ${
          running
            ? 'bg-[var(--accent-primary)]/30 text-[var(--text-muted)] cursor-not-allowed'
            : 'bg-[var(--accent-primary)] text-white hover:brightness-110 active:scale-[0.98]'
        }`}
      >
        {running ? 'Simulating...' : 'Run Protocol'}
      </button>

      {error && (
        <div className="text-[10px] text-[var(--accent-error)] bg-[var(--accent-error)]/10 rounded-lg p-2 border border-[var(--accent-error)]/20">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-2 animate-fade-in">
          <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest font-semibold px-1">
            Results
          </span>

          <div className="p-2 bg-[var(--bg-panel)] rounded-lg border border-[var(--border)] space-y-2">
            {/* Security indicator */}
            <div className="flex items-center justify-between">
              <SecurityIndicator secure={result.secure} />
              <span className="text-[9px] text-[var(--text-muted)] font-mono">
                {new Date(result.timestamp).toLocaleTimeString()}
              </span>
            </div>

            {/* Sifted key length */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-secondary)]">Sifted key length</span>
              <span className="text-[10px] text-[var(--text-primary)] font-mono font-semibold">
                {result.siftedKeyLength} bits
              </span>
            </div>

            {/* QBER */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[var(--text-secondary)]">QBER</span>
                <span
                  className={`text-[10px] font-mono font-semibold ${
                    result.qber < 0.05
                      ? 'text-[var(--accent-success)]'
                      : result.qber < 0.1
                        ? 'text-[var(--accent-warning)]'
                        : 'text-[var(--accent-error)]'
                  }`}
                >
                  {(result.qber * 100).toFixed(2)}%
                </span>
              </div>
              <QBERBar value={result.qber} />
            </div>

            {/* CHSH S-value for E91 */}
            {(protocol === 'E91' || protocol === 'DI-QKD') && (
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[var(--text-secondary)]">CHSH S-value</span>
                <span className="text-[10px] text-[var(--accent-primary)] font-mono font-semibold">
                  {result.chshSValue.toFixed(4)}
                </span>
              </div>
            )}

            {/* Threshold line */}
            <div className="flex items-center justify-between text-[9px] text-[var(--text-muted)]">
              <span>Security threshold</span>
              <span className="font-mono">
                {protocol === 'BB84' || protocol === 'Satellite QKD' || protocol === 'Repeater Chains'
                  ? 'QBER < 11%'
                  : protocol === 'CV-QKD'
                    ? 'QBER < 8%'
                    : protocol === 'DI-QKD'
                      ? 'QBER < 9%, S > 2.0'
                      : 'S > 2.0'}
              </span>
            </div>
          </div>

          {/* Network topology for Quantum Network */}
          {protocol === 'Quantum Network' && (
            <div className="p-2 bg-[var(--bg-panel)] rounded-lg border border-[var(--border)]">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest font-semibold">
                Network Topology
              </span>
              <div className="mt-1 h-32">
                <NetworkTopologySVG
                  topology={params.networkTopology}
                  nodeCount={params.networkNodes}
                />
              </div>
            </div>
          )}

          {/* Key material */}
          <div className="p-2 bg-[var(--bg-panel)] rounded-lg border border-[var(--border)] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest font-semibold">
                Key Material
              </span>
              <span className="text-[9px] text-[var(--text-muted)] font-mono">
                {result.keyMaterial.length / 2} bytes
              </span>
            </div>
            <div className="bg-[var(--bg-input)] rounded p-1.5 overflow-x-auto">
              <code className="text-[9px] text-[var(--accent-primary)] font-mono whitespace-nowrap break-all leading-relaxed">
                {result.keyMaterial.match(/.{1,2}/g)?.map((byte, i) => (
                  <span key={i}>
                    {byte}
                    {(i + 1) % 4 === 0 && i + 1 < result.keyMaterial.length / 2 && (
                      <span className="text-[var(--text-muted)] mx-0.5"> </span>
                    )}
                  </span>
                ))}
              </code>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !running && (
        <div className="flex-1 flex flex-col items-center justify-center text-[var(--text-muted)] py-8">
          <span className="text-2xl mb-2 opacity-30">📡</span>
          <span className="text-[11px]">Select a protocol and run simulation</span>
          <span className="text-[10px] opacity-50 mt-0.5">
            {protocol === 'BB84' && 'BB84 quantum key distribution protocol'}
            {protocol === 'E91' && 'Ekert 91 entanglement-based protocol'}
            {protocol === 'CV-QKD' && 'Continuous variable QKD protocol'}
            {protocol === 'DI-QKD' && 'Device-independent QKD protocol'}
            {protocol === 'Satellite QKD' && 'Satellite-based quantum key distribution'}
            {protocol === 'Repeater Chains' && 'Quantum repeater chain protocol'}
            {protocol === 'Quantum Network' && 'Multi-node quantum network protocol'}
          </span>
        </div>
      )}
    </div>
  );
}
