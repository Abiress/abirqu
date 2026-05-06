"""
Task 13.5 — Quantum-Classical Network Integration.

Hybrid protocols, QKD-secured channels, load balancing, monitoring.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class IntegrationMode(Enum):
    """Integration modes."""
    HYBRID = "hybrid"  # Quantum + Classical
    QUANTUM_ONLY = "quantum_only"
    CLASSICAL_ONLY = "classical_only"


@dataclass
class QKDKey:
    """QKD-generated key."""
    key_id: str
    key_material: bytes
    length_bits: int
    created_at: float = field(default_factory=time.time)
    is_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key_id': self.key_id,
            'length_bits': self.length_bits,
            'age_seconds': time.time() - self.created_at,
            'is_valid': self.is_valid,
        }


class QKDSecuredChannel:
    """
    Quantum Key Distribution secured channel.
    
    Uses QKD to establish symmetric keys for encryption.
    """
    
    def __init__(self, channel_id: str, node_a: str, node_b: str):
        self.channel_id = channel_id
        self.node_a = node_a
        self.node_b = node_b
        self.keys: List[QKDKey] = []
        self._key_counter = 0
        self.qkd_stats: Dict[str, Any] = {
            'keys_generated': 0,
            'bits_transmitted': 0,
            'qber': 0.05,  # Quantum Bit Error Rate
        }
    
    def generate_key(self, length_bits: int = 256) -> QKDKey:
        """
        Generate QKD key between nodes.
        
        Returns:
            QKDKey object
        """
        # Simulate QKD: key length affected by QBER
        actual_length = int(length_bits * (1.0 - self.qkd_stats['qber']))
        key_material = bytes(np.random.bytes(actual_length // 8))
        
        key = QKDKey(
            key_id=f"key_{self._key_counter}",
            key_material=key_material,
            length_bits=actual_length,
        )
        self._key_counter += 1
        self.keys.append(key)
        
        # Update stats
        self.qkd_stats['keys_generated'] += 1
        self.qkd_stats['bits_transmitted'] += length_bits
        
        return key
    
    def encrypt(self, data: bytes, key: Optional[QKDKey] = None) -> Tuple[bytes, str]:
        """
        Encrypt data using QKD key.
        
        Returns:
            Tuple of (encrypted_data, key_id)
        """
        if key is None:
            if not self.keys:
                key = self.generate_key()
            else:
                key = self.keys[-1]  # Use latest key
        
        # Simplified XOR encryption
        key_bytes = key.key_material
        encrypted = bytes([data[i] ^ key_bytes[i % len(key_bytes)] 
                         for i in range(len(data))])
        
        return encrypted, key.key_id
    
    def decrypt(self, encrypted_data: bytes, key_id: str) -> Optional[bytes]:
        """Decrypt data using key_id."""
        key = self._find_key(key_id)
        if key is None:
            return None
        
        key_bytes = key.key_material
        decrypted = bytes([encrypted_data[i] ^ key_bytes[i % len(key_bytes)] 
                         for i in range(len(encrypted_data))])
        
        return decrypted
    
    def _find_key(self, key_id: str) -> Optional[QKDKey]:
        """Find key by ID."""
        for key in self.keys:
            if key.key_id == key_id:
                return key
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get QKD channel statistics."""
        return {
            'channel_id': self.channel_id,
            'nodes': (self.node_a, self.node_b),
            'active_keys': len([k for k in self.keys if k.is_valid]),
            'qkd_stats': self.qkd_stats.copy(),
        }


class QuantumLoadBalancer:
    """
    Load balancer for quantum network devices.
    """
    
    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.assignment_history: List[Dict[str, Any]] = []
    
    def register_device(self, device_id: str, specs: Dict[str, Any]):
        """
        Register a quantum device.
        
        Args:
            device_id: Device identifier
            specs: Dict with 'qubits', 'fidelity', 'queue_length', etc.
        """
        self.devices[device_id] = {
            'specs': specs,
            'current_load': 0,
            'total_executions': 0,
            'average_fidelity': specs.get('fidelity', 0.99),
        }
    
    def assign_circuit(self, circuit: Dict[str, Any]) -> str:
        """
        Assign circuit to best device based on load balancing.
        
        Returns:
            Device ID to use
        """
        if not self.devices:
            raise ValueError("No devices registered")
        
        # Score each device
        scores = {}
        for dev_id, info in self.devices.items():
            score = self._calculate_score(dev_id, info, circuit)
            scores[dev_id] = score
        
        # Select best device (highest score)
        best_device = max(scores.keys(), key=lambda d: scores[d])
        
        # Update device load
        self.devices[best_device]['current_load'] += 1
        self.devices[best_device]['total_executions'] += 1
        
        self.assignment_history.append({
            'device': best_device,
            'circuit_depth': circuit.get('depth', 0),
            'timestamp': time.time(),
        })
        
        return best_device
    
    def _calculate_score(self, device_id: str, 
                          device_info: Dict, circuit: Dict) -> float:
        """Calculate device suitability score."""
        specs = device_info['specs']
        load = device_info['current_load']
        fidelity = device_info['average_fidelity']
        
        # Factors: low load, high fidelity, enough qubits
        load_score = 1.0 / (1.0 + load)
        fidelity_score = fidelity
        
        # Check qubit availability
        qubits_needed = circuit.get('num_qubits', 1)
        qubits_available = specs.get('qubits', 1)
        qubit_score = min(1.0, qubits_available / max(qubits_needed, 1))
        
        return (load_score + fidelity_score + qubit_score) / 3.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        return {
            'num_devices': len(self.devices),
            'total_executions': sum(d['total_executions'] 
                                      for d in self.devices.values()),
            'device_loads': {did: d['current_load'] 
                               for did, d in self.devices.items()},
            'device_fidelities': {did: d['average_fidelity'] 
                                    for did, d in self.devices.items()},
        }


class NetworkMonitor:
    """
    Monitor quantum-classical network performance.
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[Tuple[float, float]]] = {}  # metric -> [(timestamp, value)]
        self.alerts: List[Dict[str, Any]] = []
    
    def record_metric(self, metric_name: str, value: float):
        """Record a metric value."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append((time.time(), value))
        
        # Keep only recent history (last 1000 points)
        if len(self.metrics[metric_name]) > 1000:
            self.metrics[metric_name] = self.metrics[metric_name][-1000:]
    
    def check_thresholds(self, thresholds: Dict[str, Tuple[float, float]]) -> List[str]:
        """
        Check metrics against thresholds.
        
        Args:
            thresholds: Dict of metric -> (low_threshold, high_threshold)
            
        Returns:
            List of alert messages
        """
        new_alerts = []
        
        for metric, (low, high) in thresholds.items():
            if metric not in self.metrics or not self.metrics[metric]:
                continue
            
            latest_value = self.metrics[metric][-1][1]
            
            if latest_value < low:
                alert = f"{metric} is below threshold: {latest_value:.3f} < {low}"
                new_alerts.append(alert)
            elif latest_value > high:
                alert = f"{metric} is above threshold: {latest_value:.3f} > {high}"
                new_alerts.append(alert)
        
        self.alerts.extend([{'message': a, 'timestamp': time.time()} 
                         for a in new_alerts])
        return new_alerts
    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        summary = {}
        
        for metric, values in self.metrics.items():
            if not values:
                continue
            recent_values = [v for _, v in values[-100:]]  # Last 100
            summary[metric] = {
                'current': recent_values[-1],
                'average': float(np.mean(recent_values)),
                'min': float(np.min(recent_values)),
                'max': float(np.max(recent_values)),
                'std': float(np.std(recent_values)),
            }
        
        return {
            'metrics': summary,
            'total_data_points': sum(len(v) for v in self.metrics.values()),
            'recent_alerts': self.alerts[-10:] if self.alerts else [],
            'alert_count': len(self.alerts),
        }


class HybridNetworkManager:
    """
    Manager for hybrid quantum-classical network protocols.
    """
    
    def __init__(self, mode: IntegrationMode = IntegrationMode.HYBRID):
        self.mode = mode
        self.qkd_channels: Dict[str, QKDSecuredChannel] = {}
        self.load_balancer = QuantumLoadBalancer()
        self.monitor = NetworkMonitor()
        
    def setup_qkd_channel(self, channel_id: str, node_a: str, node_b: str) -> QKDSecuredChannel:
        """Setup QKD-secured channel."""
        channel = QKDSecuredChannel(channel_id, node_a, node_b)
        self.qkd_channels[channel_id] = channel
        return channel
    
    def send_secure_message(self, channel_id: str, 
                          message: str) -> Tuple[bytes, str]:
        """
        Send secure message over QKD channel.
        
        Returns:
            Tuple of (encrypted_message, key_id)
        """
        if channel_id not in self.qkd_channels:
            raise ValueError(f"Channel {channel_id} not found")
        
        channel = self.qkd_channels[channel_id]
        encrypted, key_id = channel.encrypt(message.encode())
        
        self.monitor.record_metric('messages_sent', 1.0)
        
        return encrypted, key_id
    
    def receive_secure_message(self, channel_id: str, 
                             encrypted: bytes, key_id: str) -> Optional[str]:
        """Receive and decrypt message."""
        if channel_id not in self.qkd_channels:
            return None
        
        channel = self.qkd_channels[channel_id]
        decrypted = channel.decrypt(encrypted, key_id)
        
        if decrypted:
            self.monitor.record_metric('messages_received', 1.0)
            return decrypted.decode()
        return None
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get overall network status."""
        qkd_stats = {cid: ch.get_stats() for cid, ch in self.qkd_channels.items()}
        
        return {
            'mode': self.mode.value,
            'qkd_channels': qkd_stats,
            'load_balancer': self.load_balancer.get_stats(),
            'monitor': self.monitor.get_summary(),
        }
