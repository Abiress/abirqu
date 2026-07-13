#!/usr/bin/env python3
"""
Auto-generate language bindings from the AbirQu Rust C API.

Reads ``src/c_api.rs``, parses ``#[no_mangle] pub extern "C"`` functions,
and produces idiomatic wrappers for C, Go, JavaScript/TypeScript, Python
(ctypes), and Java (JNI).

Optionally runs ``cargo build --release`` first to ensure a fresh shared
library is available.

Usage::

    python bindings/generate_bindings.py [--build] [--out DIR]

Copyright 2026 Abir Maheshwari
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

__all__ = [
    "BindingGenerator",
    "CApiFunction",
]

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
C_API_RS = ROOT / "src" / "c_api.rs"
DEFAULT_OUT = ROOT / "bindings" / "generated"


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class CApiFunction:
    """Parsed representation of a ``extern "C"`` function.

    Attributes:
        name: Function name (e.g. ``abirqu_simulator_create``).
        args: List of ``(type, name)`` tuples.
        return_type: C return type string.
        doc: Doc-comment text (may be multi-line).
    """

    name: str
    args: List[tuple[str, str]]
    return_type: str
    doc: str = ""


# ── Rust C API parser ─────────────────────────────────────────────────────────

def _parse_c_api(source: str) -> List[CApiFunction]:
    """Parse ``extern "C"`` functions from Rust source.

    Handles both single-line and multi-line signatures, with optional
    doc-comments (``/// ...``).
    """
    funcs: List[CApiFunction] = []
    lines = source.split("\n")

    i = 0
    doc = ""
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Collect doc comments
        if stripped.startswith("///"):
            doc_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("///"):
                doc_lines.append(lines[i].strip().lstrip("/ ").strip())
                i += 1
            doc = "\n".join(doc_lines)
            if i < len(lines):
                line = lines[i]
                stripped = line.strip()
            else:
                break

        # Skip blank lines
        if not stripped:
            i += 1
            continue

        # Strip leading attributes like #[no_mangle] before matching
        clean_line = re.sub(r'#\[.*?\]\s*', '', line)

        # Match: pub extern "C" fn name(…) -> RetType {
        # For multi-line signatures, accumulate lines until we see '{'.
        if re.search(r'extern\s+"C"\s+fn\s+\w+', clean_line):
            block = clean_line
            # Collect more lines if the opening '(' hasn't been closed yet
            depth = block.count("(") - block.count(")")
            while depth > 0 and i + 1 < len(lines):
                i += 1
                block += " " + lines[i]
                depth = block.count("(") - block.count(")")

            m = re.search(
                r'(?:pub\s+)?(?:unsafe\s+)?extern\s+"C"\s+fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\S+))?\s*\{',
                block,
            )
            if m:
                name = m.group(1)
                raw_args = m.group(2).strip()
                ret = (m.group(3) or "void").rstrip(":")

                args: list[tuple[str, str]] = []
                if raw_args:
                    for arg in raw_args.split(","):
                        arg = arg.strip()
                        if not arg:
                            continue
                        parts = arg.rsplit(":", 1)
                        if len(parts) == 2:
                            args.append((parts[0].strip(), parts[1].strip()))
                        else:
                            args.append(("_", arg))

                funcs.append(CApiFunction(name=name, args=args, return_type=ret, doc=doc))
                doc = ""

        i += 1

    return funcs


# ── C header generator ────────────────────────────────────────────────────────

def _generate_c_header(funcs: List[CApiFunction]) -> str:
    """Generate a C header file (``.h``)."""
    lines: list[str] = [
        "/* Auto-generated AbirQu C API header — do not edit manually. */",
        "#ifndef ABIRQU_H",
        "#define ABIRQU_H",
        "",
        "#include <stddef.h>",
        "#include <stdint.h>",
        "",
        "#ifdef __cplusplus",
        'extern "C" {',
        "#endif",
        "",
        "/* Opaque handle */",
        "typedef struct AbirQuSimulator* AbirQuSimulator;",
        "",
    ]

    for fn in funcs:
        if fn.doc:
            for dl in fn.doc.split("\n"):
                lines.append(f"/* {dl} */")
        args_str = ", ".join(f"{t} {n}" for t, n in fn.args) or "void"
        ret = fn.return_type if fn.return_type != "void" else "void"
        lines.append(f"{ret} {fn.name}({args_str});")
        lines.append("")

    lines += [
        "#ifdef __cplusplus",
        "}",
        "#endif",
        "",
        "#endif /* ABIRQU_H */",
        "",
    ]
    return "\n".join(lines)


# ── Go bindings generator ─────────────────────────────────────────────────────

def _generate_go_bindings(funcs: List[CApiFunction]) -> str:
    """Generate Go bindings with cgo preamble."""
    lib_name = "abirqu_core"
    lines: list[str] = [
        "// Auto-generated AbirQu Go bindings — do not edit manually.",
        "package abirqu",
        "",
        "/*",
        f'#cgo LDFLAGS: -l{lib_name}',
        '#include <stdlib.h>',
        '#include "abirqu.h"',
        "*/",
        '"C"',
        "import (",
        '    "C"',
        '    "unsafe"',
        ")",
        "",
    ]

    for fn in funcs:
        if fn.doc:
            for dl in fn.doc.split("\n"):
                lines.append(f"// {dl}")

        # Map C types → Go types
        go_args = []
        cgo_args = []
        for t, n in fn.args:
            if "Simulator" in t:
                go_args.append(f"{n} uintptr")
                cgo_args.append(f"C.AbirQuSimulator(unsafe.Pointer({n}))")
            elif t in ("u32",):
                go_args.append(f"{n} uint32")
                cgo_args.append(f"C.uint32_t({n})")
            elif t in ("u8",):
                go_args.append(f"{n} uint8")
                cgo_args.append(f"C.uint8_t({n})")
            elif t == "f64":
                go_args.append(f"{n} float64")
                cgo_args.append(f"C.double({n})")
            elif t == "usize":
                go_args.append(f"{n} uintptr")
                cgo_args.append(f"C.size_t({n})")
            elif "mut" in t and "f64" in t:
                go_args.append(f"{n} *float64")
                cgo_args.append(f"(*C.double)(unsafe.Pointer({n}))")
            elif "mut" in t and "u8" in t:
                go_args.append(f"{n} *byte")
                cgo_args.append(f"(*C.uint8_t)(unsafe.Pointer({n}))")
            else:
                go_args.append(f"{n} unsafe.Pointer")
                cgo_args.append(f"{n}")

        ret = fn.return_type
        go_ret = "void"
        if ret == "AbirQuSimulator" or "Simulator" in ret:
            go_ret = "uintptr"
        elif ret == "u32":
            go_ret = "uint32"
        elif ret == "usize":
            go_ret = "uintptr"
        elif ret == "f64":
            go_ret = "float64"
        elif ret != "void":
            go_ret = "uintptr"

        args_str = ", ".join(go_args)
        cgo_call = f"C.{fn.name}({', '.join(cgo_args)})"

        if go_ret == "void":
            lines.append(f"func {fn.name}({args_str}) {{")
            lines.append(f"    {cgo_call}")
        else:
            lines.append(f"func {fn.name}({args_str}) {go_ret} {{")

            if go_ret == "uintptr":
                lines.append(f"    return uintptr({cgo_call})")
            elif go_ret == "uint32":
                lines.append(f"    return uint32({cgo_call})")
            else:
                lines.append(f"    return {go_ret}({cgo_call})")

        lines.append("}")
        lines.append("")

    return "\n".join(lines)


# ── JavaScript / TypeScript bindings generator ────────────────────────────────

def _generate_js_bindings(funcs: List[CApiFunction]) -> str:
    """Generate JavaScript bindings using node-ffi-napi style."""
    lines: list[str] = [
        "// Auto-generated AbirQu JavaScript bindings — do not edit manually.",
        'const ffi = require("ffi-napi");',
        'const ref = require("ref-napi");',
        "",
        "const AbirQuSimulator = ref.types.void *;",
        "",
        "const lib = ffi.Library(__dirname + \"/../target/release/libabirqu_core\", {",
    ]

    for fn in funcs:
        js_ret = "void"
        if fn.return_type == "AbirQuSimulator" or "Simulator" in fn.return_type:
            js_ret = "AbirQuSimulator"
        elif fn.return_type == "u32":
            js_ret = "uint32"
        elif fn.return_type == "usize":
            js_ret = "size_t"
        elif fn.return_type == "f64":
            js_ret = "double"

        js_args = []
        for t, n in fn.args:
            if "Simulator" in t:
                js_args.append("AbirQuSimulator")
            elif t in ("u32",):
                js_args.append("uint32")
            elif t == "u8":
                js_args.append("uint8")
            elif t == "f64":
                js_args.append("double")
            elif t == "usize":
                js_args.append("size_t")
            elif "mut" in t:
                js_args.append("pointer")
            else:
                js_args.append("pointer")

        lines.append(
            f"    {fn.name}: [\"{js_ret}\", [{', '.join(js_args)}]],"
        )

    lines += [
        "});",
        "",
        "module.exports = lib;",
        "",
    ]
    return "\n".join(lines)


def _generate_ts_bindings(funcs: List[CApiFunction]) -> str:
    """Generate TypeScript type definitions."""
    lines: list[str] = [
        "// Auto-generated AbirQu TypeScript definitions — do not edit manually.",
        "",
        "type AbirQuSimulator = number;",
        "",
    ]

    for fn in funcs:
        if fn.doc:
            for dl in fn.doc.split("\n"):
                lines.append(f"// {dl}")

        ts_ret = "void"
        if fn.return_type == "AbirQuSimulator" or "Simulator" in fn.return_type:
            ts_ret = "AbirQuSimulator"
        elif fn.return_type == "u32":
            ts_ret = "number"
        elif fn.return_type == "usize":
            ts_ret = "number"
        elif fn.return_type == "f64":
            ts_ret = "number"

        ts_args = []
        for t, n in fn.args:
            if "Simulator" in t:
                ts_args.append(f"{n}: AbirQuSimulator")
            elif t in ("u32",):
                ts_args.append(f"{n}: number")
            elif t == "u8":
                ts_args.append(f"{n}: number")
            elif t == "f64":
                ts_args.append(f"{n}: number")
            elif t == "usize":
                ts_args.append(f"{n}: number")
            elif "mut" in t:
                ts_args.append(f"{n}: any")
            else:
                ts_args.append(f"{n}: any")

        lines.append(
            f"export function {fn.name}({', '.join(ts_args)}): {ts_ret};"
        )

    lines.append("")
    return "\n".join(lines)


# ── Python ctypes wrapper generator ───────────────────────────────────────────

def _generate_python_bindings(funcs: List[CApiFunction]) -> str:
    """Generate a Python ctypes wrapper module."""
    lines: list[str] = [
        '"""Auto-generated AbirQu Python ctypes bindings — do not edit manually."""',
        "",
        "import ctypes",
        "import os",
        "from pathlib import Path",
        "",
        "_LIB_DIR = Path(__file__).resolve().parent.parent",
        "# Try release first, then debug",
        "_LIB_NAMES = [",
        '    "libabirqu_core.so",',
        '    "abirqu_core.dll",',
        '    "libabirqu_core.dylib",',
        "]",
        "",
        "_lib = None",
        "for _name in _LIB_NAMES:",
        "    _path = _LIB_DIR / _name",
        "    if _path.exists():",
        "        _lib = ctypes.CDLL(str(_path))",
        "        break",
        "if _lib is None:",
        '    raise OSError("Could not find abirqu_core shared library")',
        "",
        "AbirQuSimulator = ctypes.c_void_p",
        "",
    ]

    for fn in funcs:
        # Map return type
        py_ret = "None"
        if fn.return_type == "AbirQuSimulator" or "Simulator" in fn.return_type:
            py_ret = "AbirQuSimulator"
        elif fn.return_type == "u32":
            py_ret = "ctypes.c_uint32"
        elif fn.return_type == "usize":
            py_ret = "ctypes.c_size_t"
        elif fn.return_type == "f64":
            py_ret = "ctypes.c_double"

        py_args = []
        for t, n in fn.args:
            if "Simulator" in t:
                py_args.append("AbirQuSimulator")
            elif t in ("u32",):
                py_args.append("ctypes.c_uint32")
            elif t == "u8":
                py_args.append("ctypes.c_uint8")
            elif t == "f64":
                py_args.append("ctypes.c_double")
            elif t == "usize":
                py_args.append("ctypes.c_size_t")
            elif "mut" in t and "f64" in t:
                py_args.append("ctypes.POINTER(ctypes.c_double)")
            elif "mut" in t and "u8" in t:
                py_args.append("ctypes.POINTER(ctypes.c_uint8)")
            else:
                py_args.append("ctypes.c_void_p")

        if fn.doc:
            for dl in fn.doc.split("\n"):
                lines.append(f"# {dl}")

        lines.append(f"_{fn.name} = _lib.{fn.name}")
        lines.append(f"_{fn.name}.restype = {py_ret}")
        lines.append(
            f"_{fn.name}.argtypes = [{', '.join(py_args)}]"
        )
        lines.append("")

    # Add a high-level wrapper class
    lines += [
        "",
        "class Simulator:",
        '    """High-level wrapper around the AbirQu C API."""',
        "",
        "    def __init__(self, num_qubits: int) -> None:",
        "        self._handle = _abirqu_simulator_create(ctypes.c_uint32(num_qubits))",
        "",
        "    def __del__(self) -> None:",
        "        if self._handle:",
        "            _abirqu_simulator_destroy(self._handle)",
        "",
        "    def reset(self) -> None:",
        "        _abirqu_simulator_reset(self._handle)",
        "",
        "    @property",
        "    def num_qubits(self) -> int:",
        "        return _abirqu_num_qubits(self._handle)",
        "",
        "    def h(self, q: int) -> None:",
        "        _abirqu_h(self._handle, ctypes.c_uint32(q))",
        "",
        "    def x(self, q: int) -> None:",
        "        _abirqu_x(self._handle, ctypes.c_uint32(q))",
        "",
        "    def y(self, q: int) -> None:",
        "        _abirqu_y(self._handle, ctypes.c_uint32(q))",
        "",
        "    def z(self, q: int) -> None:",
        "        _abirqu_z(self._handle, ctypes.c_uint32(q))",
        "",
        "    def rx(self, q: int, angle: float) -> None:",
        "        _abirqu_rx(self._handle, ctypes.c_uint32(q), ctypes.c_double(angle))",
        "",
        "    def ry(self, q: int, angle: float) -> None:",
        "        _abirqu_ry(self._handle, ctypes.c_uint32(q), ctypes.c_double(angle))",
        "",
        "    def rz(self, q: int, angle: float) -> None:",
        "        _abirqu_rz(self._handle, ctypes.c_uint32(q), ctypes.c_double(angle))",
        "",
        "    def cnot(self, ctrl: int, tgt: int) -> None:",
        "        _abirqu_cnot(self._handle, ctypes.c_uint32(ctrl), ctypes.c_uint32(tgt))",
        "",
        "    def cz(self, ctrl: int, tgt: int) -> None:",
        "        _abirqu_cz(self._handle, ctypes.c_uint32(ctrl), ctypes.c_uint32(tgt))",
        "",
        "    def get_probabilities(self) -> list[float]:",
        "        dim = _abirqu_hilbert_dim(self._handle)",
        "        buf = (ctypes.c_double * dim)()",
        "        _abirqu_get_probabilities(self._handle, buf)",
        "        return list(buf)",
        "",
    ]

    return "\n".join(lines)


# ── Java JNI wrapper generator ────────────────────────────────────────────────

def _generate_java_bindings(funcs: List[CApiFunction]) -> str:
    """Generate a Java JNI wrapper class."""
    lines: list[str] = [
        "/* Auto-generated AbirQu Java JNI wrapper — do not edit manually. */",
        "package com.abirqu;",
        "",
        "public class AbirQuSimulator {",
        "    private long handle;",
        "",
        "    static {",
        '        System.loadLibrary("abirqu_core");',
        "    }",
        "",
        "    public AbirQuSimulator(int numQubits) {",
        "        this.handle = nativeCreate(numQubits);",
        "    }",
        "",
        "    @Override",
        "    protected void finalize() throws Throwable {",
        "        if (handle != 0) {",
        "            nativeDestroy(handle);",
        "        }",
        "        super.finalize();",
        "    }",
        "",
    ]

    for fn in funcs:
        if fn.doc:
            for dl in fn.doc.split("\n"):
                lines.append(f"    // {dl}")

        # Map to Java types
        java_ret = "void"
        jni_ret = "void"
        if fn.return_type == "AbirQuSimulator" or "Simulator" in fn.return_type:
            java_ret = "long"
            jni_ret = "jlong"
        elif fn.return_type == "u32":
            java_ret = "int"
            jni_ret = "jint"
        elif fn.return_type == "usize":
            java_ret = "long"
            jni_ret = "jlong"
        elif fn.return_type == "f64":
            java_ret = "double"
            jni_ret = "jdouble"

        java_args = []
        jni_args = ["long handle"]
        for t, n in fn.args:
            camel = n[0].upper() + n[1:] if n else "arg"
            if "Simulator" in t:
                java_args.append(f"long {camel}")
                jni_args.append("jlong")
            elif t in ("u32",):
                java_args.append(f"int {camel}")
                jni_args.append("jint")
            elif t == "u8":
                java_args.append(f"byte {camel}")
                jni_args.append("jbyte")
            elif t == "f64":
                java_args.append(f"double {camel}")
                jni_args.append("jdouble")
            elif t == "usize":
                java_args.append(f"long {camel}")
                jni_args.append("jlong")
            else:
                java_args.append(f"long {camel}")
                jni_args.append("jlong")

        # Generate public method
        java_method = fn.name.replace("abirqu_", "")
        all_java_args = ", ".join(java_args) if java_args else ""
        lines.append(f"    public {java_ret} {java_method}({all_java_args}) {{")
        call_args = ["handle"]
        for t, n in fn.args:
            camel = n[0].upper() + n[1:] if n else "arg"
            call_args.append(camel)
        call = f"        return native{java_method}({', '.join(call_args)});" if java_ret != "void" else f"        native{java_method}({', '.join(call_args)});"
        lines.append(call)
        lines.append("    }")
        lines.append("")

        # Generate native method
        all_jni_args = ", ".join(jni_args)
        lines.append(f"    private native {jni_ret} native{java_method}({all_jni_args});")
        lines.append("")

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


# ── Main generator ────────────────────────────────────────────────────────────

class BindingGenerator:
    """Orchestrates parsing and generation of all language bindings.

    Usage::

        gen = BindingGenerator()
        gen.generate(build_first=True, output_dir=Path("bindings/generated"))

    This reads ``src/c_api.rs``, optionally runs ``cargo build --release``,
    and writes header / Go / JS / TS / Python / Java files into *output_dir*.
    """

    def __init__(self, api_source: Optional[Path] = None) -> None:
        self.api_source = api_source or C_API_RS
        self._functions: List[CApiFunction] = []

    @property
    def functions(self) -> List[CApiFunction]:
        if not self._functions:
            self._parse()
        return self._functions

    def _parse(self) -> None:
        """Parse the Rust C API source file."""
        source = self.api_source.read_text(encoding="utf-8")
        self._functions = _parse_c_api(source)
        print(f"Parsed {len(self._functions)} C API functions from {self.api_source.name}")

    def _run_cargo_build(self) -> bool:
        """Run ``cargo build --release`` and return success status."""
        print("Running cargo build --release …")
        try:
            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                print(f"[WARN] cargo build failed (exit {result.returncode}):")
                print(result.stderr[-2000:] if result.stderr else "(no output)")
                return False
            print("cargo build --release succeeded.")
            return True
        except FileNotFoundError:
            print("[WARN] cargo not found — skipping build step.")
            return False
        except subprocess.TimeoutExpired:
            print("[WARN] cargo build timed out after 300 s.")
            return False

    def generate(
        self,
        build_first: bool = False,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """Generate all bindings and write them to disk.

        Args:
            build_first: Run ``cargo build --release`` before generating.
            output_dir: Directory for output files.  Defaults to
                ``bindings/generated/``.

        Returns:
            Dict mapping language name to the output file path.
        """
        if build_first:
            self._run_cargo_build()

        if not self._functions:
            self._parse()

        out = output_dir or DEFAULT_OUT
        out.mkdir(parents=True, exist_ok=True)

        generated: Dict[str, Path] = {}

        # C header
        header = _generate_c_header(self._functions)
        p = out / "abirqu.h"
        p.write_text(header, encoding="utf-8")
        generated["c"] = p
        print(f"  → {p}")

        # Go
        go = _generate_go_bindings(self._functions)
        p = out / "abirqu.go"
        p.write_text(go, encoding="utf-8")
        generated["go"] = p
        print(f"  → {p}")

        # JavaScript
        js = _generate_js_bindings(self._functions)
        p = out / "abirqu.js"
        p.write_text(js, encoding="utf-8")
        generated["javascript"] = p
        print(f"  → {p}")

        # TypeScript
        ts = _generate_ts_bindings(self._functions)
        p = out / "abirqu.d.ts"
        p.write_text(ts, encoding="utf-8")
        generated["typescript"] = p
        print(f"  → {p}")

        # Python ctypes
        py = _generate_python_bindings(self._functions)
        p = out / "abirqu_ctypes.py"
        p.write_text(py, encoding="utf-8")
        generated["python"] = p
        print(f"  → {p}")

        # Java JNI
        java = _generate_java_bindings(self._functions)
        p = out / "AbirQuSimulator.java"
        p.write_text(java, encoding="utf-8")
        generated["java"] = p
        print(f"  → {p}")

        return generated


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate AbirQu language bindings from the Rust C API."
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run cargo build --release before generating.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory (default: bindings/generated/).",
    )
    args = parser.parse_args()

    gen = BindingGenerator()
    gen.generate(build_first=args.build, output_dir=args.out)
    print("\nDone.")


if __name__ == "__main__":
    main()
