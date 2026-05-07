import json
from abirqu.plugins import (
    PluginRegistry,
    PluginManifest,
    SandboxedNamespace,
    EventBus,
    AbirHubMarketplace,
    SemanticVersion,
)

print("=" * 70)
print("  Phase 36: Advanced Plugin & Extensibility System Tests")
print("=" * 70)

# ---------------------------------------------------------
# Test 36.1a: Sandboxed Plugin Execution
# ---------------------------------------------------------
print("\n--- Test 36.1a: Sandboxed Namespace ---")
sandbox = SandboxedNamespace("test-plugin", permissions=[])

# Safe code
result = sandbox.execute("x = 2 + 3\ngreeting = 'Hello from plugin!'")
print(f"  Safe execution: {result}")
print(f"  x = {sandbox.get('x')}, greeting = {sandbox.get('greeting')}")
assert sandbox.get("x") == 5

# Blocked import (os module)
result = sandbox.execute("import os; os.listdir('.')")
print(f"  Blocked import: success={result['success']}, error={result.get('error', '')[:60]}")
assert not result["success"]

# Allowed with permission
sandbox_fs = SandboxedNamespace("fs-plugin", permissions=["filesystem"])
result_fs = sandbox_fs.execute("import os; dirs = 'access_granted'")
print(f"  With filesystem perm: success={result_fs['success']}")
assert result_fs["success"]
print("✅ Sandboxed namespaces passed")

# ---------------------------------------------------------
# Test 36.1b: Event Bus (Pub/Sub)
# ---------------------------------------------------------
print("\n--- Test 36.1b: Event Bus ---")
bus = EventBus()

# Subscribe
hook_results = []
def on_pre_circuit(data):
    hook_results.append(f"pre_circuit: {data}")
    return "validated"

def on_post_transpile(data):
    hook_results.append(f"post_transpile: {data}")
    return "optimized"

bus.subscribe("pre_circuit", "validator-plugin", on_pre_circuit)
bus.subscribe("post_transpile", "optimizer-plugin", on_post_transpile)
bus.subscribe("pre_circuit", "logger-plugin", lambda d: hook_results.append(f"log: {d}"))

print(f"  Events: {bus.list_events()}")

# Publish
pub_result = bus.publish("pre_circuit", {"qubits": 4, "gates": 12})
print(f"  Published 'pre_circuit': {pub_result['subscribers_notified']} notified")
assert pub_result["subscribers_notified"] == 2

pub_result2 = bus.publish("post_transpile", {"depth": 8})
print(f"  Published 'post_transpile': {pub_result2['subscribers_notified']} notified")

print(f"  Hook results: {hook_results}")
print(f"  Event log: {len(bus.get_log())} entries")
print("✅ Event bus passed")

# ---------------------------------------------------------
# Test 36.1c: Plugin Registry & Hot-Reload
# ---------------------------------------------------------
print("\n--- Test 36.1c: Plugin Registry & Hot-Reload ---")
registry = PluginRegistry()

# Create a plugin
manifest = PluginManifest(
    name="custom-noise",
    version="1.0.0",
    author="Abir",
    description="Custom noise model for superconducting qubits",
    hooks=["pre_circuit", "post_measurement"],
    permissions=[],
)

plugin_code_v1 = """
def on_pre_circuit(data):
    return {'noise_injected': True, 'version': 'v1'}

def on_post_measurement(data):
    return {'corrected': True}

NOISE_STRENGTH = 0.01
"""

load_result = registry.register(manifest, plugin_code_v1)
print(f"  Loaded: {json.dumps(load_result, indent=2, default=str)}")
assert load_result["loaded"]

# List plugins
print(f"\n  Installed Plugins:")
for p in registry.list_plugins():
    print(f"    {p['name']} v{p['version']} [{p['status']}] — {p['description']}")

# Fire event through registry's bus
fire = registry.event_bus.publish("pre_circuit", {"test": True})
print(f"\n  Event 'pre_circuit': {fire['results']}")

# Hot-reload with updated code
plugin_code_v2 = """
def on_pre_circuit(data):
    return {'noise_injected': True, 'version': 'v2', 'enhanced': True}

def on_post_measurement(data):
    return {'corrected': True, 'fidelity_boost': 0.02}

NOISE_STRENGTH = 0.005
"""

reload_result = registry.hot_reload("custom-noise", plugin_code_v2)
print(f"\n  Hot-Reload: {json.dumps(reload_result, default=str)}")
assert reload_result["reloaded"]

# Verify new version is active
fire2 = registry.event_bus.publish("pre_circuit", {"test": True})
print(f"  After reload: {fire2['results']}")
# The v2 handler should return 'enhanced': True
assert fire2["results"][0]["result"]["version"] == "v2"

# Disable & unload
registry.disable("custom-noise")
print(f"\n  Disabled: {registry.plugins['custom-noise']['status']}")
unload = registry.unload("custom-noise")
print(f"  Unloaded: {json.dumps(unload, default=str)}")
print("✅ Plugin registry & hot-reload passed")

# ---------------------------------------------------------
# Test 36.2a: Semantic Versioning
# ---------------------------------------------------------
print("\n--- Test 36.2a: Semantic Versioning ---")
v = SemanticVersion("1.2.3")
print(f"  Version: {v}")
assert v.satisfies(">=1.0.0")
assert v.satisfies("<=2.0.0")
assert v.satisfies("^1.0.0")   # Caret: same major
assert not v.satisfies("^2.0.0")
assert v.satisfies("~1.2.0")   # Tilde: same minor
assert not v.satisfies("~1.3.0")
print(f"  >=1.0.0: {v.satisfies('>=1.0.0')}")
print(f"  ^1.0.0:  {v.satisfies('^1.0.0')}")
print(f"  ~1.2.0:  {v.satisfies('~1.2.0')}")
print(f"  ~1.3.0:  {v.satisfies('~1.3.0')}")
print("✅ Semantic versioning passed")

# ---------------------------------------------------------
# Test 36.2b: Abir-Hub Marketplace
# ---------------------------------------------------------
print("\n--- Test 36.2b: Abir-Hub Marketplace ---")
hub = AbirHubMarketplace(core_version="0.1.0")

# Search
print(f"  Search 'noise':")
results = hub.search("noise")
for r in results["results"]:
    compat = "✅" if r["compatible"] else "❌"
    print(f"    {compat} {r['name']} v{r['version']} ({r['downloads']} downloads)")

print(f"\n  Search by tags ['optimizer']:")
results2 = hub.search(tags=["optimizer"])
for r in results2["results"]:
    print(f"    {r['name']} — {r['description']}")

# Install
print(f"\n  Install 'abirqu-qml-kernel' (has dependency):")
install = hub.install("abirqu-qml-kernel")
print(f"    {json.dumps(install, indent=2, default=str)}")
assert install["installed"]
assert len(install["dependencies_installed"]) > 0  # Should auto-install abirqu-optimizer-zx

# Install incompatible plugin
print(f"\n  Install 'abirqu-finance-pro' (requires >=1.0.0):")
install_fail = hub.install("abirqu-finance-pro")
print(f"    {json.dumps(install_fail, default=str)}")
assert not install_fail["installed"]

# Publish
print(f"\n  Publish new plugin:")
pub = hub.publish(
    name="abirqu-custom-gates",
    version="0.1.0",
    author="Abir",
    description="Custom parametric gate library",
    tags=["gates", "custom"],
)
print(f"    {json.dumps(pub, default=str)}")
assert pub["published"]

# List installed
print(f"\n  Installed Plugins:")
for p in hub.list_installed():
    print(f"    {p['name']} v{p['version']} [{p['status']}]")

print("✅ Abir-Hub marketplace passed")

print("\n" + "=" * 70)
print("  Phase 36 — ALL TESTS PASSED SUCCESSFULLY")
print("=" * 70)
