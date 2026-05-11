import ast
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence


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
            safe_builtins = {
                "len": len,
                "range": range,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "print": print,
            }
            if "filesystem" in self.permissions:
                safe_builtins["__import__"] = __import__
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


class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.event_bus = EventBus()

    def register(self, manifest: PluginManifest, source: str) -> Dict[str, Any]:
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
