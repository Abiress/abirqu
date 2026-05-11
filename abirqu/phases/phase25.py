import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PluginManifest:
    name: str
    version: str
    entrypoint: str
    author: str


class PluginSecurity:
    def sign_manifest(self, manifest: PluginManifest, secret: bytes) -> str:
        payload = json.dumps(manifest.__dict__, sort_keys=True).encode("utf-8")
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()

    def verify_manifest(self, manifest: PluginManifest, signature: str, secret: bytes) -> bool:
        expected = self.sign_manifest(manifest, secret)
        return hmac.compare_digest(expected, signature)


class PluginMarketplace:
    def __init__(self) -> None:
        self._items: Dict[str, PluginManifest] = {}

    def publish(self, manifest: PluginManifest) -> None:
        key = f"{manifest.name}@{manifest.version}"
        self._items[key] = manifest

    def list(self) -> List[Dict[str, Any]]:
        return [m.__dict__ for m in self._items.values()]

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [m.__dict__ for m in self._items.values() if q in m.name.lower() or q in m.author.lower()]


class PluginPolicyEngine:
    def allow(self, manifest: PluginManifest, allowed_authors: List[str]) -> bool:
        return manifest.author in allowed_authors and manifest.entrypoint.startswith("abirqu.")
