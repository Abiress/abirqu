"""Security helpers for encrypted circuit workflows and signature checks."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Dict, Optional

from .circuit import Circuit


@dataclass
class EncryptedCircuit:
    ciphertext: str
    nonce: str
    digest: str
    algorithm: str = "xor-sha256-demo"


class CircuitProtector:
    """Lightweight crypto wrapper for circuit-at-rest protection.

    This keeps functionality fully local without requiring external dependencies.
    """

    def __init__(self, secret_key: Optional[bytes] = None) -> None:
        self.secret_key = secret_key or os.urandom(32)

    def _stream(self, nonce: bytes, length: int) -> bytes:
        out = b""
        counter = 0
        while len(out) < length:
            block = hashlib.sha256(self.secret_key + nonce + counter.to_bytes(8, "big")).digest()
            out += block
            counter += 1
        return out[:length]

    def encrypt_circuit(self, circuit: Circuit) -> EncryptedCircuit:
        plaintext = circuit.to_json().encode("utf-8")
        nonce = os.urandom(16)
        stream = self._stream(nonce, len(plaintext))
        cipher = bytes(a ^ b for a, b in zip(plaintext, stream))
        digest = hmac.new(self.secret_key, nonce + cipher, hashlib.sha256).hexdigest()
        return EncryptedCircuit(
            ciphertext=base64.b64encode(cipher).decode("ascii"),
            nonce=base64.b64encode(nonce).decode("ascii"),
            digest=digest,
        )

    def decrypt_circuit(self, payload: EncryptedCircuit) -> Circuit:
        nonce = base64.b64decode(payload.nonce.encode("ascii"))
        cipher = base64.b64decode(payload.ciphertext.encode("ascii"))
        expected = hmac.new(self.secret_key, nonce + cipher, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, payload.digest):
            raise ValueError("Integrity verification failed")
        stream = self._stream(nonce, len(cipher))
        plaintext = bytes(a ^ b for a, b in zip(cipher, stream)).decode("utf-8")
        return Circuit.from_json(plaintext)


class AccessController:
    def __init__(self) -> None:
        self._roles: Dict[str, str] = {}

    def grant(self, subject: str, role: str) -> None:
        self._roles[subject] = role

    def can_read(self, subject: str) -> bool:
        return self._roles.get(subject) in {"reader", "editor", "owner"}

    def can_write(self, subject: str) -> bool:
        return self._roles.get(subject) in {"editor", "owner"}


def sign_payload(payload: bytes, key: bytes) -> str:
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def verify_signature(payload: bytes, signature_hex: str, key: bytes) -> bool:
    expected = sign_payload(payload, key)
    return hmac.compare_digest(expected, signature_hex)
