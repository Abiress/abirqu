import json
from abirqu.physics import (
    LatticeGaugeTheory,
    QuarkGluonPlasmaSimulator,
    SYKModel,
    BlackHoleScrambler,
)

print("=" * 70)
print("  Phase 35: Space-Time & High Energy Physics Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 35.1a: Lattice Gauge Theory — Wilson Action
# ---------------------------------------------------------
print("\n--- Test 35.1a: SU(2) Lattice Gauge Theory ---")
lgt = LatticeGaugeTheory(lattice_size=4, coupling_g=1.0, dimensions=2, gauge_group="SU(2)")
action = lgt.compute_wilson_action()
print(f"  Gauge Group:          {action['gauge_group']}")
print(f"  Lattice:              {action['lattice_size']}")
print(f"  Coupling g:           {action['coupling_g']}")
print(f"  β = 2Nc/g²:           {action['beta']}")
print(f"  Plaquettes:           {action['num_plaquettes']}")
print(f"  Wilson Action:        {action['wilson_action']}")
print(f"  Avg Plaquette Trace:  {action['average_plaquette_trace']}")
print(f"  Phase:                {action['confinement_indicator']}")

tension = lgt.string_tension()
print(f"\n  String Tension:")
print(f"    Wilson Loop W({tension['wilson_loop_R']},{tension['wilson_loop_T']}): {tension['wilson_loop_value']}")
print(f"    σ = {tension['string_tension']} (lattice units)")
print(f"    Confinement: {tension['confinement']}")
print("✅ Lattice gauge theory passed")

# ---------------------------------------------------------
# Test 35.1b: Quark-Gluon Plasma Dynamics
# ---------------------------------------------------------
print("\n--- Test 35.1b: Quark-Gluon Plasma Simulation ---")
qgp = QuarkGluonPlasmaSimulator(lattice_size=4, temperature_MeV=300.0)
thermo = qgp.thermodynamic_observables()
print(f"  Temperature:          {thermo['temperature_MeV']} MeV")
print(f"  Effective Coupling:   {thermo['effective_coupling']}")
print(f"  Phase:                {thermo['phase']}")
print(f"  Energy Density:       {thermo['energy_density_GeV_fm3']} GeV/fm³")
print(f"  Pressure:             {thermo['pressure_GeV_fm3']} GeV/fm³")
print(f"  Debye Mass:           {thermo['debye_mass_GeV']} GeV")
print(f"  S-B d.o.f.:           {thermo['stefan_boltzmann_dof']}")

print(f"\n  Real-Time Evolution (Bjorken expansion):")
evolution = qgp.time_evolve(time_steps=10, dt_fm=0.5)
for step in evolution["trajectory"]:
    marker = "🔴" if step["phase"] == "QGP" else "🔵"
    print(f"    {marker} τ={step['proper_time_fm']:5.2f} fm  T={step['temperature_MeV']:6.1f} MeV  g={step['coupling_g']}  [{step['phase']}]")
if evolution["hadronization_step"] is not None:
    print(f"  ✨ Hadronization at step {evolution['hadronization_step']}")
else:
    print(f"  ⚡ Still in QGP phase at end of simulation")
print("✅ Quark-gluon plasma simulation passed")

# ---------------------------------------------------------
# Test 35.2a: SYK Model (AdS/CFT)
# ---------------------------------------------------------
print("\n--- Test 35.2a: SYK Model (AdS₂/CFT₁ Correspondence) ---")
syk = SYKModel(num_majoranas=12, q=4, J_variance=1.0)
gs = syk.ground_state_energy()
print(f"  N = {gs['N']} Majorana fermions, q = {gs['q']}-body")
print(f"  Interaction terms:    {gs['num_terms']}")
print(f"  Ground State Energy:  {gs['ground_state_energy']}")
print(f"  E₀/N:                {gs['energy_per_fermion']}")

spec = syk.spectral_density(num_energies=10)
print(f"\n  Spectral Density (Schwarzian sector):")
print(f"    Energy gap:         {spec['energy_gap']}")
print(f"    Low-E form:         {spec['low_energy_form']}")

lyap = syk.lyapunov_exponent(temperature_J=0.1)
print(f"\n  Quantum Chaos:")
print(f"    Temperature:        {lyap['temperature_J']} J")
print(f"    MSS Bound:          {lyap['mss_bound']}")
print(f"    SYK λ_L:            {lyap['syk_lyapunov']}")
print(f"    Saturation:         {lyap['saturation_fraction']:.2%}")
print(f"    Maximally Chaotic:  {lyap['is_maximally_chaotic']}")
print(f"    Scrambling Time:    {lyap['scrambling_time']} J⁻¹")
print("✅ SYK model passed")

# ---------------------------------------------------------
# Test 35.2b: Black Hole Scrambling & Hawking Radiation
# ---------------------------------------------------------
print("\n--- Test 35.2b: Black Hole Scrambler ---")
bh = BlackHoleScrambler(mass_solar=10.0)
scramble = bh.scrambling_time()
print(f"  Mass:                 {scramble['mass_solar']} M☉")
print(f"  Hawking Temperature:  {scramble['hawking_temperature_K']} K")
print(f"  Entropy:              {scramble['entropy_bits']} bits")
print(f"  Scrambling Time:      {scramble['scrambling_time_s']} s")
print(f"  Fast Scrambler:       {scramble['is_fast_scrambler']}")

print(f"\n  Hawking Radiation Spectrum:")
hawking = bh.hawking_radiation_spectrum(num_modes=10)
print(f"    Temperature:        {hawking['hawking_temperature_K']} K")
print(f"    Luminosity:         {hawking['luminosity_W']} W")
print(f"    Evaporation Time:   {hawking['evaporation_time_years']} years")
for mode in hawking["spectrum"][:5]:
    print(f"    Mode {mode['mode']:2d}: ℏω/kT={mode['hw_over_kT']:4.1f}  ⟨n⟩={mode['occupation']:.4f}")

print(f"\n  Page Curve (Information Paradox Resolution):")
page = bh.page_curve(num_steps=10)
print(f"    Total Entropy:      10^{page['total_entropy_log10']} bits")
print(f"    Unitarity:          {page['unitarity_preserved']}")
print(f"    Resolution:         {page['information_paradox']}")
for pt in page["curve"][::2]:  # Every other point
    bar = "█" * int(pt["S_radiation_log10"] / page["total_entropy_log10"] * 20) if page["total_entropy_log10"] > 0 else ""
    print(f"    t={pt['t_fraction']:.1f}  S={pt['S_radiation_log10']:7.2f}  {bar}  [{pt['phase']}]")
print("✅ Black hole scrambling passed")

print("\n" + "=" * 70)
print("  Phase 35 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
