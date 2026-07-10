"""
AbirQu Headless Server (stdio mode)
Copyright 2026 Abir Maheshwari

Reads JSON requests from stdin, writes JSON responses to stdout.
Used by the Tauri GUI as a subprocess backend.
"""
import sys
import json
import time
import os

# Ensure abirqu is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abirqu.gui.server import QuantumServer


def _register_dwave_hardware(server: QuantumServer):
    """Register D-Wave backends in the hardware registry."""
    server.hardware_registry['dwave_simulated'] = {
        'name': 'D-Wave Simulated Annealing',
        'type': 'simulator',
        'num_qubits': 5000,
        'status': 'online',
        'provider': 'D-Wave',
        'max_shots': 10000,
        'gates': ['X', 'H', 'CNOT', 'CZ'],
    }
    server.hardware_registry['dwave_advantage'] = {
        'name': 'D-Wave Advantage',
        'type': 'real',
        'num_qubits': 5000,
        'status': 'online' if os.getenv('DWAVE_API_TOKEN') else 'offline',
        'provider': 'D-Wave',
        'max_shots': 1000,
        'gates': [],
    }
    server.hardware_registry['dwave_hybrid'] = {
        'name': 'D-Wave Hybrid Solver',
        'type': 'hybrid',
        'num_qubits': 10000,
        'status': 'online' if os.getenv('DWAVE_API_TOKEN') else 'offline',
        'provider': 'D-Wave',
        'max_shots': 100,
        'gates': [],
    }


def _handle_library_query():
    """Handle library template queries."""
    from abirqu.gui.circuit_library import CircuitLibraryPanel
    lib = CircuitLibraryPanel()
    return {"status": "ok", "data": lib.get_render_data()}


def _handle_get_template(template_id: str):
    from abirqu.gui.circuit_library import CircuitLibraryPanel
    lib = CircuitLibraryPanel()
    template = lib.get_template(template_id)
    if template:
        return {"status": "ok", "data": template.to_dict()}
    return {"status": "error", "error": f"Template not found: {template_id}"}


def _handle_save_template(data: dict):
    from abirqu.gui.circuit_library import CircuitLibraryPanel, CircuitTemplate
    lib = CircuitLibraryPanel()
    template = CircuitTemplate(
        template_id=data.get("template_id", f"custom_{int(time.time())}"),
        name=data.get("name", "Custom Circuit"),
        description=data.get("description", ""),
        category=data.get("category", "Custom"),
        num_qubits=data.get("num_qubits", 2),
        depth=data.get("depth", 0),
        gates=data.get("gates", []),
        tags=data.get("tags", []),
        difficulty=data.get("difficulty", "intermediate"),
    )
    lib.save_user_circuit(template)
    return {"status": "ok", "data": {"saved": True}}


def _handle_run_dwave(circuit_data: dict, shots: int):
    """Run a circuit on D-Wave simulated annealing."""
    try:
        from abirqu.backends.dwave import DWaveBackend
        backend = DWaveBackend(use_simulated=True)
        from abirqu.circuit import Circuit
        c = Circuit(circuit_data.get('num_qubits', 2))
        for gate in circuit_data.get('gates', []):
            name = gate.get('name', '')
            qubits = gate.get('qubits', [0])
            params = gate.get('params', [])
            if hasattr(c, name.lower()):
                getattr(c, name.lower())(*qubits, *params)
            else:
                c.gate(name, qubits, params)
        result = backend.run_circuit(c, shots=shots)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "error": f"D-Wave error: {e}"}


def _build_abirqu_circuit(circuit_data: dict):
    """Build an AbirQu Circuit from GUI circuit data dict."""
    from abirqu.circuit import Circuit
    c = Circuit(circuit_data.get('num_qubits', 2))
    for gate in circuit_data.get('gates', []):
        name = gate.get('name', '')
        qubits = gate.get('qubits', [0])
        params = gate.get('params', [])
        method = name.lower()
        if hasattr(c, method):
            getattr(c, method)(*qubits, *params)
        else:
            c.gate(name, qubits, params)
    return c


def _handle_convert_circuit(circuit_data: dict, target: str):
    """Convert an AbirQu circuit to another framework format."""
    try:
        c = _build_abirqu_circuit(circuit_data)
        from abirqu.converters import convert_circuit
        result = convert_circuit(c, target)
        if target == "openqasm":
            return {"status": "ok", "data": {"format": "openqasm", "code": result}}
        elif target == "quil":
            return {"status": "ok", "data": {"format": "quil", "code": result}}
        elif target == "ionq_json":
            return {"status": "ok", "data": {"format": "ionq_json", "data": result}}
        else:
            return {"status": "ok", "data": {"format": target, "description": str(type(result).__name__)}}
    except RuntimeError as e:
        return {"status": "ok", "data": {"format": target, "error": str(e), "available": True, "needs_install": True}}
    except Exception as e:
        return {"status": "error", "error": f"Conversion error: {e}"}


def _handle_run_qiskit(circuit_data: dict, shots: int):
    """Convert to Qiskit and run on Qiskit Aer simulator."""
    try:
        c = _build_abirqu_circuit(circuit_data)
        try:
            from qiskit import QuantumCircuit
            from qiskit_aer import AerSimulator
            qc = QuantumCircuit(c.num_qubits, c.num_qubits)
            for gate in c.gates:
                name = gate.name.upper()
                q = list(gate.qubits)
                p = list(gate.params)
                if name == "H": qc.h(q[0])
                elif name in ("CNOT", "CX"): qc.cx(q[0], q[1])
                elif name == "X": qc.x(q[0])
                elif name == "Y": qc.y(q[0])
                elif name == "Z": qc.z(q[0])
                elif name == "S": qc.s(q[0])
                elif name == "T": qc.t(q[0])
                elif name == "RX": qc.rx(float(p[0]), q[0])
                elif name == "RY": qc.ry(float(p[0]), q[0])
                elif name == "RZ": qc.rz(float(p[0]), q[0])
                elif name == "CZ": qc.cz(q[0], q[1])
                elif name == "SWAP": qc.swap(q[0], q[1])
                elif name == "TOFFOLI": qc.ccx(q[0], q[1], q[2])
            qc.measure_all()
            sim = AerSimulator()
            job = sim.run(qc, shots=shots)
            counts = job.result().get_counts()
            return {"status": "ok", "data": {"counts": counts, "backend": "qiskit_aer", "framework": "qiskit"}}
        except ImportError:
            from abirqu.numpy_sim import NumPySimulator
            sim = NumPySimulator()
            result = sim.run_circuit(c, shots=shots)
            return {"status": "ok", "data": {**result, "backend": "abirqu_numpy", "framework": "qiskit_fallback"}}
    except Exception as e:
        return {"status": "error", "error": f"Qiskit error: {e}"}


def _handle_run_cirq(circuit_data: dict, shots: int):
    """Convert to Cirq and run on Cirq simulator."""
    try:
        c = _build_abirqu_circuit(circuit_data)
        try:
            import cirq
            qubits = cirq.LineQubit.range(c.num_qubits)
            ops = []
            for gate in c.gates:
                name = gate.name.upper()
                q = list(gate.qubits)
                p = list(gate.params)
                if name == "H": ops.append(cirq.H(qubits[q[0]]))
                elif name in ("CNOT", "CX"): ops.append(cirq.CNOT(qubits[q[0]], qubits[q[1]]))
                elif name == "X": ops.append(cirq.X(qubits[q[0]]))
                elif name == "Y": ops.append(cirq.Y(qubits[q[0]]))
                elif name == "Z": ops.append(cirq.Z(qubits[q[0]]))
                elif name == "S": ops.append(cirq.S(qubits[q[0]]))
                elif name == "T": ops.append(cirq.T(qubits[q[0]]))
                elif name == "RX": ops.append(cirq.rx(float(p[0]))(qubits[q[0]]))
                elif name == "RY": ops.append(cirq.ry(float(p[0]))(qubits[q[0]]))
                elif name == "RZ": ops.append(cirq.rz(float(p[0]))(qubits[q[0]]))
                elif name == "CZ": ops.append(cirq.CZ(qubits[q[0]], qubits[q[1]]))
                elif name == "SWAP": ops.append(cirq.SWAP(qubits[q[0]], qubits[q[1]]))
                elif name == "TOFFOLI": ops.append(cirq.TOFFOLI(qubits[q[0]], qubits[q[1]], qubits[q[2]]))
            ops.append(cirq.measure(*qubits, key="result"))
            circuit = cirq.Circuit(ops)
            sim = cirq.Simulator()
            result = sim.run(circuit, repetitions=shots)
            counts = {}
            for k, v in result.measurements.items():
                for row in v:
                    state = ''.join(str(int(b)) for b in row)
                    counts[state] = counts.get(state, 0) + 1
            return {"status": "ok", "data": {"counts": counts, "backend": "cirq_simulator", "framework": "cirq"}}
        except ImportError:
            from abirqu.numpy_sim import NumPySimulator
            sim = NumPySimulator()
            result = sim.run_circuit(c, shots=shots)
            return {"status": "ok", "data": {**result, "backend": "abirqu_numpy", "framework": "cirq_fallback"}}
    except Exception as e:
        return {"status": "error", "error": f"Cirq error: {e}"}


def _handle_run_oqtopus(circuit_data: dict, shots: int):
    """Run via OQTOPUS cloud interface or fallback to local simulation."""
    try:
        c = _build_abirqu_circuit(circuit_data)
        try:
            from oqtopus_engine import OqtopusInterface
            oq = OqtopusInterface()
            qasm = c.to_qasm() if hasattr(c, 'to_qasm') else ""
            result = oq.execute(qasm, shots=shots)
            return {"status": "ok", "data": {"counts": result.get("counts", {}), "backend": "oqtopus_cloud", "framework": "oqtopus"}}
        except (ImportError, Exception):
            from abirqu.numpy_sim import NumPySimulator
            sim = NumPySimulator()
            result = sim.run_circuit(c, shots=shots)
            return {"status": "ok", "data": {**result, "backend": "abirqu_numpy", "framework": "oqtopus_fallback"}}
    except Exception as e:
        return {"status": "error", "error": f"OQTOPUS error: {e}"}


def _handle_export(circuit_data: dict, fmt: str, results: dict):
    """Export circuit + results to PDF/DOC/HTML/QASM/JSON."""
    try:
        c = _build_abirqu_circuit(circuit_data)
        if fmt == "qasm":
            try:
                code = c.to_qasm() if hasattr(c, 'to_qasm') else ""
                return {"status": "ok", "data": {"format": "qasm", "content": code}}
            except Exception:
                from abirqu.converters import to_openqasm
                code = to_openqasm(c)
                return {"status": "ok", "data": {"format": "qasm", "content": code}}
        elif fmt == "json":
            import json
            data = {
                "circuit": {"num_qubits": c.num_qubits, "gates": [{"name": g.name, "qubits": list(g.qubits), "params": list(g.params)} for g in c.gates]},
                "results": results or {},
                "metadata": {"format": "abirqu_json", "version": "1.2.0"}
            }
            return {"status": "ok", "data": {"format": "json", "content": json.dumps(data, indent=2)}}
        elif fmt == "html":
            counts = (results or {}).get("counts", {})
            total = sum(counts.values()) if counts else 0
            rows = ""
            for state, count in sorted(counts.items(), key=lambda x: -x[1]):
                pct = (count / total * 100) if total else 0
                rows += f"<tr><td style='font-family:monospace;padding:4px 12px;color:#8b5cf6'>{state}</td><td style='padding:4px 12px'>{count}</td><td style='padding:4px 12px'>{pct:.1f}%</td></tr>\n"
            gates_list = ", ".join(f"{g.name}({','.join(str(q) for q in g.qubits)})" for g in c.gates)
            html = f"""<!DOCTYPE html>
<html><head><title>AbirQu Research Export</title>
<style>body{{font-family:system-ui;max-width:800px;margin:40px auto;padding:20px;color:#1e293b}}
h1{{color:#7c3aed;border-bottom:2px solid #7c3aed;padding-bottom:8px}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}
th,td{{border:1px solid #e2e8f0;text-align:left;padding:6px 12px}}
th{{background:#f8fafc;font-weight:600}}
.mono{{font-family:'SF Mono',monospace;background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:13px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}}
.stat{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;text-align:center}}
.stat-val{{font-size:20px;font-weight:700;color:#7c3aed}}
.stat-label{{font-size:11px;color:#64748b;text-transform:uppercase;margin-top:4px}}
</style></head><body>
<h1>AbirQu Quantum Research Report</h1>
<p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
<div class="stats">
<div class="stat"><div class="stat-val">{c.num_qubits}</div><div class="stat-label">Qubits</div></div>
<div class="stat"><div class="stat-val">{len(c.gates)}</div><div class="stat-label">Gates</div></div>
<div class="stat"><div class="stat-val">{total}</div><div class="stat-label">Shots</div></div>
</div>
<h2>Circuit</h2>
<p><span class="mono">{gates_list or 'Empty circuit'}</span></p>
<h2>Measurement Results</h2>
<table><tr><th>State</th><th>Count</th><th>Probability</th></tr>
{rows}</table>
<h2>OpenQASM</h2>
<pre style='background:#f8fafc;padding:12px;border-radius:8px;overflow-x:auto;font-size:12px'>{c.to_qasm() if hasattr(c, 'to_qasm') else 'N/A'}</pre>
<p style='color:#64748b;font-size:11px;margin-top:32px'>Exported from AbirQu Quantum SDK v1.2.0 &mdash; aqdi.world</p>
</body></html>"""
            return {"status": "ok", "data": {"format": "html", "content": html}}
        elif fmt == "pdf_html":
            return _handle_export(circuit_data, "html", results)
        else:
            return {"status": "error", "error": f"Unknown export format: {fmt}"}
    except Exception as e:
        return {"status": "error", "error": f"Export error: {e}"}


def _handle_frameworks_info():
    """Return status of available frameworks."""
    frameworks = {}
    for name, pkg in [("qiskit", "qiskit"), ("cirq", "cirq"), ("oqtopus", "oqtopus_engine"),
                       ("braket", "amazon_braket_sdk"), ("pytket", "pytket"),
                       ("pennylane", "pennylane"), ("qiskit_aer", "qiskit_aer")]:
        try:
            __import__(pkg)
            frameworks[name] = {"installed": True, "version": "detected"}
        except ImportError:
            frameworks[name] = {"installed": False, "version": "not installed"}
    return {"status": "ok", "data": frameworks}


def main():
    server = QuantumServer()
    server.start()
    _register_dwave_hardware(server)

    # Send ready signal
    print(json.dumps({"event": "ready", "data": {}}), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "error": f"Invalid JSON: {e}"}), flush=True)
            continue

        action = request.get("action", "")

        try:
            if action == "library":
                response = _handle_library_query()
            elif action == "get_template":
                response = _handle_get_template(request.get("template_id", ""))
            elif action == "save_template":
                response = _handle_save_template(request.get("template", {}))
            elif action == "stats":
                response = {"status": "ok", "data": server.get_stats()}
            elif action == "run_dwave":
                response = _handle_run_dwave(
                    request.get("circuit", {}),
                    request.get("shots", 100),
                )
            elif action == "convert":
                response = _handle_convert_circuit(
                    request.get("circuit", {}),
                    request.get("target", "openqasm"),
                )
            elif action == "run_qiskit":
                response = _handle_run_qiskit(
                    request.get("circuit", {}),
                    request.get("shots", 1024),
                )
            elif action == "run_cirq":
                response = _handle_run_cirq(
                    request.get("circuit", {}),
                    request.get("shots", 1024),
                )
            elif action == "run_oqtopus":
                response = _handle_run_oqtopus(
                    request.get("circuit", {}),
                    request.get("shots", 1024),
                )
            elif action == "export":
                response = _handle_export(
                    request.get("circuit", {}),
                    request.get("format", "html"),
                    request.get("results", {}),
                )
            elif action == "frameworks":
                response = _handle_frameworks_info()
            else:
                response = server.handle_request(request)
        except Exception as e:
            response = {"status": "error", "error": str(e)}

        print(json.dumps(response, default=str), flush=True)


if __name__ == "__main__":
    main()
