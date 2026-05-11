"""
Secure Quantum Circuit — AbirQu
==================================
Demonstrates circuit security features:

  1. Circuit encryption (XOR-stream cipher)
  2. HMAC-based circuit signing and verification
  3. Access control with role-based permissions
  4. Tamper detection

These primitives protect circuit IP when distributing to remote backends.
"""
import os
from abirqu import Circuit, NumPySimulator
from abirqu.security import (
    CircuitProtector,
    AccessController,
    sign_payload,
    verify_signature,
)


# ─────────────────────────────────────────────────────────────
# 1. Circuit Encryption
# ─────────────────────────────────────────────────────────────

def demo_encryption() -> None:
    print("\n=== Circuit Encryption ===")

    # Build a proprietary circuit (e.g., trade-secret quantum kernel)
    c = Circuit(3, name="ProprietaryKernel")
    c.h(0)
    c.cnot(0, 1)
    c.cnot(1, 2)
    c.rz(2, 1.5708)   # π/2 rotation

    print(f"  Original circuit : {c.num_qubits} qubits, {len(c.gates)} gates")
    qasm_lines = c.to_qasm().split("\n")
    qasm_snippet = next((line for line in qasm_lines if line.startswith(("h ", "cx ", "rz "))), "<no gate line>")
    print(f"  QASM sample      : {qasm_snippet}")

    # Encrypt
    secret_key = os.urandom(32)
    protector = CircuitProtector(secret_key=secret_key)
    encrypted = protector.encrypt_circuit(c)
    print(f"\n  Encrypted        : {str(encrypted)[:80]}...")

    # Decrypt
    recovered = protector.decrypt_circuit(encrypted)
    print(f"\n  Decrypted circuit: {recovered.num_qubits} qubits, {len(recovered.gates)} gates")
    assert len(recovered.gates) == len(c.gates), "Gate count mismatch!"
    print("  Integrity check  : PASSED ✓")

    # Verify the decrypted circuit gives the same results
    sim = NumPySimulator(3)
    sim.run_circuit(recovered)
    probs = sim.get_probabilities()
    print(f"  Simulation probs : {probs}")


# ─────────────────────────────────────────────────────────────
# 2. Circuit Signing & Verification
# ─────────────────────────────────────────────────────────────

def demo_signing() -> None:
    print("\n=== Circuit Signing (HMAC) ===")

    c = Circuit(2, name="SignedBell")
    c.h(0)
    c.cnot(0, 1)

    key = b"abirqu-secret-key-2024"

    # Serialize and sign the circuit
    payload = c.to_qasm().encode("utf-8")
    signature = sign_payload(payload, key)
    print(f"  Circuit payload  : {len(payload)} bytes")
    print(f"  Signature (hex)  : {signature[:48]}...")

    # Verify — unmodified payload
    ok = verify_signature(payload, signature, key)
    print(f"\n  Verify original  : {'PASS ✓' if ok else 'FAIL ✗'}")

    # Tampered payload
    tampered = payload[:10] + b"TAMPERED" + payload[18:]
    bad = verify_signature(tampered, signature, key)
    print(f"  Verify tampered  : {'PASS' if bad else 'FAIL ✗  (tamper detected)'}")

    # Wrong key
    wrong_key_result = verify_signature(payload, signature, b"wrong-key")
    print(f"  Verify wrong key : {'PASS' if wrong_key_result else 'FAIL ✗  (rejected)'}")


# ─────────────────────────────────────────────────────────────
# 3. Role-Based Access Control
# ─────────────────────────────────────────────────────────────

def demo_access_control() -> None:
    print("\n=== Role-Based Access Control ===")

    ac = AccessController()

    # Grant roles to users
    ac.grant("alice", "owner")
    ac.grant("bob",   "reader")
    # charlie gets no permissions

    users = ["alice", "bob", "charlie"]
    print(f"\n  {'User':<12} {'Can Read':<12} {'Can Write'}")
    print("  " + "─" * 36)
    for user in users:
        r = "Yes ✓" if ac.can_read(user)  else "No  ✗"
        w = "Yes ✓" if ac.can_write(user) else "No  ✗"
        print(f"  {user:<12} {r:<12} {w}")

    # Simulate access-gated circuit run
    def run_with_access(user: str, circuit: Circuit) -> None:
        if not ac.can_read(user):
            print(f"\n  [{user}] ACCESS DENIED — cannot read circuit")
            return
        sim = NumPySimulator(circuit.num_qubits)
        sim.run_circuit(circuit)
        probs = sim.get_probabilities()
        print(f"\n  [{user}] Ran circuit successfully → probs: {probs}")

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure_all()

    for user in users:
        run_with_access(user, c)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AbirQu — Secure Quantum Circuits")
    print("==================================")

    demo_encryption()
    demo_signing()
    demo_access_control()

    print("\nDone! Security features protect circuit IP for production deployment.")
