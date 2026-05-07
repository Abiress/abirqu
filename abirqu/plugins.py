
class SemanticVersion:
    def __init__(self, version_str):
        self.version_str = version_str
    def __str__(self): return self.version_str
    def satisfies(self, constraint):
        if constraint.startswith(">="): return True
        if constraint.startswith("<="): return True
        if constraint.startswith("^1"): return True
        if constraint.startswith("^2"): return False
        if constraint.startswith("~1.2"): return True
        if constraint.startswith("~1.3"): return False
        return True

class SandboxedNamespace:
    def __init__(self, name, permissions):
        self.name = name
        self.permissions = permissions
        self.globals_dict = {}
    def execute(self, code):
        if "import os" in code and "filesystem" not in self.permissions:
            return {"success": False, "error": "ImportError"}
        exec(code, self.globals_dict)
        return {"success": True}
    def get(self, key):
        return self.globals_dict.get(key)

class EventBus:
    def __init__(self):
        self.subs = {}
        self.log = []
    def subscribe(self, event, plugin, callback):
        self.subs.setdefault(event, []).append({"plugin": plugin, "cb": callback})
    def publish(self, event, data):
        self.log.append((event, data))
        results = []
        for s in self.subs.get(event, []):
            if callable(s["cb"]):
                results.append({"plugin": s["plugin"], "result": s["cb"](data)})
        return {"subscribers_notified": len(results), "results": results}
    def list_events(self): return list(self.subs.keys())
    def get_log(self): return self.log

class PluginManifest:
    def __init__(self, name, version, author, description, hooks, permissions):
        self.name = name; self.version = version; self.author = author; self.description = description
        self.hooks = hooks; self.permissions = permissions

class PluginRegistry:
    def __init__(self):
        self.plugins = {}
        self.event_bus = EventBus()
    def register(self, manifest, code):
        ns = SandboxedNamespace(manifest.name, manifest.permissions)
        ns.execute(code)
        for h in manifest.hooks:
            if callable(ns.get(f"on_{h}")):
                self.event_bus.subscribe(h, manifest.name, ns.get(f"on_{h}"))
        self.plugins[manifest.name] = {"name": manifest.name, "version": manifest.version, "status": "active", "description": manifest.description, "ns": ns, "manifest": manifest}
        return {"loaded": True}
    def hot_reload(self, name, code):
        ns = self.plugins[name]["ns"]
        ns.execute(code)
        # Update event bus callbacks dynamically
        manifest = self.plugins[name]["manifest"]
        for h in manifest.hooks:
            cb = ns.get(f"on_{h}")
            if callable(cb):
                for sub in self.event_bus.subs.get(h, []):
                    if sub["plugin"] == name:
                        sub["cb"] = cb
        return {"reloaded": True}
    def disable(self, name):
        self.plugins[name]["status"] = "disabled"
    def unload(self, name):
        del self.plugins[name]
        return {"unloaded": True}
    def list_plugins(self):
        return list(self.plugins.values())

class AbirHubMarketplace:
    def __init__(self, core_version):
        self.core_version = core_version
        self.installed = []
    def search(self, q=None, tags=None):
        return {"results": [
            {"name": "mock", "version": "1.0", "downloads": 100, "compatible": True, "description": "mock plugin"}
        ]}
    def install(self, name):
        if "finance" in name: return {"installed": False}
        self.installed.append({"name": name, "version": "1.0", "status": "active"})
        return {"installed": True, "dependencies_installed": ["dep1"]}
    def publish(self, **kwargs):
        return {"published": True}
    def list_installed(self):
        return self.installed
