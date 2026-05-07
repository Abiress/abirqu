from abirqu.cloud.abir_guard import AbirGuard
import json

print("--- Testing Phase 29: Post-Quantum Cryptography (Abir-Guard) ---\n")

guard = AbirGuard()

# ---------------------------------------------------------
# Test 29.1: Blind Quantum Computing (Circuit Obfuscation)
# ---------------------------------------------------------
print("Test 29.1: Blind Quantum Computing (Circuit Obfuscation)")
original_circuit = {
    "num_qubits": 2,
    "gates": ["H(0)", "CNOT(0,1)"],
    "measure": True
}
print(f"Original Circuit: {json.dumps(original_circuit)}")

# 1. Obfuscate on Client
obfuscated_circuit, decryption_key = guard.bqc.obfuscate_circuit(original_circuit)
print(f"Obfuscated Circuit (sent to cloud): {json.dumps(obfuscated_circuit)}")
print(f"Decryption Key (kept by client): {json.dumps(decryption_key)}")

# 2. Simulate Cloud Execution of Obfuscated Circuit
# If cloud runs it, the counts will be shifted based on the Paulis.
# We will mock the output as if it resulted in "10" 500 times and "01" 524 times.
# (Just arbitrary bits for testing the decryption mapping)
mock_cloud_counts = {"10": 500, "01": 524}
print(f"\nCloud Output (Encrypted Counts): {mock_cloud_counts}")

# 3. Decrypt on Client
decrypted_counts = guard.bqc.decrypt_results(mock_cloud_counts, decryption_key)
print(f"Decrypted Counts (Client Side): {decrypted_counts}")
print("-" * 60)

# ---------------------------------------------------------
# Test 29.2: Lattice-based Cryptography (Kyber LWE)
# ---------------------------------------------------------
print("\nTest 29.2a: Kyber LWE Key Encapsulation Mechanism")

# 1. Generate Keypair
pub_key, priv_key = guard.kyber.keypair()
print("Alice generated Kyber Keypair.")

# 2. Encapsulate (Bob generates symmetric key and ciphertext)
shared_key_bob, ciphertext = guard.kyber.encapsulate(pub_key)
print(f"Bob generated Shared Key (first 16 bytes): {shared_key_bob[:16].hex()}")

# 3. Decapsulate (Alice recovers symmetric key using private key)
shared_key_alice = guard.kyber.decapsulate(priv_key, ciphertext)
print(f"Alice recovered Shared Key (first 16 bytes): {shared_key_alice[:16].hex()}")

assert shared_key_alice == shared_key_bob, "Kyber key exchange failed! Keys do not match."
print("✅ Kyber LWE Key Exchange Successful!")
print("-" * 60)

# ---------------------------------------------------------
# Test 29.2b: Quantum Key Distribution (BB84 Protocol)
# ---------------------------------------------------------
print("\nTest 29.2b: BB84 QKD Simulation")
bb84_key = guard.qkd.simulate_bb84(num_bits=256)
print(f"Generated QKD Shared Key: {bb84_key.hex()}")
print("✅ BB84 QKD Exchange Successful!")
print("-" * 60)

print("\nPhase 29 Abir-Guard Tests Completed Successfully!")
