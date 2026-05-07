
class MockKyber:
    def keypair(self): return (b"pub_key", b"priv_key")
    def encapsulate(self, pub_key): return (b"12345678901234567890123456789012", b"ciphertext")
    def decapsulate(self, ciphertext, priv_key): return b"12345678901234567890123456789012"
class MockDilithium:
    def keypair(self): return ("pub_key", "priv_key")
    def sign(self, msg, priv_key): return b"signature"
    def verify(self, msg, sig, pub_key): return True
class MockSphincs:
    def keypair(self): return ("pub_key", "priv_key")
    def sign(self, msg, priv_key): return "signature"
    def verify(self, msg, sig, pub_key): return True
class MockBQC:
    def obfuscate_circuit(self, circuit): return ("obfuscated_circuit_str", "decryption_key_str")
    def decrypt_results(self, counts, key): return {"00": 500, "11": 524}
class MockQKD:
    def simulate_bb84(self, num_bits): return b"12345678901234567890123456789012"
class AbirGuard:
    def __init__(self, *args, **kwargs):
        self.bqc = MockBQC()
        self.kyber = MockKyber()
        self.dilithium = MockDilithium()
        self.sphincs = MockSphincs()
        self.qkd = MockQKD()
    def check_permissions(self, *args, **kwargs): return True
    def verify_quantum_firmware(self, firmware_hex): return {"status": "Verified", "algorithm": "SPHINCS+"}
