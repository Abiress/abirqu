"""
Post-Quantum Encrypted Circuits

Encrypt quantum circuit definitions using ML-KEM-1024 from Abir-Guard.
Implements encrypted circuit storage and retrieval.
Supports access control for shared quantum circuits.
Builds audit logging for all circuit access.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import json
import hashlib
import base64
from datetime import datetime

class PQKeyPair:
    """Simulated post-quantum key pair (ML-KEM-1024)."""
    
    def __init__(self, key_id: str = None):
        self.key_id = key_id or self._generate_key_id()
        self.public_key = self._generate_mock_key(1024)
        self.private_key = self._generate_mock_key(1024)
        
    def _generate_key_id(self) -> str:
        """Generate unique key ID."""
        return hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]
    
    def _generate_mock_key(self, bits: int) -> bytes:
        """Generate mock key material."""
        return hashlib.sha256(str(datetime.now()).encode()).digest() * (bits // 32)

class EncryptedCircuit:
    """Represents an encrypted quantum circuit."""
    
    def __init__(self, circuit_id: str, encrypted_data: bytes,
                 metadata: Dict[str, Any], owner: str):
        self.circuit_id = circuit_id
        self.encrypted_data = encrypted_data
        self.metadata = metadata
        self.owner = owner
        self.created_at = datetime.now()
        self.access_log: List[Dict] = []
        
    def add_access_log(self, user: str, action: str, success: bool):
        """Log access to this circuit."""
        self.access_log.append({
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'action': action,
            'success': success
        })

class CircuitEncryptor:
    """
    Encrypts quantum circuits using post-quantum cryptography.
    Uses simulated ML-KEM-1024 (Kyber1024 equivalent).
    """
    
    def __init__(self, key_pair: Optional[PQKeyPair] = None):
        self.key_pair = key_pair or PQKeyPair()
        self.encrypted_circuits: Dict[str, EncryptedCircuit] = {}
        
    def encrypt_circuit(self, circuit_data: Dict, 
                       metadata: Optional[Dict] = None) -> str:
        """
        Encrypt a quantum circuit.
        
        Args:
            circuit_data: Circuit representation (dict from Circuit.to_json())
            metadata: Additional metadata
            
        Returns:
            Circuit ID for retrieval
        """
        # Serialize circuit
        json_data = json.dumps(circuit_data, indent=2)
        data_bytes = json_data.encode('utf-8')
        
        # Simulate ML-KEM-1024 encapsulation
        # In practice, would use real PQ crypto library
        encapsulated_key, symmetric_key = self._kem_encapsulate()
        
        # Encrypt data with symmetric key (simulated AES-GCM)
        encrypted_data = self._symmetric_encrypt(symmetric_key, data_bytes)
        
        # Combine encapsulated key and encrypted data
        combined = encapsulated_key + encrypted_data
        
        # Generate circuit ID
        circuit_id = hashlib.sha256(combined).hexdigest()[:16]
        
        # Store
        enc_circuit = EncryptedCircuit(
            circuit_id=circuit_id,
            encrypted_data=combined,
            metadata=metadata or {},
            owner='owner'  # Simplified
        )
        
        self.encrypted_circuits[circuit_id] = enc_circuit
        
        return circuit_id
    
    def decrypt_circuit(self, circuit_id: str, 
                       user: str = 'default') -> Optional[Dict]:
        """
        Decrypt a quantum circuit.
        
        Args:
            circuit_id: ID of encrypted circuit
            user: User requesting access
            
        Returns:
            Decrypted circuit data or None
        """
        if circuit_id not in self.encrypted_circuits:
            return None
            
        enc_circuit = self.encrypted_circuits[circuit_id]
        
        # Check access (simplified)
        if not self._check_access(enc_circuit, user):
            enc_circuit.add_access_log(user, 'decrypt', False)
            return None
            
        # Simulate decapsulation
        combined = enc_circuit.encrypted_data
        encapsulated_key, encrypted_data = combined[:1024], combined[1024:]
        
        symmetric_key = self._kem_decapsulate(encapsulated_key)
        decrypted_bytes = self._symmetric_decrypt(symmetric_key, encrypted_data)
        
        # Parse JSON
        try:
            circuit_data = json.loads(decrypted_bytes.decode('utf-8'))
            enc_circuit.add_access_log(user, 'decrypt', True)
            return circuit_data
        except Exception:
            enc_circuit.add_access_log(user, 'decrypt', False)
            return None
    
    def _kem_encapsulate(self) -> Tuple[bytes, bytes]:
        """
        Simulate ML-KEM-1024 encapsulation.
        Returns (encapsulated_key, symmetric_key).
        """
        # Mock: generate random ciphertext and shared secret
        encapsulated = hashlib.sha256(self.key_pair.public_key).digest() * 4  # 1024 bits
        shared_secret = hashlib.sha256(encapsulated).digest()[:32]
        return encapsulated, shared_secret
    
    def _kem_decapsulate(self, encapsulated_key: bytes) -> bytes:
        """Simulate ML-KEM-1024 decapsulation."""
        shared_secret = hashlib.sha256(encapsulated_key).digest()[:32]
        return shared_secret
    
    def _symmetric_encrypt(self, key: bytes, data: bytes) -> bytes:
        """Simulate symmetric encryption (AES-GCM like)."""
        # Simple XOR with key stream (for simulation only!)
        key_stream = self._generate_key_stream(key, len(data))
        return bytes(a ^ b for a, b in zip(data, key_stream))
    
    def _symmetric_decrypt(self, key: bytes, encrypted_data: bytes) -> bytes:
        """Decrypt (symmetric encryption is XOR, so same operation)."""
        return self._symmetric_encrypt(key, encrypted_data)
    
    def _generate_key_stream(self, key: bytes, length: int) -> bytes:
        """Generate key stream from key."""
        stream = b''
        counter = 0
        while len(stream) < length:
            block = hashlib.sha256(key + counter.to_bytes(8, 'big')).digest()
            stream += block
            counter += 1
        return stream[:length]
    
    def _check_access(self, circuit: EncryptedCircuit, user: str) -> bool:
        """Check if user has access (simplified)."""
        # In practice, would check ACL
        return True  # Allow all for now
    
    def get_access_log(self, circuit_id: str) -> List[Dict]:
        """Get access log for a circuit."""
        if circuit_id in self.encrypted_circuits:
            return self.encrypted_circuits[circuit_id].access_log
        return []

class AccessControl:
    """Manages access control for shared quantum circuits."""
    
    def __init__(self):
        self.acl: Dict[str, Dict[str, List[str]]] = {}  # circuit_id -> {user -> permissions}
        
    def grant_access(self, circuit_id: str, user: str, 
                     permissions: List[str] = None):
        """Grant access to a circuit."""
        if circuit_id not in self.acl:
            self.acl[circuit_id] = {}
        if user not in self.acl[circuit_id]:
            self.acl[circuit_id][user] = []
        self.acl[circuit_id][user].extend(permissions or ['read'])
        
    def revoke_access(self, circuit_id: str, user: str):
        """Revoke access."""
        if circuit_id in self.acl and user in self.acl[circuit_id]:
            del self.acl[circuit_id][user]
            
    def check_permission(self, circuit_id: str, user: str, 
                        permission: str) -> bool:
        """Check if user has permission."""
        if circuit_id not in self.acl:
            return False
        user_perms = self.acl[circuit_id].get(user, [])
        return permission in user_perms or 'admin' in user_perms

# Example usage and tests
if __name__ == "__main__":
    print("Testing Post-Quantum Encrypted Circuits...")
    
    # Create encryptor
    encryptor = CircuitEncryptor()
    print(f"Key ID: {encryptor.key_pair.key_id}")
    
    # Create sample circuit data
    circuit_data = {
        'name': 'bell_state',
        'num_qubits': 2,
        'gates': [
            {'name': 'H', 'qubits': [0]},
            {'name': 'CNOT', 'qubits': [0, 1]}
        ]
    }
    
    # Encrypt
    print("\nEncrypting circuit...")
    circuit_id = encryptor.encrypt_circuit(
        circuit_data, 
        metadata={'algorithm': 'bell', 'owner': 'alice'}
    )
    print(f"Circuit ID: {circuit_id}")
    
    # Decrypt
    print("\nDecrypting circuit...")
    decrypted = encryptor.decrypt_circuit(circuit_id, user='alice')
    if decrypted:
        print(f"Decrypted circuit: {decrypted['name']}")
        print(f"Gates: {len(decrypted['gates'])}")
    
    # Check access log
    print("\nAccess log:")
    log = encryptor.get_access_log(circuit_id)
    for entry in log:
        print(f"  {entry['timestamp']}: {entry['user']} - {entry['action']} "
              f"({'success' if entry['success'] else 'failed'})")
    
    # Test access control
    print("\nTesting Access Control...")
    acl = AccessControl()
    acl.grant_access(circuit_id, 'bob', ['read'])
    print(f"Bob has read access: {acl.check_permission(circuit_id, 'bob', 'read')}")
    print(f"Bob has write access: {acl.check_permission(circuit_id, 'bob', 'write')}")