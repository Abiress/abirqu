"""
Extract and run Python code blocks from README.md.
Ensures all README code examples are executable against the real package.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

README_PATH = Path(__file__).resolve().parent.parent / "README.md"


def extract_python_blocks(md_path: Path) -> list[tuple[str, str]]:
    """Extract all ```python code blocks with their section headers."""
    text = md_path.read_text(encoding="utf-8")
    blocks = []

    # Find all headers and their code blocks
    lines = text.split("\n")
    current_header = ""
    in_code_block = False
    code_lines = []

    for line in lines:
        # Track headers
        if line.startswith("### ") or line.startswith("## "):
            current_header = line.lstrip("#").strip()

        # Track code blocks
        if line.strip() == "```python" and not in_code_block:
            in_code_block = True
            code_lines = []
        elif line.strip() == "```" and in_code_block:
            in_code_block = False
            code = "\n".join(code_lines)
            if code.strip():
                blocks.append((current_header, code))
        elif in_code_block:
            code_lines.append(line)

    return blocks


def test_readme_code_blocks():
    """Run each Python code block from README.md as a separate test."""
    blocks = extract_python_blocks(README_PATH)
    assert len(blocks) > 0, "No Python code blocks found in README.md"

    failures = []
    for header, code in blocks:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            failures.append(
                f"--- {header} ---\n"
                f"Exit code: {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

    assert len(failures) == 0, (
        f"{len(failures)} README code block(s) failed:\n\n"
        + "\n\n".join(failures)
    )


if __name__ == "__main__":
    blocks = extract_python_blocks(README_PATH)
    print(f"Found {len(blocks)} Python code blocks in README.md\n")
    passed, failed = 0, 0
    for header, code in blocks:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(f"  PASS  {header}")
            passed += 1
        else:
            print(f"  FAIL  {header}")
            print(f"        {result.stderr.strip().split(chr(10))[-1]}")
            failed += 1
    print(f"\n{'=' * 50}")
    print(f"README code blocks: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
