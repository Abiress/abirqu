import hashlib
import hmac
import os
from typing import Any, Dict, Tuple

from ..cloud.abir_guard import AbirGuard


class PostQuantumSecuritySuite:
    def __init__(self) -> None:
        self.guard = AbirGuard()

    def blind_compute(self, circuit: Dict[str, Any], encrypted_counts: Dict[str, int]) -> Dict[str, Any]:
        obf, key = self.guard.bqc.obfuscate_circuit(circuit)
        dec = self.guard.bqc.decrypt_results(encrypted_counts, key)
        return {"obfuscated": obf, "decrypted_counts": dec}

    def key_exchange(self) -> Dict[str, Any]:
        pub, priv = self.guard.kyber.keypair()
        shared_bob, ciphertext = self.guard.kyber.encapsulate(pub)
        # Support either argument order for compatibility
        try:
            shared_alice = self.guard.kyber.decapsulate(priv, ciphertext)
        except Exception:
            shared_alice = self.guard.kyber.decapsulate(ciphertext, priv)
        return {"matched": shared_alice == shared_bob, "shared_key_len": len(shared_bob)}

    def qkd(self, bits: int = 256) -> Dict[str, Any]:
        key = self.guard.qkd.simulate_bb84(num_bits=bits)
        return {"key_hex": key.hex(), "key_len": len(key), "bits_requested": bits}


class SignedExecutionEnvelope:
    def __init__(self, secret: bytes = b"abirqu-pqc-demo-secret") -> None:
        self.secret = secret

    def sign(self, payload: bytes) -> str:
        return hmac.new(self.secret, payload, hashlib.sha256).hexdigest()

    def verify(self, payload: bytes, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)
