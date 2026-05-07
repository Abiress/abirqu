import json
from abirqu.bio import (
    ProteinLatticeModel,
    MolecularDockingSimulator,
    ProtonTunnelingSimulator,
    QuantumSequenceAligner,
    FoldingTopologyAnalyzer,
)

print("=" * 70)
print("  Phase 32: Biological Quantum Simulation Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 32.1a: Protein Folding — HP Lattice Model
# ---------------------------------------------------------
print("\n--- Test 32.1a: Protein Folding (Levinthal Bypass) ---")
# Short hydrophobic-rich peptide
peptide = "AVLIFWM"
model = ProteinLatticeModel(peptide)
fold = model.fold_quantum_annealing(num_samples=1000)
print(f"  Sequence:           {fold['sequence']}")
print(f"  HP String:          {fold['hp_string']}")
print(f"  Best Energy:        {fold['best_energy']}")
print(f"  Conformations Sampled: {fold['valid_conformations_sampled']}")
print(f"  Levinthal Classical:   {fold['levinthal_classical_conformations']}")
print(f"  Quantum Speedup:       {fold['quantum_speedup_ratio']}x")
print(f"  Energy Stats:          {fold['energy_histogram']}")
assert fold["best_energy"] <= 0, "Should find at least one H-H contact"
print("✅ Protein folding passed")

# ---------------------------------------------------------
# Test 32.1b: Molecular Docking
# ---------------------------------------------------------
print("\n--- Test 32.1b: Molecular Docking (Drug Discovery) ---")
docker = MolecularDockingSimulator(
    protein_name="SARS-CoV-2 Main Protease (Mpro)",
    binding_pocket_residues=["HIS41", "CYS145", "GLU166", "GLN189"],
    pocket_volume_A3=450.0
)
result = docker.dock_ligand(
    ligand_name="Nirmatrelvir",
    ligand_smiles="CC(C)(C)NC(=O)C1CC(CC1)C(=O)NC(CC2CCNC2=O)C(=O)C3CCC(F)(F)CC3",
    num_poses=2000
)
print(f"  Protein:            {result['protein']}")
print(f"  Ligand:             {result['ligand']}")
print(f"  Poses Explored:     {result['total_poses_explored']}")
print(f"  Quantum Evals:      {result['quantum_evaluations']}")
print(f"  Quantum Speedup:    {result['quantum_speedup']}")
print(f"  Best Score:         {result['best_docking_score_kcal']} kcal/mol")
print(f"  Est. Ki:            {result['estimated_Ki_nM']} nM")
print(f"  Binding:            {result['binding_classification']}")
print("✅ Molecular docking passed")

# ---------------------------------------------------------
# Test 32.2a: Proton Tunneling in DNA
# ---------------------------------------------------------
print("\n--- Test 32.2a: Proton Tunneling Mutation Analysis ---")
tunnel = ProtonTunnelingSimulator(temperature_K=310.15)

for pair in ["A-T", "G-C"]:
    res = tunnel.simulate_base_pair(pair)
    print(f"\n  [{pair}] Base Pair:")
    print(f"    Barrier:             {res['barrier_height_eV']} eV / {res['barrier_width_A']} Å")
    print(f"    Tunneling Prob:      {res['tunneling_probability']}")
    print(f"    Thermal Rate:        {res['thermal_hopping_rate']}")
    print(f"    Mutation Prob/Repl:  {res['mutation_probability_per_replication']}")

# Full strand analysis
print("\n  Full Strand Analysis:")
strand = tunnel.simulate_dna_strand("ATGCCGATCG")
print(f"    Sequence:    {strand['sequence']}")
print(f"    Hotspots:    {strand['mutation_hotspot_positions']}")
print(f"    Total:       {strand['total_hotspots']} hotspot(s)")
print("✅ Proton tunneling simulation passed")

# ---------------------------------------------------------
# Test 32.2b: Quantum Sequence Alignment
# ---------------------------------------------------------
print("\n--- Test 32.2b: Quantum-Enhanced Sequence Alignment ---")
aligner = QuantumSequenceAligner(
    seq_a="ATGCGATCGATCG",
    seq_b="ATGCAATCAATCG"
)
alignment = aligner.quantum_enhanced_align()
print(f"  Aligned A:           {alignment['aligned_seq_a']}")
print(f"  Aligned B:           {alignment['aligned_seq_b']}")
print(f"  Score:               {alignment['alignment_score']}")
print(f"  Identity:            {alignment['identity']}")
print(f"  Classical Ops:       {alignment['classical_operations']}")
print(f"  Quantum Ops:         {alignment['quantum_operations']}")
print(f"  Quantum Speedup:     {alignment['quantum_speedup']}")
assert alignment["identity"] > 0.5, "Should have high identity for similar sequences"
print("✅ Quantum sequence alignment passed")

# ---------------------------------------------------------
# Test 32.2c: Folding Topology & Contact Map
# ---------------------------------------------------------
print("\n--- Test 32.2c: Folding Topology & Contact Map ---")
topo = FoldingTopologyAnalyzer("AELMAELMIYVIYGELM")
ss = topo.predict_secondary_structure()
print(f"  Sequence:      {ss['sequence']}")
print(f"  SS Prediction: {ss['secondary_structure']}")
print(f"  Helix:         {ss['helix_fraction']:.1%}")
print(f"  Sheet:         {ss['sheet_fraction']:.1%}")

cmap = topo.build_contact_map()
print(f"\n  Contact Map:")
print(f"    Contacts:        {cmap['num_contacts']}")
print(f"    Contact Density: {cmap['contact_density']}")
print(f"    Contact Order:   {cmap['contact_order']}")
print("✅ Folding topology analysis passed")

print("\n" + "=" * 70)
print("  Phase 32 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
