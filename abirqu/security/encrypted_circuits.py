"""Encrypted Circuits for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
from typing import Optional, Dict, Any
import base64
import hashlib

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class CircuitEncryptor:
    """Encrypts and decrypts quantum circuits for secure transmission/storage."""
    
    def __init__(self, password: Optional[bytes] = None):
        self.key = None
        self.fernet = None
        
        if password:
            self.set_password(password)
            
    def set_password(self, password: bytes):
        """Set encryption password."""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography package not installed. Install with: pip install cryptography")
            
        # Derive key from password
        salt = b'abirqu_salt'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.key = key
        self.fernet = Fernet(key)
        
    def encrypt(self, circuit) -> bytes:
        """Encrypt a quantum circuit."""
        if not self.fernet:
            raise ValueError("No encryption key set. Call set_password() first.")
            
        # Serialize circuit to QASM
        from ..core.circuit import Circuit
        if isinstance(circuit, Circuit):
            data = circuit.to_qasm().encode('utf-8')
        else:
            data = str(circuit).encode('utf-8')
            
        # Encrypt
        encrypted = self.fernet.encrypt(data)
        return encrypted
        
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt encrypted circuit data."""
        if not self.fernet:
            raise ValueError("No encryption key set.")
            
        decrypted = self.fernet.decrypt(encrypted_data)
        return decrypted.decode('utf-8')
        
    def encrypt_to_file(self, circuit, filepath: str):
        """Encrypt circuit and save to file."""
        encrypted = self.encrypt(circuit)
        with open(filepath, 'wb') as f:
            f.write(encrypted)
            
    def decrypt_from_file(self, filepath: str) -> str:
        """Decrypt circuit from file."""
        with open(filepath, 'rb') as f:
            encrypted = f.read()
        return self.decrypt(encrypted)
        
    def get_key_hash(self) -> str:
        """Get hash of encryption key for verification."""
        if not self.key:
            return ""
        return hashlib.sha256(self.key).hexdigest()[:16]
