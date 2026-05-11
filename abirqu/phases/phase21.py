import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class DatasetVersion:
    version: str
    created_at: float
    rows: int


class QuantumDatasetStore:
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, name: str, rows: List[Dict[str, Any]], version: Optional[str] = None) -> DatasetVersion:
        ver = version or f"v{int(time.time())}"
        path = self.root / f"{name}_{ver}.json"
        path.write_text(json.dumps(rows, indent=2))
        return DatasetVersion(version=ver, created_at=time.time(), rows=len(rows))

    def read(self, name: str, version: str) -> List[Dict[str, Any]]:
        path = self.root / f"{name}_{version}.json"
        return json.loads(path.read_text())


class QuantumFeatureEncoder:
    def encode(self, x: np.ndarray, mode: str = "angle") -> np.ndarray:
        x = np.asarray(x, dtype=float)
        if mode == "amplitude":
            n = np.linalg.norm(x)
            return x / n if n > 0 else x
        if mode == "basis":
            return (x > 0.5).astype(float)
        if mode == "kernel":
            return np.exp(-x * x)
        return np.pi * x


class QuantumResultAnalyzer:
    def summarize_counts(self, counts: Dict[str, int]) -> Dict[str, Any]:
        total = sum(counts.values())
        if total == 0:
            return {"total": 0, "entropy": 0.0, "top_state": None}
        probs = np.array([c / total for c in counts.values()], dtype=float)
        entropy = float(-np.sum(np.where(probs > 0, probs * np.log2(probs), 0.0)))
        top_state = max(counts, key=counts.get)
        return {"total": total, "entropy": entropy, "top_state": top_state}


class PrecisionManager:
    def map_precision(self, classical_dtype: str, target: str = "quantum") -> Dict[str, str]:
        table = {
            "float64": "float32",
            "float32": "float16",
            "int64": "int32",
            "int32": "int16",
        }
        return {"source": classical_dtype, "target": table.get(classical_dtype, classical_dtype), "domain": target}
