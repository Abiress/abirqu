"""
AbirQu WebAssembly Loader
==========================

Pyodide-based loader for running AbirQu in browsers and Node.js.
Provides a Python runtime in WebAssembly with the full AbirQu SDK.

Usage (Browser):
    <script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>
    <script src="abirqu_wasm.js"></script>
    <script>
        const q = await AbirQu.init();
        const result = await q.run('from abirqu import Circuit; ...');
    </script>

Usage (Node.js):
    import { AbirQuWASM } from '@abirqu/wasm';
    const q = await AbirQuWASM.init();
    const result = await q.run('from abirqu import Circuit; ...');
"""
import json
from typing import Any, Dict, Optional


class AbirQuWASM:
    """WebAssembly runtime for AbirQu quantum computing SDK."""

    _instance = None
    _pyodide = None

    @classmethod
    async def init(cls, cdn_url: str = "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js") -> "AbirQuWASM":
        """Initialize the Pyodide runtime and install AbirQu."""
        if cls._instance is not None:
            return cls._instance

        instance = cls()

        try:
            import pyodide
            instance._pyodide = pyodide
        except ImportError:
            raise ImportError(
                "Pyodide is required for WASM runtime. "
                "Include <script src='https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js'> in HTML."
            )

        # Install abirqu
        await instance._pyodide.loadPackage("micropip")
        await instance._pyodide.runPythonAsync("""
import micropip
await micropip.install('abirqu')
from abirqu import __version__
print(f"AbirQu {__version__} loaded successfully")
""")

        cls._instance = instance
        return instance

    async def run(self, code: str, capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute Python code with AbirQu imported.

        Parameters
        ----------
        code : str
            Python code to execute. AbirQu is already imported.
        capture_output : bool
            Whether to capture stdout/stderr.

        Returns
        -------
        Dict[str, Any]
            {'stdout': str, 'stderr': str, 'result': Any, 'error': str|None}
        """
        if self._pyodide is None:
            raise RuntimeError("Runtime not initialized. Call AbirQu.init() first.")

        result = {'stdout': '', 'stderr': '', 'result': None, 'error': None}

        if capture_output:
            self._pyodide.runPython("""
import sys
from io import StringIO
_stdout_capture = StringIO()
_stderr_capture = StringIO()
sys.stdout = _stdout_capture
sys.stderr = _stderr_capture
""")

        try:
            await self._pyodide.runPythonAsync(code)
            result['result'] = True
        except Exception as e:
            result['error'] = str(e)
        finally:
            if capture_output:
                result['stdout'] = self._pyodide.runPython("_stdout_capture.getvalue()")
                result['stderr'] = self._pyodide.runPython("_stderr_capture.getvalue()")
                self._pyodide.runPython("sys.stdout = sys.__stdout__; sys.stderr = sys.__stderr__")

        return result

    async def run_circuit(self, circuit_code: str, shots: int = 1000) -> Dict[str, Any]:
        """
        Run a quantum circuit and return measurement results.

        Parameters
        ----------
        circuit_code : str
            Python code that creates a Circuit object named 'circuit'.
        shots : int
            Number of measurement shots.

        Returns
        -------
        Dict[str, Any]
            {'counts': Dict[str, int], 'error': str|None}
        """
        code = f"""
{circuit_code}
circuit.measure_all()
from abirqu.primitives import QuantumRun
_result = QuantumRun(circuit, shots={shots})
"""
        result = await self.run(code)
        if result['error']:
            return {'counts': {}, 'error': result['error']}

        counts = self._pyodide.runPython("dict(_result.counts)")
        return {'counts': counts, 'error': None}

    def get_version(self) -> str:
        """Get the loaded AbirQu version."""
        return self._pyodide.runPython("import abirqu; abirqu.__version__")

    def list_modules(self) -> list:
        """List available AbirQu modules."""
        code = """
import abirqu
modules = []
for name in dir(abirqu):
    obj = getattr(abirqu, name)
    if hasattr(obj, '__module__') and 'abirqu' in str(getattr(obj, '__module__', '')):
        modules.append(name)
modules
"""
        return self._pyodide.runPython(code)


# JavaScript-compatible API
class AbirQu:
    """JavaScript-friendly wrapper for AbirQu WASM runtime."""

    @staticmethod
    async def init(**kwargs) -> AbirQuWASM:
        return await AbirQuWASM.init(**kwargs)

    @staticmethod
    async def run(code: str, **kwargs) -> Dict[str, Any]:
        q = await AbirQuWASM.init()
        return await q.run(code, **kwargs)

    @staticmethod
    async def circuit(code: str, shots: int = 1000) -> Dict[str, Any]:
        q = await AbirQuWASM.init()
        return await q.run_circuit(code, shots)


# Module exports
__all__ = ['AbirQu', 'AbirQuWASM']
