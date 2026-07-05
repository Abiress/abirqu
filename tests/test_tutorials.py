"""
Extract and run Python code blocks from tutorials/*.md files.
Each tutorial is a separate pytest test case.
Code blocks within a tutorial are concatenated and executed together.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

TUTORIALS_DIR = Path(__file__).resolve().parent.parent / "tutorials"


def extract_python_blocks(md_path: Path) -> str:
    """Extract all ```python code blocks from a markdown file and concatenate them."""
    text = md_path.read_text(encoding="utf-8")
    pattern = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)
    blocks = pattern.findall(text)
    return "\n\n".join(blocks)


def discover_tutorials() -> list[Path]:
    """Return sorted list of tutorial markdown files (excluding INDEX.md)."""
    tutorials = sorted(
        p for p in TUTORIALS_DIR.glob("*.md") if p.name != "INDEX.md"
    )
    return tutorials


def _sanitize_filename(name: str) -> str:
    """Turn a filename into a valid Python identifier for test IDs."""
    return re.sub(r"[^a-zA-Z0-9]", "_", Path(name).stem)


TutorialPath = pytest.param  # for clarity in parametrize


@pytest.mark.parametrize(
    "tutorial_path",
    discover_tutorials(),
    ids=[_sanitize_filename(p.name) for p in discover_tutorials()],
)
def test_tutorial_code(tutorial_path: Path):
    """Run all Python code blocks from a single tutorial as one script."""
    code = extract_python_blocks(tutorial_path)
    if not code.strip():
        pytest.skip(f"No Python code blocks found in {tutorial_path.name}")

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Code in {tutorial_path.name} failed with exit code {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# CLI entrypoint: allows running as `python tests/test_tutorials.py [batch]`
# Usage: python tests/test_tutorials.py 1 50   (run tutorials 1 through 50)
# ---------------------------------------------------------------------------

def _cli_main():
    """CLI mode: run tutorials by index range, report pass/fail."""
    tutorials = discover_tutorials()
    total = len(tutorials)

    if len(sys.argv) == 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    elif len(sys.argv) == 2:
        # single index
        start = end = int(sys.argv[1])
    else:
        start, end = 1, total

    batch = tutorials[max(0, start - 1) : end]
    passed, failed = 0, 0
    failures: list[str] = []

    for tutorial in batch:
        code = extract_python_blocks(tutorial)
        if not code.strip():
            print(f"  SKIP  {tutorial.name} (no code blocks)")
            continue
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(f"  PASS  {tutorial.name}")
            passed += 1
        else:
            print(f"  FAIL  {tutorial.name}")
            failures.append(tutorial.name)
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Tutorials {start}-{end}: {passed} passed, {failed} failed, {total} total")
    if failures:
        print(f"Failed: {', '.join(failures)}")
        sys.exit(1)


if __name__ == "__main__":
    _cli_main()
