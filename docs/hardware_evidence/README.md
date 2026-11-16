# Hardware Evidence Registry

**Policy**: Under AbirQu verification standards, a quantum hardware provider or backend adapter may only be displayed or advertised as **"verified on hardware"** if a verified result file containing the real physical job ID, backend name, execution timestamp, and measured outcome counts is committed in this directory (`docs/hardware_evidence/`).

Any provider without physical execution evidence is classified as **"untested on hardware"** (SDK adapter functional, tested against mock/simulator).

## Current Audit Registry

No verified physical hardware runs have been committed to this registry yet. All 12 supported cloud hardware adapters have been verified against local simulator/mock test suites and are classified as **Untested on hardware**.

| Provider | Backend | Evidence File | Verified Status |
|----------|---------|---------------|-----------------|
| **IBM Quantum** | `ibm_fez` / `ibm_brisbane` | *None* | Untested on Hardware (Mock Verified) |
| **D-Wave** | `dwave_advantage` | *None* | Untested on Hardware (Simulator Verified) |
| **IonQ** | `ionq_harmony` / `aria` | *None* | Untested on Hardware (API Mock Verified) |
| **Rigetti** | `aspen_m_3` | *None* | Untested on Hardware (Quil Mock Verified) |
| **Quantinuum** | `h1_1` | *None* | Untested on Hardware (Pytket Mock Verified) |
| **AWS Braket** | `sv1` / QPU | *None* | Untested on Hardware (Braket Mock Verified) |
| **Azure Quantum** | IonQ / Quantinuum QPU | *None* | Untested on Hardware (Azure Mock Verified) |
| **Google Quantum** | `weber` / `sycamore` | *None* | Untested on Hardware (Cirq Mock Verified) |
| **OQC** | `lucy` | *None* | Untested on Hardware (Mock Verified) |
| **Pasqal** | `fresnel` | *None* | Untested on Hardware (Pulser Mock Verified) |
| **QuEra** | `aquila` | *None* | Untested on Hardware (Neutral Atom Mock Verified) |
| **SpinQ** | `triangulum` | *None* | Untested on Hardware (NMR Simulator Verified) |
