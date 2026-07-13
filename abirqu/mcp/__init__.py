"""
Model Context Protocol (MCP) Integration
=========================================
JSON-RPC 2.0 server and client for exposing quantum operations as MCP
tools, plus built-in tools for circuit creation, execution, and analysis.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 message types
# ---------------------------------------------------------------------------

def _jsonrpc_response(
    request_id: Any, result: Any = None, error: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    msg: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def _jsonrpc_error(
    request_id: Any, code: int, message: str, data: Any = None
) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return _jsonrpc_response(request_id, error=err)


# ---------------------------------------------------------------------------
# Tool decorator
# ---------------------------------------------------------------------------

def mcp_tool(
    name: Optional[str] = None,
    description: str = "",
    input_schema: Optional[Dict[str, Any]] = None,
) -> Callable:
    """Decorator that registers a function as an MCP tool.

    Usage::

        @mcp_tool("create_circuit", description="Create a quantum circuit")
        def create_circuit(num_qubits: int) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        schema = input_schema or _infer_schema(func)
        func._mcp_tool = {  # type: ignore[attr-defined]
            "name": tool_name,
            "description": description or func.__doc__ or "",
            "inputSchema": schema,
        }
        return func

    return decorator


def _infer_schema(func: Callable) -> Dict[str, Any]:
    """Infer a JSON Schema from function signature (best-effort)."""
    import inspect

    sig = inspect.signature(func)
    properties: Dict[str, Any] = {}
    required: List[str] = []
    for pname, param in sig.parameters.items():
        prop: Dict[str, Any] = {}
        if param.annotation is not inspect.Parameter.empty:
            annotation = param.annotation
            if annotation is int:
                prop["type"] = "integer"
            elif annotation is float:
                prop["type"] = "number"
            elif annotation is str:
                prop["type"] = "string"
            elif annotation is bool:
                prop["type"] = "boolean"
            else:
                prop["type"] = "string"
        if param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            required.append(pname)
        properties[pname] = prop
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

class MCPServer:
    """MCP server that exposes quantum tools over JSON-RPC 2.0.

    Instantiate, register tools (via ``register`` or ``register_tool``),
    then call ``handle`` with raw JSON-RPC request strings.

    Example::

        server = MCPServer("abirqu")
        server.register_tool(my_func)
        response = server.handle(json.dumps({...}))
    """

    def __init__(self, name: str = "abirqu-mcp") -> None:
        self.name = name
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._tool_funcs: Dict[str, Callable] = {}

    # -- registration -------------------------------------------------------

    def register_tool(self, func: Callable) -> None:
        """Register a callable that carries ``_mcp_tool`` metadata."""
        meta = getattr(func, "_mcp_tool", None)
        if meta is None:
            raise ValueError(
                f"{func.__name__} is not decorated with @mcp_tool"
            )
        self._tools[meta["name"]] = meta
        self._tool_funcs[meta["name"]] = func

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register *func* under *name* without requiring the decorator."""
        schema = input_schema or _infer_schema(func)
        self._tools[name] = {
            "name": name,
            "description": description or func.__doc__ or "",
            "inputSchema": schema,
        }
        self._tool_funcs[name] = func

    # -- JSON-RPC dispatch --------------------------------------------------

    def handle(self, raw: str) -> str:
        """Handle a single JSON-RPC 2.0 request and return the response JSON."""
        try:
            request = json.loads(raw)
        except json.JSONDecodeError as exc:
            resp = _jsonrpc_error(None, -32700, "Parse error", str(exc))
            return json.dumps(resp)

        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            return json.dumps(
                _jsonrpc_response(req_id, self._handle_initialize())
            )
        if method == "tools/list":
            return json.dumps(
                _jsonrpc_response(req_id, self._handle_list_tools())
            )
        if method == "tools/call":
            return json.dumps(self._handle_tool_call(req_id, params))
        if method == "ping":
            return json.dumps(_jsonrpc_response(req_id, "pong"))

        return json.dumps(
            _jsonrpc_error(req_id, -32601, f"Method not found: {method}")
        )

    def _handle_initialize(self) -> Dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": self.name, "version": "1.0.0"},
            "capabilities": {"tools": {"listChanged": False}},
        }

    def _handle_list_tools(self) -> Dict[str, Any]:
        return {"tools": list(self._tools.values())}

    def _handle_tool_call(
        self, req_id: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in self._tools:
            return _jsonrpc_error(
                req_id, -32602, f"Unknown tool: {tool_name}"
            )

        try:
            result = self._tool_funcs[tool_name](**arguments)
        except Exception as exc:
            return _jsonrpc_error(req_id, -32000, str(exc))

        return _jsonrpc_response(req_id, {"content": [{"type": "text", "text": json.dumps(result)}]})

    # -- convenience --------------------------------------------------------

    def tool_schema(self) -> List[Dict[str, Any]]:
        """Return OpenAPI-compatible tool descriptions."""
        return list(self._tools.values())


# ---------------------------------------------------------------------------
# Built-in tools
# ---------------------------------------------------------------------------

def _builtin_create_circuit(
    num_qubits: int = 2,
    name: Optional[str] = None,
    gates: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create a quantum circuit from a description."""
    from ..circuit import Circuit

    circ = Circuit(num_qubits, name or f"mcp_circuit_{uuid.uuid4().hex[:6]}")
    for g in gates or []:
        circ.add_gate(
            g.get("name", "H"),
            g.get("qubits", [0]),
            g.get("params"),
        )
    return {"circuit_id": circ.name, "num_qubits": num_qubits, "num_gates": len(circ.gates)}


def _builtin_execute_circuit(
    circuit_id: str = "",
    num_qubits: int = 2,
    shots: int = 1024,
    gates: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Execute a circuit on the built-in NumPy simulator."""
    from ..circuit import Circuit

    circ = Circuit(num_qubits, circuit_id)
    for g in gates or []:
        circ.add_gate(
            g.get("name", "H"),
            g.get("qubits", [0]),
            g.get("params"),
        )
    result = circ.run(shots=shots)
    return {"counts": result.get("counts", {}), "backend": "NumPySimulator"}


def _builtin_optimize_circuit(
    num_qubits: int = 2,
    gates: Optional[List[Dict[str, Any]]] = None,
    target: str = "generic",
) -> Dict[str, Any]:
    """Transpile and optimise a circuit."""
    from ..circuit import Circuit
    from ..transpiler import TranspilerPipeline, TargetBackend

    circ = Circuit(num_qubits)
    for g in gates or []:
        circ.add_gate(
            g.get("name", "H"),
            g.get("qubits", [0]),
            g.get("params"),
        )
    backend_map = {v.value: v for v in TargetBackend}
    tb = backend_map.get(target, TargetBackend.GENERIC)
    pipe = TranspilerPipeline(target=tb)
    optimised = pipe.transpile(circ)
    return {
        "num_gates_before": len(circ.gates),
        "num_gates_after": len(optimised.gates),
        "target": target,
    }


def _builtin_analyze_results(
    counts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Interpret measurement result counts."""
    counts = counts or {}
    total = sum(counts.values()) or 1
    probabilities = {k: v / total for k, v in counts.items()}
    most_probable = max(probabilities, key=lambda k: probabilities[k]) if probabilities else ""
    return {
        "total_shots": total,
        "num_outcomes": len(counts),
        "probabilities": probabilities,
        "most_probable": most_probable,
        "entropy": -sum(p * _log2(p) for p in probabilities.values() if p > 0),
    }


def _log2(x: float) -> float:
    import math
    return math.log2(x)


def _builtin_get_backend_info() -> Dict[str, Any]:
    """List available backends and their properties."""
    from ..transpiler import TargetBackend

    backends = {}
    for tb in TargetBackend:
        backends[tb.value] = {
            "name": tb.value,
            "native_gates": {
                "IBM": ["ECR", "ID", "RZ", "X", "SX"],
                "google": ["PhasedXPow", "XPow", "YPow", "CZ"],
                "ionq": ["GPI", "GPI2", "MS"],
                "generic": ["H", "RZ", "CNOT"],
            }.get(tb.value, ["H", "RZ", "CNOT"]),
        }
    return {"backends": backends}


def register_builtin_tools(server: MCPServer) -> None:
    """Register all built-in tools on *server*."""
    server.register(
        "create_circuit",
        _builtin_create_circuit,
        "Create a quantum circuit from a description",
    )
    server.register(
        "execute_circuit",
        _builtin_execute_circuit,
        "Execute a circuit on the built-in simulator",
    )
    server.register(
        "optimize_circuit",
        _builtin_optimize_circuit,
        "Transpile and optimise a circuit for a target backend",
    )
    server.register(
        "analyze_results",
        _builtin_analyze_results,
        "Interpret measurement result counts",
    )
    server.register(
        "get_backend_info",
        _builtin_get_backend_info,
        "List available quantum backends",
    )


# ---------------------------------------------------------------------------
# MCP Client
# ---------------------------------------------------------------------------

class MCPClient:
    """Client for connecting to external MCP servers over JSON-RPC 2.0.

    Wraps a *transport* — any object with a ``send(raw: str) → str``
    method (e.g. stdio, HTTP, WebSocket adapter).

    Parameters
    ----------
    transport : object
        Must implement ``send(raw: str) -> str``.
    server_name : str
        Human-readable label for the remote server.
    """

    def __init__(self, transport: Any, server_name: str = "remote") -> None:
        self.transport = transport
        self.server_name = server_name
        self._tools: List[Dict[str, Any]] = []
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        req: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params is not None:
            req["params"] = params
        raw_response = self.transport.send(json.dumps(req))
        return json.loads(raw_response)

    def initialize(self) -> Dict[str, Any]:
        """Initialize connection and return server capabilities."""
        return self._send("initialize")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from the remote server."""
        resp = self._send("tools/list")
        self._tools = resp.get("result", {}).get("tools", [])
        return self._tools

    def call_tool(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Invoke a remote tool by name."""
        resp = self._send(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        result = resp.get("result", {})
        error = resp.get("error")
        if error:
            raise RuntimeError(f"MCP error: {error['message']}")
        return result

    def ping(self) -> str:
        """Ping the remote server."""
        resp = self._send("ping")
        return resp.get("result", "")


__all__ = [
    "MCPServer",
    "MCPClient",
    "mcp_tool",
    "register_builtin_tools",
]
