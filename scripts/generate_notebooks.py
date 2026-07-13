#!/usr/bin/env python3
"""
Generate Jupyter notebooks from AbirQu markdown tutorials.

Reads all ``.md`` files from ``tutorials/``, converts each into a ``.ipynb``
file (nbformat 4.5), and produces a master quick-start notebook that
collects the best examples from across the tutorials.

Usage::

    python scripts/generate_notebooks.py          # convert all tutorials
    python scripts/generate_notebooks.py --only quickstart   # master only

Copyright 2026 Abir Maheshwari
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
TUTORIALS_DIR = ROOT / "tutorials"
NOTEBOOKS_DIR = TUTORIALS_DIR / "notebooks"

# ── Notebook metadata ────────────────────────────────────────────────────────

_KERNEL_SPEC = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}

_NOTEBOOK_META = {
    "kernelspec": _KERNEL_SPEC,
    "language_info": {
        "codemirror_mode": {"name": "ipython", "version": 3},
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbformat": 4,
        "nbformat_minor": 5,
        "pygments_lexer": "ipython3",
        "version": "3.10.0",
    },
}


# ── Markdown → Notebook conversion ───────────────────────────────────────────

def _make_cell(cell_type: str, source: str, **extra: Any) -> Dict[str, Any]:
    """Build a single notebook cell dict."""
    cell: Dict[str, Any] = {
        "cell_type": cell_type,
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    cell.update(extra)
    return cell


def _split_code_and_markdown(text: str) -> List[Dict[str, Any]]:
    """Split a markdown string into alternating markdown/code cells.

    Code fences (```) delimit code cells; everything else becomes a markdown
    cell.  Empty cells are skipped.
    """
    cells: List[Dict[str, Any]] = []
    in_code = False
    lang = ""
    buf: List[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") and not in_code:
            # start code block
            lang = stripped[3:].strip()
            md_chunk = "\n".join(buf).strip()
            if md_chunk:
                cells.append(_make_cell("markdown", md_chunk))
            buf = []
            in_code = True
        elif stripped.startswith("```") and in_code:
            # end code block
            code = "\n".join(buf)
            if code.strip():
                cells.append(_make_cell("code", code))
            buf = []
            in_code = False
        else:
            buf.append(line)

    # trailing markdown
    if buf:
        md = "\n".join(buf).strip()
        if md:
            cells.append(_make_cell("markdown", md))

    return cells


def md_to_notebook(text: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Convert a markdown string into a Jupyter notebook dict.

    Args:
        text: Full markdown content (with `````python`` code fences).
        title: Optional title override; if *None* extracted from first heading.

    Returns:
        A dict ready to be serialised as ``.ipynb``.
    """
    if title is None:
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = m.group(1) if m else "Untitled"

    cells = _split_code_and_markdown(text)
    if not cells:
        cells = [_make_cell("markdown", "# " + title)]

    return {
        "cells": cells,
        "metadata": _NOTEBOOK_META,
        "nbformat": 4,
        "nbformat_minor": 5,
    }


# ── Single-tutorial conversion ───────────────────────────────────────────────

def convert_tutorial(md_path: Path, out_dir: Path) -> Optional[Path]:
    """Convert one markdown file to a ``.ipynb`` notebook.

    Returns the output path on success, or *None* on failure.
    """
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[WARN] Could not read {md_path}: {exc}", file=sys.stderr)
        return None

    nb = md_to_notebook(text)
    out_path = out_dir / (md_path.stem + ".ipynb")
    out_path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  {md_path.name} → {out_path.name}")
    return out_path


def convert_all_tutorials() -> List[Path]:
    """Convert every ``*.md`` in ``tutorials/`` to ``.ipynb`` notebooks."""
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for md in sorted(TUTORIALS_DIR.glob("*.md")):
        result = convert_tutorial(md, NOTEBOOKS_DIR)
        if result is not None:
            paths.append(result)
    return paths


# ── Master quick-start notebook ───────────────────────────────────────────────

_QUICKSTART_INSTALL = """\
# AbirQu — Quick Start
#
# This notebook walks through the core features of AbirQu:
# installation, basic circuits, chemistry, error correction, and
# quantum communication.  Run each cell to get started!

## 1. Installation

```bash
pip install abirqu
```
"""

_QUICKSTART_BASIC = """\
## 2. Basic Quantum Circuit

Create a Bell state, apply rotations, and measure.
"""

_QUICKSTART_BASIC_CODE = """\
from abirqu.circuit import Circuit
import numpy as np

circuit = Circuit(2, name="Bell state")
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure_all()

result = circuit.run(shots=1024)
print("Counts:", result["counts"])
print("Probabilities:", result["probabilities"])
"""

_QUICKSTART_CHEMISTRY = """\
## 3. Quantum Chemistry (VQE)

Minimise the energy of a simple Hamiltonian.
"""

_QUICKSTART_CHEMISTRY_CODE = """\
from abirqu.circuit import Circuit
from abirqu.autodiff import parameter_shift_gradient
import numpy as np

# Simple 2-qubit VQE ansatz
def vqe_circuit(theta):
    c = Circuit(2)
    c.ry(0, theta[0])
    c.ry(1, theta[1])
    c.cnot(0, 1)
    return c

# Hamiltonian: Z⊗I + I⊗Z + 0.5*X⊗X
H = np.diag([1, -1, -1, 1]).astype(complex)
H += 0.5 * np.array([[0,0,0,1],[0,0,1,0],[0,1,0,0],[1,0,0,0]], dtype=complex)

# Initial parameters
theta = np.array([0.5, 0.3])
grad = parameter_shift_gradient(vqe_circuit(theta), theta, H)
print("Gradients:", grad.gradients)
print("Method:", grad.method, "| Evals:", grad.circuit_evals)
"""

_QUICKSTART_QEC = """\
## 4. Quantum Error Correction

Protect a logical qubit using a repetition code.
"""

_QUICKSTART_QEC_CODE = """\
from abirqu.circuit import Circuit

# 3-qubit repetition code
code = Circuit(3)
code.h(0)  # encode
code.cnot(0, 1)
code.cnot(0, 2)

# Introduce a bit-flip error on qubit 1
code.x(1)

# Syndrome measurement
code.cnot(0, 1)
code.cnot(0, 2)

code.measure_all()
result = code.run(shots=1024)
print("Syndrome counts:", result["counts"])
"""

_QUICKSTART_COMM = """\
## 5. Quantum Communication

BB84-style key distribution simulation.
"""

_QUICKSTART_COMM_CODE = """\
from abirqu.circuit import Circuit
import numpy as np

def bb84_round():
    n = 4
    circ = Circuit(n)
    # Alice's random bits and bases
    bits = np.random.randint(0, 2, n)
    bases = np.random.randint(0, 2, n)
    for i in range(n):
        if bits[i]:
            circ.x(i)
        if bases[i]:
            circ.h(i)
    # Bob's random bases
    bob_bases = np.random.randint(0, 2, n)
    for i in range(n):
        if bob_bases[i]:
            circ.h(i)
    circ.measure_all()
    return circ, bits, bases, bob_bases

circ, bits, a_bases, b_bases = bb84_round()
result = circ.run(shots=1)
print("Alice bits:", bits)
print("Alice bases:", a_bases)
print("Bob bases:  ", b_bases)
"""


def build_quickstart_notebook() -> Dict[str, Any]:
    """Assemble the master quick-start notebook dict."""
    cells = [
        _make_cell("markdown", _QUICKSTART_INSTALL),
        _make_cell("code", "pip install -q abirqu"),
        _make_cell("markdown", _QUICKSTART_BASIC),
        _make_cell("code", _QUICKSTART_BASIC_CODE),
        _make_cell("markdown", _QUICKSTART_CHEMISTRY),
        _make_cell("code", _QUICKSTART_CHEMISTRY_CODE),
        _make_cell("markdown", _QUICKSTART_QEC),
        _make_cell("code", _QUICKSTART_QEC_CODE),
        _make_cell("markdown", _QUICKSTART_COMM),
        _make_cell("code", _QUICKSTART_COMM_CODE),
    ]
    return {
        "cells": cells,
        "metadata": _NOTEBOOK_META,
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def create_quickstart_notebook() -> Path:
    """Write the master quick-start notebook."""
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    nb = build_quickstart_notebook()
    out = NOTEBOOKS_DIR / "abirqu_quickstart.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  [quickstart] → {out.name}")
    return out


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    only_quickstart = "--only" in args and "quickstart" in args

    if only_quickstart:
        print("Generating quick-start notebook …")
        create_quickstart_notebook()
        return

    print("Converting tutorials → notebooks …")
    paths = convert_all_tutorials()
    print(f"Converted {len(paths)} tutorial(s).\n")

    print("Generating quick-start notebook …")
    create_quickstart_notebook()
    print("Done.")


if __name__ == "__main__":
    main()
