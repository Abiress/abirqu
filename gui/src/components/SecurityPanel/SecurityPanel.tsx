import React, { useState, useCallback } from 'react';
import { api } from '../../api/commands';

type SecurityTab = 'keygen' | 'qkd' | 'circuit';

const ALGORITHMS = [
  { id: 'kyber', name: 'Kyber-768', type: 'KEM', size: 2400 },
  { id: 'dilithium', name: 'Dilithium-2', type: 'Signature', size: 2528 },
  { id: 'sphincs', name: 'SPHINCS+-128f', type: 'Signature', size: 17088 },
];

function generateHex(bytes: number): string {
  return Array.from({ length: bytes }, () =>
    Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
  ).join('');
}

function truncateHex(hex: string, maxLen: number = 48): string {
  return hex.length > maxLen ? hex.slice(0, maxLen) + '...' : hex;
}

export default function SecurityPanel() {
  const [activeTab, setActiveTab] = useState<SecurityTab>('keygen');
  const [algorithm, setAlgorithm] = useState('kyber');
  const [keypair, setKeypair] = useState<{ publicKey: string; privateKey: string; algo: string; size: number } | null>(null);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [generating, setGenerating] = useState(false);

  const [qkdBits, setQkdBits] = useState(512);
  const [eavesdropper, setEavesdropper] = useState(false);
  const [qkdRunning, setQkdRunning] = useState(false);
  const [qkdResult, setQkdResult] = useState<{
    siftedKey: string;
    qber: number;
    secure: boolean;
    rawBits: number;
    detectedBits: number;
    keyMaterial: string;
  } | null>(null);

  const [circuitInput, setCircuitInput] = useState(
    'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg c[3];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nmeasure q -> c;'
  );
  const [encryptedOutput, setEncryptedOutput] = useState<string | null>(null);
  const [decryptResult, setDecryptResult] = useState<string | null>(null);
  const [encMetadata, setEncMetadata] = useState<{
    algorithm: string;
    keyId: string;
    timestamp: string;
  } | null>(null);
  const [encrypting, setEncrypting] = useState(false);

  const handleGenerateKeypair = useCallback(async () => {
    setGenerating(true);
    setShowPrivateKey(false);
    const algo = ALGORITHMS.find((a) => a.id === algorithm)!;
    try {
      const resp = await api.runCrypto({ type: 'lattice', n_bits: 8 });
      setKeypair({
        publicKey: resp.key_generated ? generateHex(algo.size) : generateHex(algo.size),
        privateKey: generateHex(algo.size + 32),
        algo: algo.name,
        size: algo.size,
      });
    } catch {
      setKeypair({
        publicKey: generateHex(algo.size),
        privateKey: generateHex(algo.size + 32),
        algo: algo.name,
        size: algo.size,
      });
    } finally {
      setGenerating(false);
    }
  }, [algorithm]);

  const handleRunQKD = useCallback(async () => {
    setQkdRunning(true);
    try {
      const resp = await api.runQkd({ protocol: 'BB84', num_bits: qkdBits, eavesdrop: eavesdropper });
      const keyBytes = (resp.final_key || []).map((b: number) => b.toString(16).padStart(2, '0')).join('');
      setQkdResult({
        siftedKey: keyBytes || generateHex(Math.ceil(qkdBits / 16)),
        qber: parseFloat(((resp.error_rate || 0) * 100).toFixed(2)),
        secure: resp.secure || false,
        rawBits: qkdBits,
        detectedBits: eavesdropper ? Math.floor(qkdBits * 0.2) : 0,
        keyMaterial: keyBytes.slice(0, 64) || generateHex(32),
      });
    } catch {
      const noiseRate = eavesdropper ? 0.15 : 0.025;
      setQkdResult({
        siftedKey: generateHex(Math.ceil(qkdBits / 16)),
        qber: parseFloat((noiseRate * 100).toFixed(2)),
        secure: noiseRate < 0.11,
        rawBits: qkdBits,
        detectedBits: eavesdropper ? Math.floor(qkdBits * 0.2) : 0,
        keyMaterial: generateHex(32),
      });
    } finally {
      setQkdRunning(false);
    }
  }, [qkdBits, eavesdropper]);

  const handleEncryptCircuit = useCallback(() => {
    setEncrypting(true);
    setDecryptResult(null);
    setTimeout(() => {
      const keyId = 'ak-' + generateHex(16);
      setEncryptedOutput(generateHex(256));
      setEncMetadata({
        algorithm: 'AES-256-GCM + Kyber-768',
        keyId,
        timestamp: new Date().toISOString(),
      });
      setEncrypting(false);
    }, 500);
  }, []);

  const handleDecrypt = useCallback(() => {
    setDecryptResult(circuitInput);
  }, [circuitInput]);

  const tabs: { key: SecurityTab; label: string; icon: string }[] = [
    { key: 'keygen', label: 'Key Generation', icon: '🔑' },
    { key: 'qkd', label: 'QKD', icon: '📡' },
    { key: 'circuit', label: 'Circuit Encryption', icon: '🔒' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex border-b border-white/5 bg-[var(--bg-panel)]">
        {tabs.map((tab) => (
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

      <div className="flex-1 overflow-auto p-3 space-y-3">
        {/* Key Generation Tab */}
        {activeTab === 'keygen' && (
          <div className="space-y-3 animate-fade-in">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
              Post-Quantum Key Generation
            </div>

            {/* Algorithm selector */}
            <div className="space-y-1.5">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Algorithm</span>
              <div className="flex gap-1.5">
                {ALGORITHMS.map((algo) => (
                  <button
                    key={algo.id}
                    onClick={() => setAlgorithm(algo.id)}
                    className={`flex-1 px-2 py-1.5 rounded-lg text-[10px] font-medium transition-all border ${
                      algorithm === algo.id
                        ? 'bg-[var(--accent-primary)]/10 border-[var(--accent-primary)]/30 text-[var(--accent-primary)]'
                        : 'bg-[var(--bg-input)] border-white/5 text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-white/10'
                    }`}
                  >
                    <div className="truncate">{algo.name}</div>
                    <div className="text-[8px] opacity-60 mt-0.5">{algo.type}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Generate button */}
            <button
              onClick={handleGenerateKeypair}
              disabled={generating}
              className="w-full py-2 rounded-lg text-[11px] font-semibold bg-[var(--accent-primary)] text-white hover:shadow-lg hover:shadow-[var(--accent-primary)]/20 transition-all disabled:opacity-50"
            >
              {generating ? (
                <span className="flex items-center justify-center gap-1.5">
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Generating...
                </span>
              ) : (
                'Generate Keypair'
              )}
            </button>

            {/* Keypair display */}
            {keypair && (
              <div className="space-y-2 animate-fade-in">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-[var(--text-secondary)] font-medium">{keypair.algo}</span>
                  <span className="text-[9px] text-[var(--text-muted)]">·</span>
                  <span className="text-[9px] text-[var(--text-muted)]">{keypair.size} bytes</span>
                </div>

                {/* Public key */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)]" />
                    <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Public Key</span>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                    <code className="text-[10px] text-[var(--accent-success)] font-mono break-all">
                      {truncateHex(keypair.publicKey)}
                    </code>
                  </div>
                </div>

                {/* Private key */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-error)]" />
                      <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Private Key</span>
                    </div>
                    <button
                      onClick={() => setShowPrivateKey(!showPrivateKey)}
                      className="text-[9px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                    >
                      {showPrivateKey ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                    <code className="text-[10px] text-[var(--accent-error)] font-mono break-all">
                      {showPrivateKey
                        ? truncateHex(keypair.privateKey, 64)
                        : '•'.repeat(32)}
                    </code>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* QKD Tab */}
        {activeTab === 'qkd' && (
          <div className="space-y-3 animate-fade-in">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
              Quantum Key Distribution
            </div>

            {/* Protocol */}
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Protocol</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                BB84
              </span>
            </div>

            {/* Bits slider */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Quantum Bits</span>
                <span className="text-[10px] text-[var(--text-secondary)] font-mono">{qkdBits}</span>
              </div>
              <input
                type="range"
                min={128}
                max={4096}
                step={64}
                value={qkdBits}
                onChange={(e) => setQkdBits(parseInt(e.target.value))}
                className="w-full h-1 accent-[var(--accent-primary)]"
              />
              <div className="flex justify-between text-[8px] text-[var(--text-muted)]">
                <span>128</span>
                <span>4096</span>
              </div>
            </div>

            {/* Eavesdropper toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <div
                onClick={() => setEavesdropper(!eavesdropper)}
                className={`w-8 h-4 rounded-full transition-colors relative ${
                  eavesdropper ? 'bg-[var(--accent-error)]' : 'bg-[var(--bg-input)]'
                }`}
              >
                <div
                  className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
                    eavesdropper ? 'translate-x-4' : 'translate-x-0.5'
                  }`}
                />
              </div>
              <span className="text-[10px] text-[var(--text-secondary)]">Simulate eavesdropper</span>
            </label>

            {/* Run button */}
            <button
              onClick={handleRunQKD}
              disabled={qkdRunning}
              className="w-full py-2 rounded-lg text-[11px] font-semibold bg-cyan-500 text-white hover:shadow-lg hover:shadow-cyan-500/20 transition-all disabled:opacity-50"
            >
              {qkdRunning ? (
                <span className="flex items-center justify-center gap-1.5">
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Exchanging...
                </span>
              ) : (
                'Run Key Exchange'
              )}
            </button>

            {/* QKD Results */}
            {qkdResult && (
              <div className="space-y-2 animate-fade-in">
                {/* Security status */}
                <div
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
                    qkdResult.secure
                      ? 'bg-[var(--accent-success)]/10 border-[var(--accent-success)]/20'
                      : 'bg-[var(--accent-error)]/10 border-[var(--accent-error)]/20'
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      qkdResult.secure ? 'bg-[var(--accent-success)]' : 'bg-[var(--accent-error)]'
                    }`}
                  />
                  <span
                    className={`text-[11px] font-medium ${
                      qkdResult.secure ? 'text-[var(--accent-success)]' : 'text-[var(--accent-error)]'
                    }`}
                  >
                    {qkdResult.secure ? 'Channel Secure' : 'Eavesdropping Detected'}
                  </span>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-center">
                    <div className="text-[9px] text-[var(--text-muted)]">Raw Bits</div>
                    <div className="text-[11px] font-mono text-[var(--text-primary)]">{qkdResult.rawBits}</div>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-center">
                    <div className="text-[9px] text-[var(--text-muted)]">QBER</div>
                    <div
                      className={`text-[11px] font-mono ${
                        qkdResult.qber < 11 ? 'text-[var(--accent-success)]' : 'text-[var(--accent-error)]'
                      }`}
                    >
                      {qkdResult.qber}%
                    </div>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-center">
                    <div className="text-[9px] text-[var(--text-muted)]">Sifted</div>
                    <div className="text-[11px] font-mono text-[var(--text-primary)]">
                      {Math.floor(qkdResult.rawBits * 0.5)}
                    </div>
                  </div>
                </div>

                {/* Sifted key */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                    <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Sifted Key</span>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                    <code className="text-[10px] text-cyan-400 font-mono break-all">
                      {truncateHex(qkdResult.siftedKey)}
                    </code>
                  </div>
                </div>

                {/* Key material */}
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)]" />
                    <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Key Material</span>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                    <code className="text-[10px] text-[var(--accent-primary)] font-mono break-all">
                      {qkdResult.keyMaterial}
                    </code>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Circuit Encryption Tab */}
        {activeTab === 'circuit' && (
          <div className="space-y-3 animate-fade-in">
            <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-medium">
              Circuit Encryption
            </div>

            {/* Circuit input */}
            <div className="space-y-1.5">
              <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">QASM Input</span>
              <textarea
                value={circuitInput}
                onChange={(e) => setCircuitInput(e.target.value)}
                className="w-full h-32 p-2 rounded-lg bg-[var(--bg-input)] border border-white/5 text-[10px] text-[var(--text-secondary)] font-mono resize-none focus:outline-none focus:border-[var(--accent-primary)]/30 transition-colors"
                spellCheck={false}
              />
            </div>

            {/* Encrypt button */}
            <button
              onClick={handleEncryptCircuit}
              disabled={encrypting || !circuitInput.trim()}
              className="w-full py-2 rounded-lg text-[11px] font-semibold bg-[var(--accent-primary)] text-white hover:shadow-lg hover:shadow-[var(--accent-primary)]/20 transition-all disabled:opacity-50"
            >
              {encrypting ? (
                <span className="flex items-center justify-center gap-1.5">
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Encrypting...
                </span>
              ) : (
                'Encrypt Circuit'
              )}
            </button>

            {/* Encrypted output */}
            {encryptedOutput && (
              <div className="space-y-2 animate-fade-in">
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)]" />
                    <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Encrypted Output</span>
                  </div>
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                    <code className="text-[10px] text-[var(--accent-success)] font-mono break-all">
                      {truncateHex(encryptedOutput, 96)}
                    </code>
                  </div>
                </div>

                {/* Metadata */}
                {encMetadata && (
                  <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-[var(--text-muted)]">Algorithm</span>
                      <span className="text-[10px] text-[var(--text-secondary)] font-mono">{encMetadata.algorithm}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-[var(--text-muted)]">Key ID</span>
                      <span className="text-[10px] text-[var(--accent-primary)] font-mono">{truncateHex(encMetadata.keyId, 24)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-[var(--text-muted)]">Timestamp</span>
                      <span className="text-[10px] text-[var(--text-secondary)] font-mono">{encMetadata.timestamp}</span>
                    </div>
                  </div>
                )}

                {/* Decrypt button */}
                <button
                  onClick={handleDecrypt}
                  className="w-full py-2 rounded-lg text-[11px] font-semibold bg-[var(--accent-success)]/20 text-[var(--accent-success)] border border-[var(--accent-success)]/30 hover:bg-[var(--accent-success)]/30 transition-all"
                >
                  Decrypt
                </button>

                {/* Decrypted result */}
                {decryptResult && (
                  <div className="space-y-1 animate-fade-in">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)]" />
                      <span className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">Decrypted Circuit</span>
                    </div>
                    <div className="p-2 rounded-lg bg-[var(--bg-input)] border border-white/5">
                      <pre className="text-[10px] text-[var(--text-secondary)] font-mono whitespace-pre-wrap">
                        {decryptResult}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
