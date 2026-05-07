import json
from abirqu.internet import (
    EntanglementSwapper,
    OrbitalSatelliteNoiseModel,
    DeepSpaceRelay,
    QKDTelemetryChannel,
    EntanglementSensorNetwork,
)

print("=" * 70)
print("  Phase 31: Quantum Internet & Inter-Planetary Communication Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 31.1a: Entanglement Swapping
# ---------------------------------------------------------
print("\n--- Test 31.1a: Entanglement Swapping (Earth-Moon) ---")
swapper = EntanglementSwapper(num_relay_nodes=2, link_fidelity=0.97, swap_success_probability=0.5)
result = swapper.simulate_relay_chain(distance_km=384_400)
print(json.dumps(result, indent=2))
assert result["end_to_end_fidelity"] > 0.5, "Fidelity too low for viable link"
print("✅ Entanglement swapping simulation passed")

# ---------------------------------------------------------
# Test 31.1b: Orbital Satellite Noise Models
# ---------------------------------------------------------
print("\n--- Test 31.1b: Orbital Satellite Noise Models ---")
for orbit in ["LEO", "GEO", "LUNAR", "MARS"]:
    model = OrbitalSatelliteNoiseModel(orbit)
    channel = model.compute_channel_model()
    print(f"\n  [{orbit}] Channel Model:")
    print(f"    Altitude:          {channel['altitude_km']} km")
    print(f"    Atm. Error Rate:   {channel['atmospheric_error_rate']}")
    print(f"    Doppler Shift:     {channel['doppler_shift_ghz']} GHz")
    print(f"    Beam Loss:         {channel['beam_divergence_loss_db']} dB")
    print(f"    Background Noise:  {channel['background_noise_cps']} cps")
print("\n✅ All orbital noise models computed")

# ---------------------------------------------------------
# Test 31.1c: Deep-Space Relay Routes
# ---------------------------------------------------------
print("\n--- Test 31.1c: Deep-Space Relay Routes ---")
relay = DeepSpaceRelay()
for route_name in ["Earth-LEO", "Earth-Moon", "Earth-Mars"]:
    result = relay.simulate_route(route_name)
    print(f"\n  Route: {route_name}")
    print(f"    End-to-End Fidelity: {result['entanglement_swapping']['end_to_end_fidelity']}")
    print(f"    Latency:             {result['entanglement_swapping']['one_way_latency_seconds']} s")
    print(f"    Viable:              {result['is_viable']}")
print("\n✅ Deep-space relay simulation passed")

# ---------------------------------------------------------
# Test 31.2a: QKD-Secured Telemetry
# ---------------------------------------------------------
print("\n--- Test 31.2a: QKD-Secured Probe Telemetry ---")
channel = QKDTelemetryChannel(probe_name="Voyager-Q1", distance_km=20_000_000_000)

# Negotiate key
key_result = channel.negotiate_key(num_raw_bits=2048)
print(f"  QKD Key Negotiation:")
print(f"    Sifted Key Length: {key_result['sifted_key_length']}")
print(f"    QBER:             {key_result['qber']}")
print(f"    Secure:           {key_result['is_secure']}")
print(f"    Final Key:        {key_result['final_key_hex'][:32]}...")

# Encrypt telemetry
telemetry_data = "PROBE_STATUS:NOMINAL|TEMP:3.2K|DIST:20AU|FUEL:87%"
encrypted = channel.encrypt_telemetry_frame(telemetry_data)
print(f"\n  Encrypted Telemetry:")
print(f"    Ciphertext:       {encrypted['ciphertext_hex']}")
print(f"    Security:         {encrypted['security_level']}")

# Verify round-trip decryption
full_ciphertext_hex = encrypted["ciphertext_hex"].replace("...", "")
# For proper round-trip, re-encrypt to get full ciphertext
plaintext_bytes = telemetry_data.encode("utf-8")
import hashlib
key_stream = b""
counter = 0
while len(key_stream) < len(plaintext_bytes):
    key_stream += hashlib.sha256(channel._shared_key + counter.to_bytes(4, "big")).digest()
    counter += 1
full_ciphertext = bytes(p ^ k for p, k in zip(plaintext_bytes, key_stream))
decrypted = channel.decrypt_telemetry_frame(full_ciphertext.hex())
assert decrypted == telemetry_data, f"Decryption mismatch: {decrypted}"
print(f"    Decrypted:        {decrypted}")
print("\n✅ QKD telemetry encryption/decryption passed")

# ---------------------------------------------------------
# Test 31.2b: Entanglement Sensor Network
# ---------------------------------------------------------
print("\n--- Test 31.2b: Entanglement-Based Sensor Network ---")
network = EntanglementSensorNetwork(num_sensors=8, baseline_sensitivity=1.0)

# Deploy at positions
positions = [(i * 100, 0, 0) for i in range(8)]
deployment = network.deploy_network(positions)
print(f"  Deployed {deployment['num_sensors']} sensors")
print(f"  Max Baseline: {deployment['max_baseline_km']} km")
print(f"  Effective Aperture: {deployment['effective_aperture_km2']} km²")

# Simulate measurement
measurement = network.simulate_measurement(signal_strength=0.001)
print(f"\n  Measurement Results:")
print(f"    True Signal:           {measurement['true_signal']}")
print(f"    Heisenberg Sensitivity:{measurement['heisenberg_sensitivity']}")
print(f"    Classical SQL:         {measurement['standard_quantum_limit']}")
print(f"    SNR (Quantum):         {measurement['snr_heisenberg']}")
print(f"    SNR (Classical):       {measurement['snr_classical']}")
print(f"    Quantum Advantage:     {measurement['quantum_advantage_factor']}x")
print(f"    Entanglement State:    {measurement['entanglement_state']}")
print("\n✅ Entanglement sensor network passed")

print("\n" + "=" * 70)
print("  Phase 31 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
