"""Tests for out-of-process plugin isolation and permission enforcement."""
import pytest
from abirqu.plugin_market import PluginManifest, OutOfProcessPluginHost


def test_plugin_execution_success():
    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="A test plugin",
        author="Abir Maheshwari",
        permissions=[],
    )
    code = """
def on_circuit_compile(data):
    return {"circuit_name": data.get("name", "unknown") + "_compiled"}
"""
    host = OutOfProcessPluginHost(manifest, code)
    res = host.execute_hook("circuit_compile", {"name": "bell_state"})
    assert res["ok"] is True
    assert res["result"] == {"circuit_name": "bell_state_compiled"}


def test_plugin_missing_hook():
    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="A test plugin",
        author="Abir Maheshwari",
        permissions=[],
    )
    code = "x = 42"
    host = OutOfProcessPluginHost(manifest, code)
    res = host.execute_hook("nonexistent_hook", {})
    assert res["ok"] is True
    assert res["result"] is None


def test_plugin_blocks_filesystem_without_permission():
    manifest = PluginManifest(
        name="unauthorized_fs",
        version="1.0.0",
        description="Attempts FS access",
        author="Abir Maheshwari",
        permissions=[],
    )
    code = """
def on_run(data):
    with open("/tmp/should_fail.txt", "w") as f:
        f.write("hello")
    return "written"
"""
    host = OutOfProcessPluginHost(manifest, code)
    res = host.execute_hook("run", {})
    assert res["ok"] is False
    assert "PermissionError" in res["error"] or "Filesystem access not granted" in res["error"]


def test_plugin_allows_filesystem_with_permission(tmp_path):
    manifest = PluginManifest(
        name="authorized_fs",
        version="1.0.0",
        description="Attempts FS access",
        author="Abir Maheshwari",
        permissions=["filesystem"],
    )
    target = str(tmp_path / "allowed.txt")
    code = f"""
def on_run(data):
    with open({repr(target)}, "w") as f:
        f.write("allowed_content")
    return "ok"
"""
    host = OutOfProcessPluginHost(manifest, code)
    res = host.execute_hook("run", {})
    assert res["ok"] is True
    assert res["result"] == "ok"
    assert (tmp_path / "allowed.txt").read_text() == "allowed_content"


def test_plugin_blocks_network_without_permission():
    manifest = PluginManifest(
        name="unauthorized_net",
        version="1.0.0",
        description="Attempts socket connect",
        author="Abir Maheshwari",
        permissions=[],
    )
    code = """
import socket

def on_run(data):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 80))
    return "connected"
"""
    host = OutOfProcessPluginHost(manifest, code)
    res = host.execute_hook("run", {})
    assert res["ok"] is False
    assert "PermissionError" in res["error"] or "Network access not granted" in res["error"]
