"""Plugin marketplace and registry for AbirQu."""

import ast
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class PluginBase(Protocol):
    """Protocol that all AbirQu plugins must implement."""

    def activate(self, context: Dict[str, Any]) -> None: ...

    def deactivate(self) -> None: ...

    def get_manifest(self) -> "PluginManifest": ...


@dataclass
class PluginManifest:
    name: str
    version: str
    author: str = "unknown"
    description: str = ""
    hooks: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


class SandboxedNamespace:
    def __init__(self, plugin_name: str, permissions: Optional[List[str]] = None):
        self.plugin_name = plugin_name
        self.permissions = set(permissions or [])
        self._locals: Dict[str, Any] = {}

    def execute(self, code: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)) and "filesystem" not in self.permissions:
                    return {"success": False, "error": "imports blocked in sandbox"}
                if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                    return {"success": False, "error": f"access to private/dunder attribute '{node.attr}' blocked in sandbox"}
                if isinstance(node, ast.Name) and node.id.startswith("_"):
                    return {"success": False, "error": f"access to private/dunder name '{node.id}' blocked in sandbox"}
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name.startswith("_"):
                    return {"success": False, "error": f"definition of private/dunder name '{node.name}' blocked in sandbox"}
                if isinstance(node, ast.keyword) and node.arg and node.arg.startswith("_"):
                    return {"success": False, "error": f"private/dunder keyword argument '{node.arg}' blocked in sandbox"}

            # Note: AST-based validation and wrapper functions mitigate in-process privilege
            # escalation and dunder traversal, but robust security isolation requires a separate
            # process / container sandbox boundary.
            def _safe_print(*args, **kwargs):
                print(*args, **kwargs)

            def _safe_len(obj):
                return len(obj)

            def _safe_range(*args):
                return range(*args)

            def _safe_min(*args, **kwargs):
                return min(*args, **kwargs)

            def _safe_max(*args, **kwargs):
                return max(*args, **kwargs)

            def _safe_sum(*args, **kwargs):
                return sum(*args, **kwargs)

            def _safe_abs(x):
                return abs(x)

            safe_builtins = {
                "len": _safe_len,
                "range": _safe_range,
                "min": _safe_min,
                "max": _safe_max,
                "sum": _safe_sum,
                "abs": _safe_abs,
                "print": _safe_print,
            }
            if "filesystem" in self.permissions:
                _ALLOWED_IMPORTS = {"json", "math", "datetime", "collections", "itertools", "functools", "re", "hashlib", "uuid"}
                def _restricted_import(name, *args, **kwargs):
                    if name.split(".")[0] not in _ALLOWED_IMPORTS:
                        raise ImportError(f"import '{name}' is not allowed in sandbox")
                    return __import__(name, *args, **kwargs)
                safe_builtins["__import__"] = _restricted_import
            exec(compile(tree, "<sandbox>", "exec"), {"__builtins__": safe_builtins}, self._locals)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get(self, key: str) -> Any:
        return self._locals.get(key)


class EventBus:
    def __init__(self):
        self._subs: Dict[str, List[Dict[str, Any]]] = {}
        self._log: List[Dict[str, Any]] = []

    def subscribe(self, event: str, plugin: str, fn: Callable[[Any], Any]) -> None:
        self._subs.setdefault(event, []).append({"plugin": plugin, "fn": fn})

    def publish(self, event: str, data: Any) -> Dict[str, Any]:
        subs = self._subs.get(event, [])
        results = []
        for s in subs:
            try:
                out = s["fn"](data)
                results.append({"plugin": s["plugin"], "result": out, "ok": True})
            except Exception as exc:
                results.append({"plugin": s["plugin"], "error": str(exc), "ok": False})
        entry = {"event": event, "data": data, "results": results}
        self._log.append(entry)
        return {"subscribers_notified": len(subs), "results": results}

    def list_events(self):
        return sorted(self._subs.keys())

    def get_log(self):
        return list(self._log)


class OutOfProcessPluginHost:
    """Out-of-process plugin host running plugins in an isolated subprocess.
    Enforces manifest-declared permissions for filesystem and network.
    """
    def __init__(self, manifest: PluginManifest, source: str):
        self.manifest = manifest
        self.source = source
        self.permissions = set(manifest.permissions or [])

    def execute_hook(self, hook: str, data: Any = None) -> Dict[str, Any]:
        import os
        import subprocess
        import sys
        import json

        perms = list(self.permissions)
        wrapper_code = f"""
import sys, json

manifest_permissions = {perms}

# Restrict network socket connection if not granted
if "network" not in manifest_permissions:
    try:
        import socket
        def _blocked_connect(*args, **kwargs):
            raise PermissionError("Network access not granted in plugin manifest")
        socket.socket.connect = _blocked_connect
    except Exception:
        pass

# Restrict filesystem access if not granted
if "filesystem" not in manifest_permissions:
    import builtins
    def _restricted_open(file, *args, **kwargs):
        raise PermissionError("Filesystem access not granted in plugin manifest")
    builtins.open = _restricted_open

# Execute plugin source code
plugin_globals = {{}}
exec({repr(self.source)}, plugin_globals)

hook_name = "on_" + {repr(hook)}
fn = plugin_globals.get(hook_name)
if fn and callable(fn):
    res = fn({repr(data)})
    print(json.dumps({{"ok": True, "result": res}}))
else:
    print(json.dumps({{"ok": True, "result": None}}))
"""
        try:
            clean_env = {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONNOUSERSITE": "1",
            }
            res = subprocess.run(
                [sys.executable, "-c", wrapper_code],
                capture_output=True,
                text=True,
                timeout=5,
                env=clean_env,
            )
            if res.returncode != 0:
                err = res.stderr.strip().splitlines()[-1] if res.stderr else "Execution failure"
                return {"ok": False, "error": err}
            return json.loads(res.stdout.strip())
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Plugin execution timed out (limit: 5s)"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


class PluginRegistry:
    def __init__(self, out_of_process: bool = True):
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.event_bus = EventBus()
        self.out_of_process = out_of_process

    def register(self, manifest: PluginManifest, source: str) -> Dict[str, Any]:
        if self.out_of_process:
            host = OutOfProcessPluginHost(manifest, source)
            # Test run activate/initial hook check
            test_res = host.execute_hook("init", None)
            if not test_res.get("ok"):
                return {"loaded": False, "error": test_res.get("error")}
            self.plugins[manifest.name] = {
                "manifest": manifest,
                "status": "enabled",
                "host": host,
                "source": source,
            }
            for hook in manifest.hooks or []:
                self.event_bus.subscribe(
                    hook,
                    manifest.name,
                    lambda data, h=hook, p_host=host: p_host.execute_hook(h, data).get("result"),
                )
            return {"loaded": True, "name": manifest.name, "version": manifest.version}

        ns = SandboxedNamespace(manifest.name, permissions=manifest.permissions or [])
        res = ns.execute(source)
        if not res["success"]:
            return {"loaded": False, "error": res.get("error")}
        self.plugins[manifest.name] = {
            "manifest": manifest,
            "status": "enabled",
            "namespace": ns,
            "source": source,
        }
        for hook in manifest.hooks or []:
            fn = ns.get(f"on_{hook}")
            if callable(fn):
                self.event_bus.subscribe(hook, manifest.name, fn)
        return {"loaded": True, "name": manifest.name, "version": manifest.version}

    def list_plugins(self) -> List[Dict[str, Any]]:
        out = []
        for name, p in self.plugins.items():
            m = p["manifest"]
            out.append({"name": name, "version": m.version, "description": m.description, "status": p["status"]})
        return out

    def hot_reload(self, name: str, source: str) -> Dict[str, Any]:
        if name not in self.plugins:
            return {"reloaded": False, "error": "plugin not found"}
        manifest = self.plugins[name]["manifest"]
        for event, subs in self.event_bus._subs.items():
            self.event_bus._subs[event] = [s for s in subs if s["plugin"] != name]
        self.disable(name)
        self.unload(name)
        r = self.register(manifest, source)
        return {"reloaded": bool(r.get("loaded")), "name": name}

    def disable(self, name: str) -> None:
        if name in self.plugins:
            self.plugins[name]["status"] = "disabled"

    def unload(self, name: str) -> Dict[str, Any]:
        if name in self.plugins:
            del self.plugins[name]
            return {"unloaded": True, "name": name}
        return {"unloaded": False, "name": name}


class SemanticVersion:
    def __init__(self, v: str):
        self.raw = v
        self.major, self.minor, self.patch = [int(x) for x in v.split(".")]

    def __str__(self):
        return self.raw

    def _cmp(self, other: "SemanticVersion"):
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def satisfies(self, expr: str) -> bool:
        expr = expr.strip()
        if expr.startswith(">="):
            o = SemanticVersion(expr[2:])
            return (self.major, self.minor, self.patch) >= (o.major, o.minor, o.patch)
        if expr.startswith("<="):
            o = SemanticVersion(expr[2:])
            return (self.major, self.minor, self.patch) <= (o.major, o.minor, o.patch)
        if expr.startswith("^"):
            o = SemanticVersion(expr[1:])
            return self.major == o.major and (self.major, self.minor, self.patch) >= (o.major, o.minor, o.patch)
        if expr.startswith("~"):
            o = SemanticVersion(expr[1:])
            return self.major == o.major and self.minor == o.minor and self.patch >= o.patch
        return self.raw == expr


class AbirHubMarketplace:
    def __init__(self, core_version: str):
        self.core_version = SemanticVersion(core_version)
        self.repo: Dict[str, Dict[str, Any]] = {
            "abirqu-noise-pack": {"name": "abirqu-noise-pack", "version": "0.1.0", "author": "core", "description": "Noise models", "tags": ["noise"], "requires": ">=0.1.0", "downloads": 1200},
            "abirqu-optimizer-zx": {"name": "abirqu-optimizer-zx", "version": "0.1.1", "author": "core", "description": "ZX optimizer", "tags": ["optimizer"], "requires": ">=0.1.0", "downloads": 980},
            "abirqu-qml-kernel": {"name": "abirqu-qml-kernel", "version": "0.1.0", "author": "labs", "description": "QML kernels", "tags": ["qml"], "requires": ">=0.1.0", "deps": ["abirqu-optimizer-zx"], "downloads": 540},
            "abirqu-finance-pro": {"name": "abirqu-finance-pro", "version": "1.0.0", "author": "ext", "description": "Finance workloads", "tags": ["finance"], "requires": ">=1.0.0", "downloads": 50},
            "abirqu-error-mitigation": {"name": "abirqu-error-mitigation", "version": "0.1.0", "author": "core", "description": "Error mitigation strategies (ZNE, PEC, CDR)", "tags": ["error-mitigation", "noise"], "requires": ">=1.2.0", "downloads": 850},
            "abirqu-vqe-advanced": {"name": "abirqu-vqe-advanced", "version": "0.1.0", "author": "core", "description": "Advanced VQE ansatze and optimizers", "tags": ["chemistry", "vqe"], "requires": ">=1.2.0", "downloads": 720},
            "abirqu-quantum-ml": {"name": "abirqu-quantum-ml", "version": "0.1.0", "author": "core", "description": "Quantum ML kernels and classifiers", "tags": ["qml", "ml"], "requires": ">=1.2.0", "downloads": 610},
            "abirqu-noise-char": {"name": "abirqu-noise-char", "version": "0.1.0", "author": "core", "description": "Noise characterization and tomography", "tags": ["noise", "characterization"], "requires": ">=1.2.0", "downloads": 430},
        }
        self.installed: Dict[str, Dict[str, Any]] = {}

    def _compatible(self, pkg: Dict[str, Any]) -> bool:
        return self.core_version.satisfies(pkg.get("requires", ">=0.0.0"))

    def search(self, query: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        q = query.lower().strip()
        t = set(tags or [])
        rows = []
        for pkg in self.repo.values():
            if q and q not in pkg["name"] and q not in pkg["description"].lower():
                continue
            if t and not t.intersection(set(pkg.get("tags", []))):
                continue
            row = dict(pkg)
            row["compatible"] = self._compatible(pkg)
            rows.append(row)
        return {"results": rows}

    def install(self, name: str) -> Dict[str, Any]:
        if name not in self.repo:
            return {"installed": False, "reason": "not-found"}
        pkg = self.repo[name]
        if not self._compatible(pkg):
            return {"installed": False, "reason": "incompatible-core-version"}
        deps_done = []
        for d in pkg.get("deps", []):
            if d not in self.installed:
                self.installed[d] = {**self.repo[d], "status": "installed"}
                deps_done.append(d)
        self.installed[name] = {**pkg, "status": "installed"}
        return {"installed": True, "name": name, "dependencies_installed": deps_done}

    def publish(self, **kwargs):
        name = kwargs["name"]
        self.repo[name] = dict(kwargs)
        return {"published": True, "name": name}

    def list_installed(self):
        return list(self.installed.values())


__all__ = [
    "PluginBase",
    "PluginManifest",
    "SandboxedNamespace",
    "EventBus",
    "PluginRegistry",
    "SemanticVersion",
    "AbirHubMarketplace",
]
