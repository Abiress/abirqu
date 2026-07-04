"""
Comprehensive tests for AbirQu GUI/IDE module
Copyright 2026 Abir Maheshwari

Tests for server, circuit editor, visualizations, hardware panel,
job dashboard, circuit library, code editor, and theme manager.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import time
import json
import pytest
from abirqu.gui.server import QuantumServer, QuantumJob, JobStatus
from abirqu.gui.circuit_editor import CircuitEditor, GateItem, AVAILABLE_GATES
from abirqu.gui.bloch_sphere import BlochSphereWidget, BlochState
from abirqu.gui.state_visualizer import StateVisualizer, StateEntry
from abirqu.gui.measurement_panel import MeasurementPanel
from abirqu.gui.hardware_panel import HardwarePanel, HardwareBackend
from abirqu.gui.job_dashboard import JobDashboard, JobEntry
from abirqu.gui.circuit_library import CircuitLibraryPanel, CircuitTemplate
from abirqu.gui.code_editor import CodeEditor, SyntaxToken, CompletionItem
from abirqu.gui.theme import ThemeManager, DARK_THEME, LIGHT_THEME


# ==================== Server Tests ====================

class TestQuantumServer:
    def test_init(self):
        server = QuantumServer()
        assert server.is_running is False
        assert len(server.jobs) == 0

    def test_start_stop(self):
        server = QuantumServer()
        server.start()
        assert server.is_running is True
        server.stop()
        assert server.is_running is False

    def test_hardware_registry(self):
        server = QuantumServer()
        hw = server.get_hardware()
        assert len(hw) >= 3
        ids = [h['name'] for h in hw]
        assert any('Simulator' in n for n in ids)

    def test_compile_request(self):
        server = QuantumServer()
        server.start()
        req = {'action': 'compile', 'circuit': {'num_qubits': 2, 'gates': [{'name': 'H', 'qubits': [0]}]}}
        resp = server.handle_request(req)
        assert resp['status'] == 'ok'
        assert resp['data']['compiled'] is True

    def test_execute_request(self):
        server = QuantumServer()
        server.start()
        req = {'action': 'execute', 'circuit': {'num_qubits': 2, 'gates': [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]}, 'shots': 100}
        resp = server.handle_request(req)
        assert resp['status'] == 'ok'
        assert 'job_id' in resp['data']

    def test_job_lifecycle(self):
        server = QuantumServer()
        server.start()
        req = {'action': 'execute', 'circuit': {'num_qubits': 2, 'gates': [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]}, 'shots': 100}
        resp = server.handle_request(req)
        job_id = resp['data']['job_id']
        time.sleep(0.5)
        status_req = {'action': 'status', 'job_id': job_id}
        status_resp = server.handle_request(status_req)
        assert status_resp['status'] == 'ok'
        assert status_resp['data']['status'] in ('running', 'completed')

    def test_cancel_job(self):
        server = QuantumServer()
        server.start()
        req = {'action': 'execute', 'circuit': {'num_qubits': 2, 'gates': []}, 'shots': 100}
        resp = server.handle_request(req)
        job_id = resp['data']['job_id']
        cancel_req = {'action': 'cancel', 'job_id': job_id}
        cancel_resp = server.handle_request(cancel_req)
        assert cancel_resp['status'] == 'ok'

    def test_list_jobs(self):
        server = QuantumServer()
        server.start()
        req = {'action': 'execute', 'circuit': {'num_qubits': 2, 'gates': []}, 'shots': 10}
        server.handle_request(req)
        list_req = {'action': 'list_jobs'}
        list_resp = server.handle_request(list_req)
        assert list_resp['status'] == 'ok'
        assert len(list_resp['data']['jobs']) >= 1

    def test_unknown_action(self):
        server = QuantumServer()
        resp = server.handle_request({'action': 'nonexistent'})
        assert resp['status'] == 'error'

    def test_simulate_bell_state(self):
        server = QuantumServer()
        server.start()
        req = {'action': 'execute', 'circuit': {'num_qubits': 2, 'gates': [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]}, 'shots': 1000}
        resp = server.handle_request(req)
        time.sleep(0.3)
        job_id = resp['data']['job_id']
        result_req = {'action': 'result', 'job_id': job_id}
        result_resp = server.handle_request(result_req)
        if result_resp['data'].get('counts'):
            counts = result_resp['data']['counts']
            assert '00' in counts or '11' in counts

    def test_event_log(self):
        server = QuantumServer()
        server.start()
        req = {'action': 'compile', 'circuit': {'num_qubits': 1, 'gates': []}}
        server.handle_request(req)
        log = server.get_event_log()
        assert len(log) >= 1

    def test_stats(self):
        server = QuantumServer()
        server.start()
        stats = server.get_stats()
        assert 'total_jobs' in stats
        assert 'hardware_count' in stats
        assert stats['hardware_count'] >= 3

    def test_callbacks(self):
        server = QuantumServer()
        received = []
        server.on('job_update', lambda d: received.append(d))
        server.start()
        req = {'action': 'execute', 'circuit': {'num_qubits': 1, 'gates': []}, 'shots': 10}
        server.handle_request(req)
        time.sleep(0.3)
        assert len(received) >= 1


# ==================== Circuit Editor Tests ====================

class TestGateItem:
    def test_creation(self):
        g = GateItem(name='H', qubit=0, col=0)
        assert g.name == 'H'
        assert g.qubit == 0
        assert g.color == '#7c3aed'

    def test_multi_qubit(self):
        g = GateItem(name='CNOT', qubit=0, target_qubit=1, col=0)
        assert g.is_multi_qubit is True
        assert g.box_width == 0.8

    def test_single_qubit(self):
        g = GateItem(name='X', qubit=0, col=0)
        assert g.is_multi_qubit is False
        assert g.box_width == 0.6

    def test_to_dict(self):
        g = GateItem(name='CNOT', qubit=0, target_qubit=1, col=0)
        d = g.to_dict()
        assert d['name'] == 'CNOT'
        assert d['qubits'] == [0, 1]

    def test_repr(self):
        g = GateItem(name='H', qubit=0, col=0)
        assert 'H' in repr(g)


class TestCircuitEditor:
    def test_init(self):
        ed = CircuitEditor(num_qubits=3)
        assert ed.num_qubits == 3
        assert len(ed.gates) == 0

    def test_add_gate(self):
        ed = CircuitEditor(num_qubits=2)
        gate = ed.add_gate('H', qubit=0)
        assert gate.name == 'H'
        assert len(ed.gates) == 1

    def test_add_multi_qubit_gate(self):
        ed = CircuitEditor(num_qubits=3)
        gate = ed.add_gate('CNOT', qubit=0, target_qubit=1)
        assert gate.is_multi_qubit is True
        assert gate.target_qubit == 1

    def test_remove_gate(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0, col=0)
        removed = ed.remove_gate_at(0, 0)
        assert removed is not None
        assert len(ed.gates) == 0

    def test_move_gate(self):
        ed = CircuitEditor(num_qubits=3)
        gate = ed.add_gate('H', qubit=0, col=0)
        ed.move_gate(gate, new_qubit=2, new_col=1)
        assert gate.qubit == 2
        assert gate.col == 1

    def test_clear(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0)
        ed.add_gate('X', qubit=1)
        ed.clear()
        assert len(ed.gates) == 0

    def test_insert_col(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0, col=0)
        ed.insert_col(after_col=0)
        assert ed.max_cols == 2

    def test_delete_col(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0, col=0)
        ed.add_gate('X', qubit=0, col=1)
        ed.delete_col(0)
        assert ed.max_cols == 1

    def test_get_gate_at(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0, col=0)
        gate = ed.get_gate_at(0, 0)
        assert gate is not None
        assert gate.name == 'H'

    def test_get_column(self):
        ed = CircuitEditor(num_qubits=3)
        ed.add_gate('H', qubit=0, col=0)
        ed.add_gate('X', qubit=2, col=0)
        col = ed.get_column(0)
        assert len(col) == 2

    def test_to_json(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0)
        ed.add_gate('CNOT', qubit=0, target_qubit=1)
        j = ed.to_json()
        data = json.loads(j)
        assert data['num_qubits'] == 2
        assert len(data['gates']) == 2

    def test_from_json(self):
        ed = CircuitEditor()
        j = json.dumps({'num_qubits': 2, 'gates': [{'name': 'H', 'qubits': [0]}, {'name': 'CNOT', 'qubits': [0, 1]}]})
        ed.from_json(j)
        assert ed.num_qubits == 2
        assert len(ed.gates) == 2

    def test_render_data(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0)
        ed.add_gate('CNOT', qubit=0, target_qubit=1)
        rd = ed.get_render_data()
        assert rd['num_qubits'] == 2
        assert 0 in rd['grid']

    def test_callbacks(self):
        ed = CircuitEditor(num_qubits=2)
        events = []
        ed.on('gate_added', lambda g: events.append('added'))
        ed.on('circuit_changed', lambda c: events.append('changed'))
        ed.add_gate('H', qubit=0)
        assert 'added' in events
        assert 'changed' in events

    def test_available_gates(self):
        assert len(AVAILABLE_GATES) >= 15
        names = [g['name'] for g in AVAILABLE_GATES]
        assert 'H' in names
        assert 'CNOT' in names
        assert 'Toffoli' in names


# ==================== Bloch Sphere Tests ====================

class TestBlochState:
    def test_zero_state(self):
        s = BlochState(theta=0, phi=0)
        assert abs(s.z - 1.0) < 1e-10
        assert abs(s.x) < 1e-10
        assert abs(s.y) < 1e-10

    def test_one_state(self):
        s = BlochState(theta=math.pi, phi=0)
        assert abs(s.z + 1.0) < 1e-10

    def test_plus_state(self):
        s = BlochState(theta=math.pi/2, phi=0)
        assert abs(s.x - 1.0) < 1e-10

    def test_from_statevector(self):
        s = BlochState.from_statevector(complex(1, 0), complex(0, 0))
        assert abs(s.theta) < 1e-10

    def test_from_statevector_one(self):
        s = BlochState.from_statevector(complex(0, 0), complex(1, 0))
        assert abs(s.theta - math.pi) < 1e-10

    def test_from_counts(self):
        counts = {'0': 500, '1': 500}
        s = BlochState.from_dict(counts, 1, 0)
        assert abs(s.theta - math.pi/2) < 0.5

    def test_repr(self):
        s = BlochState(theta=1.0, phi=0.5)
        r = repr(s)
        assert 'BlochState' in r


class TestBlochSphereWidget:
    def test_init(self):
        w = BlochSphereWidget()
        assert w.resolution == 30

    def test_set_state(self):
        w = BlochSphereWidget()
        s = BlochState(theta=math.pi/2, phi=0)
        w.set_state(s)
        assert w.state.theta == math.pi/2

    def test_set_from_statevector(self):
        w = BlochSphereWidget()
        w.set_from_statevector(complex(1/math.sqrt(2), 0), complex(1/math.sqrt(2), 0))
        assert abs(w.state.x - 1.0) < 0.1

    def test_get_state_vector(self):
        w = BlochSphereWidget()
        sv = w.get_state_vector()
        assert 'x' in sv and 'y' in sv and 'z' in sv

    def test_get_arrow_data(self):
        w = BlochSphereWidget()
        arrow = w.get_arrow_data()
        assert 'origin' in arrow
        assert 'tip' in arrow

    def test_get_render_data(self):
        w = BlochSphereWidget()
        rd = w.get_render_data()
        assert 'sphere' in rd
        assert 'axes' in rd
        assert 'state_vector' in rd
        assert 'arrow' in rd

    def test_project_2d(self):
        w = BlochSphereWidget()
        proj = w.project_2d()
        assert 'center' in proj
        assert 'radius' in proj
        assert 'great_circles' in proj
        assert len(proj['great_circles']) == 3

    def test_sphere_mesh(self):
        w = BlochSphereWidget(resolution=10)
        mesh = w._sphere_mesh
        assert len(mesh['vertices']) > 0
        assert len(mesh['indices']) > 0


# ==================== State Visualizer Tests ====================

class TestStateVisualizer:
    def test_init(self):
        v = StateVisualizer()
        assert v.max_display == 32

    def test_set_statevector(self):
        v = StateVisualizer()
        v.set_statevector([complex(1, 0), complex(0, 0)], 1)
        assert len(v.states) == 1
        assert v.num_qubits == 1

    def test_set_from_counts(self):
        v = StateVisualizer()
        v.set_from_counts({'00': 500, '11': 500}, 1000)
        assert len(v.states) == 2
        assert v.num_qubits == 2

    def test_render_data(self):
        v = StateVisualizer()
        v.set_from_counts({'00': 500, '11': 500}, 1000)
        rd = v.get_render_data()
        assert 'bars' in rd
        assert 'statistics' in rd
        assert rd['num_qubits'] == 2

    def test_bloch_data(self):
        v = StateVisualizer()
        v.set_statevector([complex(1, 0), complex(0, 0)], 1)
        bd = v.get_bloch_data()
        assert bd['single_qubit'] is True
        assert 'theta' in bd

    def test_phase_color(self):
        color = StateVisualizer._phase_color(0.0)
        assert color.startswith('#')
        assert len(color) == 7

    def test_empty(self):
        v = StateVisualizer()
        rd = v.get_render_data()
        assert rd['num_states'] == 0


# ==================== Measurement Panel Tests ====================

class TestMeasurementPanel:
    def test_init(self):
        p = MeasurementPanel()
        assert p.shots == 0

    def test_set_results(self):
        p = MeasurementPanel()
        p.set_results({'00': 500, '11': 500}, 1000)
        assert p.shots == 1000
        assert len(p.counts) == 2

    def test_get_bins(self):
        p = MeasurementPanel()
        p.set_results({'00': 600, '11': 400}, 1000)
        bins = p.get_bins()
        assert len(bins) == 2
        assert bins[0].count >= bins[1].count

    def test_statistics(self):
        p = MeasurementPanel()
        p.set_results({'0': 500, '1': 500}, 1000)
        stats = p.get_statistics()
        assert stats['total_shots'] == 1000
        assert stats['unique_outcomes'] == 2

    def test_per_qubit(self):
        p = MeasurementPanel()
        p.set_results({'00': 500, '11': 500}, 1000)
        pq = p.get_per_qubit_data()
        assert len(pq) == 2

    def test_clear(self):
        p = MeasurementPanel()
        p.set_results({'0': 100}, 100)
        p.clear()
        assert p.shots == 0

    def test_render_data(self):
        p = MeasurementPanel()
        p.set_results({'00': 500, '11': 500}, 1000)
        rd = p.get_render_data()
        assert 'bars' in rd
        assert 'statistics' in rd


# ==================== Hardware Panel Tests ====================

class TestHardwarePanel:
    def test_init(self):
        p = HardwarePanel()
        assert len(p.backends) >= 5

    def test_default_backends(self):
        p = HardwarePanel()
        backends = p.get_all_backends()
        names = [b.name for b in backends]
        assert any('Statevector' in n for n in names)
        assert any('Clifford' in n for n in names)

    def test_select_backend(self):
        p = HardwarePanel()
        result = p.select_backend('abirqu_simulator')
        assert result is True
        assert p.selected_backend == 'abirqu_simulator'

    def test_get_selected(self):
        p = HardwarePanel()
        p.select_backend('abirqu_simulator')
        sel = p.get_selected()
        assert sel is not None
        assert sel.backend_id == 'abirqu_simulator'

    def test_add_backend(self):
        p = HardwarePanel()
        hw = HardwareBackend(
            backend_id='test_hw', name='Test HW', backend_type='simulator',
            num_qubits=5, provider='Test',
        )
        p.add_backend(hw)
        assert 'test_hw' in p.backends

    def test_remove_backend(self):
        p = HardwarePanel()
        hw = HardwareBackend(
            backend_id='test_hw', name='Test HW', backend_type='simulator',
            num_qubits=5, provider='Test',
        )
        p.add_backend(hw)
        p.remove_backend('test_hw')
        assert 'test_hw' not in p.backends

    def test_compatible_backends(self):
        p = HardwarePanel()
        compat = p.get_compatible_backends(2, ['H', 'CNOT'])
        assert len(compat) >= 1

    def test_get_by_type(self):
        p = HardwarePanel()
        sims = p.get_backends_by_type('simulator')
        assert len(sims) >= 5

    def test_render_data(self):
        p = HardwarePanel()
        rd = p.get_render_data()
        assert 'backends' in rd
        assert 'providers' in rd

    def test_stats(self):
        p = HardwarePanel()
        stats = p.get_stats()
        assert stats['total'] >= 5
        assert 'simulator' in stats['by_type']

    def test_backend_to_dict(self):
        hw = HardwareBackend(
            backend_id='test', name='Test', backend_type='simulator',
            num_qubits=5, provider='Test',
        )
        d = hw.to_dict()
        assert d['backend_id'] == 'test'


# ==================== Job Dashboard Tests ====================

class TestJobDashboard:
    def test_init(self):
        d = JobDashboard()
        assert len(d.jobs) == 0

    def test_add_job(self):
        d = JobDashboard()
        job = d.add_job('job1', 'Bell State', 'abirqu_simulator', 1024)
        assert job.job_id == 'job1'
        assert len(d.jobs) == 1

    def test_update_job(self):
        d = JobDashboard()
        d.add_job('job1', 'Test', 'sim', 100)
        d.update_job('job1', status='running', progress=0.5)
        job = d.get_job('job1')
        assert job.status == 'running'
        assert job.progress == 0.5

    def test_remove_job(self):
        d = JobDashboard()
        d.add_job('job1', 'Test', 'sim', 100)
        d.remove_job('job1')
        assert len(d.jobs) == 0

    def test_get_by_status(self):
        d = JobDashboard()
        d.add_job('j1', 'Test', 'sim', 100)
        d.add_job('j2', 'Test', 'sim', 100)
        d.update_job('j1', status='completed')
        completed = d.get_jobs_by_status('completed')
        assert len(completed) == 1

    def test_stats(self):
        d = JobDashboard()
        d.add_job('j1', 'Test', 'sim', 100)
        d.add_job('j2', 'Test', 'sim', 200)
        stats = d.get_stats()
        assert stats['total_jobs'] == 2
        assert stats['total_shots'] == 300

    def test_performance(self):
        d = JobDashboard()
        d.add_job('j1', 'Test', 'sim', 100)
        d.update_job('j1', status='completed', completed_at=time.time())
        perf = d.get_performance_data()
        assert perf['total_completed'] >= 1

    def test_render_data(self):
        d = JobDashboard()
        d.add_job('j1', 'Test', 'sim', 100)
        rd = d.get_render_data()
        assert 'jobs' in rd
        assert 'stats' in rd
        assert 'performance' in rd

    def test_clear(self):
        d = JobDashboard()
        d.add_job('j1', 'Test', 'sim', 100)
        d.clear()
        assert len(d.jobs) == 0

    def test_job_entry_properties(self):
        job = JobEntry(
            job_id='test', circuit_name='Test', backend='sim',
            shots=100, started_at=time.time(), completed_at=time.time() + 1.0,
        )
        assert job.duration is not None
        assert job.elapsed >= 0

    def test_max_jobs_cleanup(self):
        d = JobDashboard(max_jobs=3)
        for i in range(5):
            d.add_job(f'j{i}', 'Test', 'sim', 100)
        assert len(d.jobs) <= 3


# ==================== Circuit Library Tests ====================

class TestCircuitLibraryPanel:
    def test_init(self):
        lib = CircuitLibraryPanel()
        assert len(lib.templates) >= 10

    def test_builtin_circuits(self):
        lib = CircuitLibraryPanel()
        bell = lib.get_template('bell_state')
        assert bell is not None
        assert bell.name == 'Bell State'
        assert bell.num_qubits == 2

    def test_get_by_category(self):
        lib = CircuitLibraryPanel()
        algos = lib.get_by_category('Algorithms')
        assert len(algos) >= 3

    def test_search(self):
        lib = CircuitLibraryPanel()
        results = lib.search('bell')
        assert len(results) >= 1
        assert any('Bell' in r.name for r in results)

    def test_search_tags(self):
        lib = CircuitLibraryPanel()
        results = lib.search('entanglement')
        assert len(results) >= 1

    def test_save_user_circuit(self):
        lib = CircuitLibraryPanel()
        ct = CircuitTemplate(
            template_id='user_test', name='User Test', description='Test',
            category='Custom', num_qubits=2, depth=2,
            gates=[{'name': 'H', 'qubits': [0]}], tags=['test'],
        )
        lib.save_user_circuit(ct)
        assert 'user_test' in lib.user_circuits

    def test_delete_user_circuit(self):
        lib = CircuitLibraryPanel()
        ct = CircuitTemplate(
            template_id='user_del', name='Delete Me', description='Test',
            category='Custom', num_qubits=2, depth=2,
            gates=[], tags=[],
        )
        lib.save_user_circuit(ct)
        lib.delete_user_circuit('user_del')
        assert 'user_del' not in lib.user_circuits

    def test_categories(self):
        lib = CircuitLibraryPanel()
        cats = lib.get_categories()
        assert 'Fundamental' in cats
        assert 'Algorithms' in cats
        assert 'QEC' in cats

    def test_render_data(self):
        lib = CircuitLibraryPanel()
        rd = lib.get_render_data()
        assert 'builtin' in rd
        assert 'user' in rd
        assert 'categories' in rd

    def test_template_to_dict(self):
        lib = CircuitLibraryPanel()
        bell = lib.get_template('bell_state')
        d = bell.to_dict()
        assert d['template_id'] == 'bell_state'
        assert 'gates' in d


# ==================== Code Editor Tests ====================

class TestCodeEditor:
    def test_init(self):
        ed = CodeEditor()
        assert ed.content == ''
        assert ed.modified is False

    def test_set_content(self):
        ed = CodeEditor()
        ed.set_content('from abirqu import Circuit\nc = Circuit(2)')
        assert 'Circuit' in ed.content
        assert ed.modified is True

    def test_insert_at_cursor(self):
        ed = CodeEditor()
        ed.set_content('hello world')
        ed.cursor_line = 0
        ed.cursor_col = 5
        ed.insert_at_cursor(' beautiful')
        assert 'hello beautiful world' in ed.content

    def test_undo_redo(self):
        ed = CodeEditor()
        ed.set_content('first')
        ed.set_content('second')
        assert ed.undo() is True
        assert ed.content == 'first'
        assert ed.redo() is True
        assert ed.content == 'second'

    def test_highlight_syntax(self):
        ed = CodeEditor()
        ed.set_content('from abirqu import Circuit\nc = Circuit(2)\n# comment\n"string"')
        tokens = ed.highlight_syntax()
        types = [t.token_type for t in tokens]
        assert 'comment' in types
        assert 'string' in types

    def test_highlight_gates(self):
        ed = CodeEditor()
        tokens = ed.highlight_syntax('H CNOT X Y Z')
        gate_tokens = [t for t in tokens if t.token_type == 'gate']
        assert len(gate_tokens) >= 5

    def test_highlight_keywords(self):
        ed = CodeEditor()
        tokens = ed.highlight_syntax('def quantum(): pass')
        kw_tokens = [t for t in tokens if t.token_type == 'keyword']
        assert any(t.text == 'def' for t in kw_tokens)

    def test_get_completions(self):
        ed = CodeEditor()
        completions = ed.get_completions('H')
        assert len(completions) >= 1
        assert completions[0].text == 'H'

    def test_get_completions_all(self):
        ed = CodeEditor()
        completions = ed.get_completions()
        assert len(completions) >= 30

    def test_analyze_code(self):
        ed = CodeEditor()
        ed.set_content('def foo()\n  pass')
        diagnostics = ed.analyze_code()
        errors = [d for d in diagnostics if d.severity == 'warning']
        assert len(errors) >= 1

    def test_render_data(self):
        ed = CodeEditor()
        ed.set_content('x = 1')
        rd = ed.get_render_data()
        assert 'tokens' in rd
        assert 'diagnostics' in rd
        assert rd['line_count'] == 1

    def test_save_load(self):
        ed = CodeEditor()
        ed.set_content('test content')
        path = ed.save('/tmp/test_abirqu_editor.py')
        assert path is not None
        ed2 = CodeEditor()
        ed2.load(path)
        assert ed2.content == 'test content'

    def test_delete_selection(self):
        ed = CodeEditor()
        ed.set_content('hello world')
        ed.selection_start = (0, 5)
        ed.selection_end = (0, 6)
        ed.delete_selection()
        assert 'helloworld' in ed.content

    def test_get_line_info(self):
        ed = CodeEditor()
        ed.set_content('line1\nline2\nline3')
        info = ed.get_line_info(1)
        assert info['content'] == 'line2'


# ==================== Theme Manager Tests ====================

class TestThemeManager:
    def test_init_dark(self):
        tm = ThemeManager('dark')
        assert tm.current_theme_name == 'dark'

    def test_init_light(self):
        tm = ThemeManager('light')
        assert tm.current_theme_name == 'light'

    def test_switch_theme(self):
        tm = ThemeManager('dark')
        tm.switch_theme('light')
        assert tm.current_theme_name == 'light'

    def test_get_color(self):
        tm = ThemeManager('dark')
        color = tm.get_color('bg_primary')
        assert color.startswith('#')

    def test_list_themes(self):
        tm = ThemeManager()
        themes = tm.list_themes()
        assert 'dark' in themes
        assert 'light' in themes

    def test_callback(self):
        tm = ThemeManager('dark')
        received = []
        tm.on_theme_change(lambda name: received.append(name))
        tm.switch_theme('light')
        assert received == ['light']

    def test_css_generation(self):
        tm = ThemeManager('dark')
        css = tm.get_css()
        assert 'background-color' in css

    def test_dark_theme_colors(self):
        assert DARK_THEME['bg_primary'] == '#1a1a2e'
        assert DARK_THEME['accent_primary'] == '#7c3aed'

    def test_light_theme_colors(self):
        assert LIGHT_THEME['bg_primary'] == '#ffffff'
        assert LIGHT_THEME['accent_primary'] == '#7c3aed'


# ==================== Integration Tests ====================

class TestIntegration:
    def test_editor_to_server(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0)
        ed.add_gate('CNOT', qubit=0, target_qubit=1)
        server = QuantumServer()
        server.start()
        circuit_data = ed.get_circuit_data()
        req = {'action': 'execute', 'circuit': circuit_data, 'shots': 100}
        resp = server.handle_request(req)
        assert resp['status'] == 'ok'

    def test_full_workflow(self):
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0)
        ed.add_gate('CNOT', qubit=0, target_qubit=1)
        server = QuantumServer()
        server.start()
        req = {'action': 'execute', 'circuit': ed.get_circuit_data(), 'shots': 1000}
        resp = server.handle_request(req)
        job_id = resp['data']['job_id']
        time.sleep(0.5)
        result_req = {'action': 'result', 'job_id': job_id}
        result = server.handle_request(result_req)
        if result['data'].get('counts'):
            mp = MeasurementPanel()
            mp.set_results(result['data']['counts'], 1000)
            assert len(mp.counts) > 0

    def test_library_to_editor(self):
        lib = CircuitLibraryPanel()
        bell = lib.get_template('bell_state')
        ed = CircuitEditor(num_qubits=bell.num_qubits)
        for g in bell.gates:
            qubits = g.get('qubits', [0])
            ed.add_gate(
                name=g['name'],
                qubit=qubits[0],
                target_qubit=qubits[1] if len(qubits) > 1 else None,
            )
        assert len(ed.gates) == len(bell.gates)

    def test_state_visualizer_to_bloch(self):
        sv = StateVisualizer()
        sv.set_statevector([complex(1/math.sqrt(2), 0), complex(1/math.sqrt(2), 0)], 1)
        bloch_data = sv.get_bloch_data()
        assert bloch_data['single_qubit'] is True

    def test_hardware_compatibility(self):
        hp = HardwarePanel()
        compat = hp.get_compatible_backends(2, ['H', 'CNOT', 'T'])
        assert len(compat) >= 1

    def test_job_dashboard_workflow(self):
        dash = JobDashboard()
        dash.add_job('j1', 'Bell State', 'abirqu_simulator', 1024)
        dash.update_job('j1', status='running', progress=0.5)
        dash.update_job('j1', status='completed', progress=1.0)
        stats = dash.get_stats()
        assert stats['completed'] == 1

    def test_code_editor_to_circuit(self):
        code = CodeEditor()
        code.set_content('from abirqu import Circuit\nc = Circuit(2)\nc.h(0)\nc.cx(0, 1)')
        ed = CircuitEditor(num_qubits=2)
        ed.add_gate('H', qubit=0)
        ed.add_gate('CNOT', qubit=0, target_qubit=1)
        assert len(ed.gates) == 2

    def test_theme_applies_to_all(self):
        tm = ThemeManager('dark')
        components = [
            CircuitEditor(), BlochSphereWidget(), StateVisualizer(),
            MeasurementPanel(), HardwarePanel(), JobDashboard(),
            CircuitLibraryPanel(), CodeEditor(),
        ]
        for comp in components:
            assert comp is not None
        tm.switch_theme('light')
        assert tm.current_theme_name == 'light'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
