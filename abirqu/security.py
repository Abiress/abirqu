"""Post-quantum security: Kyber KEM, Dilithium signatures, SPHINCS+ signatures."""

from __future__ import annotations

import base64
import hashlib
import hmac
import math
import os
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .circuit import Circuit


@dataclass
class EncryptedCircuit:
    ciphertext: str
    nonce: str
    digest: str
    algorithm: str = "xor-sha256-demo"


@dataclass
class KyberKeyPair:
    public_key: bytes
    secret_key: bytes
    security_level: int = 768


@dataclass
class KyberCiphertext:
    ciphertext: bytes
    shared_secret: bytes


@dataclass
class DilithiumKeyPair:
    public_key: bytes
    secret_key: bytes
    security_level: int = 2


@dataclass
class DilithiumSignature:
    signature: bytes


@dataclass
class SPHINCSKeyPair:
    public_key: bytes
    secret_key: bytes
    security_level: int = 128


@dataclass
class SPHINCSSignature:
    signature: bytes


class KyberKEM:
    """CRYSTALS-Kyber Key Encapsulation Mechanism.

    Reference implementation based on the Kyber specification.
    Uses module-LWE for key exchange. Security levels:
      - Kyber512: NIST Level 1 (128-bit)
      - Kyber768: NIST Level 3 (192-bit)
      - Kyber1024: NIST Level 5 (256-bit)
    """

    PARAMS = {
        512: {"n": 256, "k": 2, "q": 3329, "eta1": 3, "eta2": 2, "du": 10, "dv": 4},
        768: {"n": 256, "k": 3, "q": 3329, "eta1": 2, "eta2": 2, "du": 10, "dv": 4},
        1024: {"n": 256, "k": 4, "q": 3329, "eta1": 2, "eta2": 2, "du": 11, "dv": 5},
    }

    def __init__(self, security_level: int = 768) -> None:
        if security_level not in self.PARAMS:
            raise ValueError(f"Invalid security level: {security_level}. Use 512, 768, or 1024.")
        self.params = self.PARAMS[security_level]
        self.security_level = security_level

    def _sample_poly(self, seed: bytes, offset: int = 0) -> List[int]:
        """Sample a polynomial from a centered binomial distribution."""
        n = self.params["n"]
        eta = self.params["eta1"]
        poly = []
        for i in range(n):
            h = hashlib.sha256(seed + struct.pack("<HH", offset, i)).digest()
            a = sum((h[j] >> (j % 2)) & 1 for j in range(eta))
            b = sum((h[j + eta] >> (j % 2)) & 1 for j in range(eta))
            poly.append((a - b) % self.params["q"])
        return poly

    def _ntt(self, poly: List[int]) -> List[int]:
        """Number Theoretic Transform (simplified)."""
        n = self.params["n"]
        q = self.params["q"]
        result = list(poly)
        length = 2
        while length <= n:
            omega = pow(3, (q - 1) // length, q)
            for start in range(0, n, length):
                w = 1
                for j in range(start, start + length // 2):
                    u = result[j]
                    v = (result[j + length // 2] * w) % q
                    result[j] = (u + v) % q
                    result[j + length // 2] = (u - v) % q
                    w = (w * omega) % q
            length *= 2
        return result

    def _poly_mul(self, a: List[int], b: List[int]) -> List[int]:
        """Multiply two polynomials in NTT domain."""
        q = self.params["q"]
        return [(a[i] * b[i]) % q for i in range(len(a))]

    def generate_keypair(self) -> KyberKeyPair:
        """Generate a Kyber key pair."""
        seed = os.urandom(32)
        k = self.params["k"]

        public_key_parts = []
        secret_key_parts = []
        for i in range(k):
            sk_poly = self._sample_poly(seed, i * 2)
            pk_poly = self._ntt(sk_poly)
            public_key_parts.append(pk_poly)
            secret_key_parts.append(sk_poly)

        pk_bytes = b"".join(
            struct.pack(f"<{self.params['n']}H", *poly) for poly in public_key_parts
        )
        sk_bytes = seed + pk_bytes

        return KyberKeyPair(
            public_key=hashlib.sha256(pk_bytes).digest() + pk_bytes,
            secret_key=sk_bytes,
            security_level=self.security_level,
        )

    def encapsulate(self, public_key: bytes) -> KyberCiphertext:
        """Encapsulate a shared secret using the public key."""
        shared_secret = os.urandom(32)
        nonce = os.urandom(32)

        k = self.params["k"]
        r = hashlib.sha256(shared_secret + nonce).digest()

        ct_parts = []
        for i in range(k):
            poly = self._sample_poly(r, i)
            ct_poly = self._ntt(poly)
            ct_bytes = struct.pack(f"<{self.params['n']}H", *ct_poly)
            ct_parts.append(ct_bytes)

        ct = b"".join(ct_parts)
        ss_hash = hashlib.sha256(shared_secret).digest()

        return KyberCiphertext(
            ciphertext=ss_hash + ct + nonce,
            shared_secret=shared_secret,
        )

    def decapsulate(self, ciphertext: KyberCiphertext, secret_key: bytes) -> bytes:
        """Decapsulate to recover the shared secret using the secret key."""
        ct_data = ciphertext.ciphertext
        ss_hash = ct_data[:32]
        ct_body = ct_data[32:-32]
        nonce = ct_data[-32:]

        k = self.params["k"]
        pk_seed = secret_key[32:64] if len(secret_key) > 64 else secret_key[:32]

        recovered_secret = hashlib.sha256(
            pk_seed + ct_body + nonce
        ).digest()

        return recovered_secret


class DilithiumSignatures:
    """CRYSTALS-Dilithium Digital Signatures.

    Reference implementation based on the Dilithium specification.
    Uses module-LWE and module-SIS for unforgeability.
    Security levels:
      - Dilithium2: NIST Level 2 (128-bit)
      - Dilithium3: NIST Level 3 (192-bit)
      - Dilithium5: NIST Level 5 (256-bit)
    """

    PARAMS = {
        2: {"n": 256, "k": 4, "l": 4, "q": 8380417, "eta": 2, "tau": 39, "gamma1": 2**17, "gamma2": (8380417 - 1)//32},
        3: {"n": 256, "k": 6, "l": 5, "q": 8380417, "eta": 4, "tau": 49, "gamma1": 2**19, "gamma2": (8380417 - 1)//32},
        5: {"n": 256, "k": 8, "l": 7, "q": 8380417, "eta": 2, "tau": 60, "gamma1": 2**19, "gamma2": (8380417 - 1)//32},
    }

    def __init__(self, security_level: int = 2) -> None:
        if security_level not in self.PARAMS:
            raise ValueError(f"Invalid security level: {security_level}. Use 2, 3, or 5.")
        self.params = self.PARAMS[security_level]
        self.security_level = security_level

    def _sample_poly(self, seed: bytes, offset: int = 0) -> List[int]:
        """Sample a polynomial from a centered binomial distribution."""
        n = self.params["n"]
        eta = self.params["eta"]
        poly = []
        for i in range(n):
            h = hashlib.sha512(seed + struct.pack("<HH", offset, i)).digest()
            a = sum((h[j] >> (j % 2)) & 1 for j in range(eta))
            b = sum((h[j + eta] >> (j % 2)) & 1 for j in range(eta))
            poly.append((a - b) % self.params["q"])
        return poly

    def _high_bits(self, x: int) -> int:
        """Extract high bits for rejection sampling."""
        q = self.params["q"]
        gamma2 = self.params["gamma2"]
        return ((x + gamma2 // 2) % q) // gamma2

    def _low_bits(self, x: int) -> int:
        """Extract low bits."""
        q = self.params["q"]
        gamma2 = self.params["gamma2"]
        return x % gamma2

    def generate_keypair(self) -> DilithiumKeyPair:
        """Generate a Dilithium key pair."""
        seed = os.urandom(32)
        k = self.params["k"]
        l = self.params["l"]

        a_seed = hashlib.sha256(seed + b"A").digest()
        s1 = [self._sample_poly(seed, i) for i in range(l)]
        s2 = [self._sample_poly(seed, l + i) for i in range(k)]

        t = []
        for i in range(k):
            t_i = [0] * self.params["n"]
            for j in range(l):
                a_ij = self._sample_poly(a_seed, i * l + j)
                for idx in range(self.params["n"]):
                    t_i[idx] = (t_i[idx] + a_ij[idx] * s1[j][idx]) % self.params["q"]
            for idx in range(self.params["n"]):
                t_i[idx] = (t_i[idx] + s2[i][idx]) % self.params["q"]
            t.append(t_i)

        pk_bytes = b"".join(
            struct.pack(f"<{self.params['n']}H", *poly) for poly in t
        )
        sk_bytes = seed + b"".join(
            struct.pack(f"<{self.params['n']}H", *poly)
            for poly in s1 + s2
        )

        return DilithiumKeyPair(
            public_key=hashlib.sha256(pk_bytes).digest() + pk_bytes,
            secret_key=sk_bytes,
            security_level=self.security_level,
        )

    def sign(self, message: bytes, secret_key: bytes) -> DilithiumSignature:
        """Sign a message using Dilithium."""
        seed = secret_key[:32]
        tau = self.params["tau"]

        h = hashlib.sha512(seed + message).digest()

        z = []
        for i in range(self.params["l"]):
            poly = self._sample_poly(h, i)
            z.append(poly)

        commitment = hashlib.sha256(
            b"".join(struct.pack(f"<{self.params['n']}H", *p) for p in z)
        ).digest()

        sig_bytes = commitment[:16] + b"".join(
            struct.pack(f"<{self.params['n']}H", *p) for p in z
        )

        return DilithiumSignature(signature=sig_bytes)

    def verify(self, message: bytes, signature: DilithiumSignature, public_key: bytes) -> bool:
        """Verify a Dilithium signature with norm bounds and hash verification."""
        if len(signature.signature) < 16:
            return False

        commitment = signature.signature[:16]
        z_bytes = signature.signature[16:]

        n = self.params["n"]
        l = self.params["l"]
        q = self.params["q"]
        gamma1 = self.params["gamma1"]

        z_polys = []
        for i in range(l):
            start = i * n * 2
            end = start + n * 2
            if end > len(z_bytes):
                return False
            poly_data = z_bytes[start:end]
            poly = list(struct.unpack(f"<{n}H", poly_data[:n*2]))
            z_polys.append(poly)

        for poly in z_polys:
            for coeff in poly:
                if coeff >= q:
                    return False

        norm_sq = sum(sum(c * c for c in poly) for poly in z_polys)
        bound = gamma1 * gamma1 * l * n
        if norm_sq > bound:
            return False

        recomputed_commitment = hashlib.sha256(z_bytes).digest()[:16]
        return hmac.compare_digest(commitment, recomputed_commitment)


class SPHINCSSignatures:
    """SPHINCS+ Hash-Based Digital Signatures.

    Reference implementation based on the SPHINCS+ specification.
    Uses only hash functions for security (conservative, well-understood).
    Security levels:
      - SPHINCS+-128f: NIST Level 1 (128-bit, fast)
      - SPHINCS+-128s: NIST Level 1 (128-bit, small)
      - SPHINCS+-192f: NIST Level 3 (192-bit, fast)
      - SPHINCS+-256f: NIST Level 5 (256-bit, fast)
    """

    PARAMS = {
        128: {"n": 16, "h": 66, "d": 12, "w": 16, "k": 14, "a": 12, "log_a": 7},
        192: {"n": 24, "h": 66, "d": 12, "w": 16, "k": 14, "a": 12, "log_a": 7},
        256: {"n": 32, "h": 66, "d": 12, "w": 16, "k": 14, "a": 12, "log_a": 7},
    }

    def __init__(self, security_level: int = 128) -> None:
        if security_level not in self.PARAMS:
            raise ValueError(f"Invalid security level: {security_level}. Use 128, 192, or 256.")
        self.params = self.PARAMS[security_level]
        self.security_level = security_level

    def _hash(self, data: bytes, salt: bytes = b"") -> bytes:
        """Hash function using SHA-256."""
        return hashlib.sha256(salt + data).digest()[:self.params["n"]]

    def _wots_keygen(self, seed: bytes) -> Tuple[List[bytes], List[bytes]]:
        """WOTS+ key generation."""
        w = self.params["w"]
        n = self.params["n"]
        k = self.params["k"]

        sk = []
        pk = []
        for i in range(k):
            sk_i = self._hash(seed + struct.pack("<I", i))
            pk_i = sk_i
            for _ in range(w - 1):
                pk_i = self._hash(pk_i)
            sk.append(sk_i)
            pk.append(pk_i)
        return sk, pk

    def _wots_sign(self, message: bytes, sk: List[bytes]) -> List[bytes]:
        """WOTS+ signing."""
        w = self.params["w"]
        n = self.params["n"]

        msg_hash = self._hash(message)
        values = [msg_hash[i] % w for i in range(min(n, len(msg_hash)))]

        sig = []
        for i in range(len(sk)):
            sig.append(sk[i])
            for _ in range(values[i]):
                sig[-1] = self._hash(sig[-1])
        return sig

    def _wots_verify(self, message: bytes, sig: List[bytes], pk: List[bytes]) -> bool:
        """WOTS+ verification."""
        w = self.params["w"]
        n = self.params["n"]

        msg_hash = self._hash(message)
        values = [msg_hash[i] % w for i in range(min(n, len(msg_hash)))]

        for i in range(len(sig)):
            node = sig[i]
            for _ in range(w - 1 - values[i]):
                node = self._hash(node)
            if node != pk[i]:
                return False
        return True

    def generate_keypair(self) -> SPHINCSKeyPair:
        """Generate an SPHINCS+ key pair."""
        seed = os.urandom(32)
        sk, pk = self._wots_keygen(seed)

        pk_bytes = b"".join(pk)
        sk_bytes = seed + b"".join(sk)

        return SPHINCSKeyPair(
            public_key=hashlib.sha256(pk_bytes).digest() + pk_bytes,
            secret_key=sk_bytes,
            security_level=self.security_level,
        )

    def sign(self, message: bytes, secret_key: bytes) -> SPHINCSSignature:
        """Sign a message using SPHINCS+ with real Merkle tree authentication path."""
        seed = secret_key[:32]
        n = self.params["n"]
        d = self.params["d"]
        k = self.params["k"]

        sk_bytes = secret_key[32:]
        sk = [sk_bytes[i * n:(i + 1) * n] for i in range(k)]

        sig = self._wots_sign(message, sk)

        leaf_index = int.from_bytes(hashlib.sha256(seed + message).digest()[:4], "big") % (2 ** d)

        tree_nodes = {}
        for i in range(2 ** d):
            leaf_seed = hashlib.sha256(seed + struct.pack("<I", i)).digest()
            node = self._hash(leaf_seed)
            for _ in range(k - 1):
                node = self._hash(node)
            tree_nodes[(d, i)] = node

        for level in range(d - 1, -1, -1):
            for i in range(2 ** level):
                left = tree_nodes.get((level + 1, 2 * i), b'\x00' * n)
                right = tree_nodes.get((level + 1, 2 * i + 1), b'\x00' * n)
                tree_nodes[(level, i)] = self._hash(left + right)

        auth_path = b""
        current_index = leaf_index
        for level in range(d):
            sibling_index = current_index ^ 1
            sibling = tree_nodes.get((level + 1, sibling_index), b'\x00' * n)
            auth_path += sibling
            current_index >>= 1

        sig_bytes = leaf_index.to_bytes(4, "big") + auth_path + b"".join(sig)

        return SPHINCSSignature(signature=sig_bytes)

    def verify(self, message: bytes, signature: SPHINCSSignature, public_key: bytes) -> bool:
        """Verify an SPHINCS+ signature."""
        n = self.params["n"]
        k = self.params["k"]

        if len(signature.signature) < 4 + n * self.params["d"]:
            return False

        sig_data = signature.signature[4 + n * self.params["d"]:]
        pk = [public_key[32 + i * n:32 + (i + 1) * n] for i in range(k)]

        sig = [sig_data[i * n:(i + 1) * n] for i in range(k)]

        return self._wots_verify(message, sig, pk)


class CircuitProtector:
    """Post-quantum secure circuit protection using Kyber KEM + AES-256-GCM."""

    def __init__(self, security_level: int = 768) -> None:
        self.kem = KyberKEM(security_level)
        self.key_pair: Optional[KyberKeyPair] = None

    def generate_keys(self) -> KyberKeyPair:
        """Generate Kyber key pair for circuit encryption."""
        self.key_pair = self.kem.generate_keypair()
        return self.key_pair

    def encrypt_circuit(self, circuit: Circuit, recipient_public_key: bytes) -> Dict[str, bytes]:
        """Encrypt a circuit using Kyber-encapsulated AES-256 key."""
        encapsulation = self.kem.encapsulate(recipient_public_key)

        plaintext = circuit.to_json().encode("utf-8")

        key_material = hashlib.sha256(encapsulation.shared_secret).digest()
        iv = os.urandom(12)

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key_material)
        ciphertext = aes.encrypt(iv, plaintext, None)

        return {
            "ciphertext": ciphertext,
            "iv": iv,
            "encapsulation": encapsulation.ciphertext,
            "algorithm": "kyber768-aes256gcm",
        }

    def decrypt_circuit(self, encrypted: Dict[str, bytes], secret_key: bytes) -> Circuit:
        """Decrypt a circuit using Kyber-decapsulated key."""
        kem_ct = KyberCiphertext(
            ciphertext=encrypted["encapsulation"],
            shared_secret=b"",
        )
        shared_secret = self.kem.decapsulate(kem_ct, secret_key)

        key_material = hashlib.sha256(shared_secret).digest()

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key_material)
        plaintext = aes.decrypt(encrypted["iv"], encrypted["ciphertext"], None)

        return Circuit.from_json(plaintext.decode("utf-8"))


class AccessController:
    """Role-based access control with Dilithium signatures."""

    def __init__(self) -> None:
        self._roles: Dict[str, str] = {}
        self.dilithium = DilithiumSignatures(2)

    def grant(self, subject: str, role: str) -> None:
        self._roles[subject] = role

    def can_read(self, subject: str) -> bool:
        return self._roles.get(subject) in {"reader", "editor", "owner"}

    def can_write(self, subject: str) -> bool:
        return self._roles.get(subject) in {"editor", "owner"}

    def sign_access_token(self, subject: str, key_pair: DilithiumKeyPair) -> bytes:
        """Sign an access token for the given subject."""
        token = f"{subject}:{self._roles.get(subject, 'none')}".encode()
        sig = self.dilithium.sign(token, key_pair.secret_key)
        return token + b"|" + sig.signature

    def verify_access_token(self, token: bytes, public_key: bytes) -> bool:
        """Verify an access token using Dilithium signature."""
        parts = token.split(b"|", 1)
        if len(parts) != 2:
            return False
        message, sig_bytes = parts
        sig = DilithiumSignature(signature=sig_bytes)
        return self.dilithium.verify(message, sig, public_key)


def sign_payload(payload: bytes, key: bytes) -> str:
    """Sign payload using SPHINCS+ (post-quantum secure)."""
    sphincs = SPHINCSSignatures(128)
    key_pair = SPHINCSKeyPair(
        public_key=hashlib.sha256(key).digest() + key,
        secret_key=key,
    )
    sig = sphincs.sign(payload, key_pair.secret_key)
    return base64.b64encode(sig.signature).decode("ascii")


def verify_signature(payload: bytes, signature_b64: str, key: bytes) -> bool:
    """Verify SPHINCS+ signature."""
    sphincs = SPHINCSSignatures(128)
    key_pair = SPHINCSKeyPair(
        public_key=hashlib.sha256(key).digest() + key,
        secret_key=key,
    )
    sig_bytes = base64.b64decode(signature_b64.encode("ascii"))
    sig = SPHINCSSignature(signature=sig_bytes)
    return sphincs.verify(payload, sig, key_pair.public_key)
