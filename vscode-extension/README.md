# AbirQu — VS Code Extension

Run, optimize, and visualize quantum circuits directly from VS Code.

## Features

| Command | Description |
|---------|-------------|
| **AbirQu: Run Circuit** | Execute the selected (or full) circuit via the local AbirQu simulator and display results. |
| **AbirQu: Optimize Circuit** | Transpile & simplify the selected circuit code in-place. |
| **AbirQu: Visualize Circuit** | Open an SVG-based circuit diagram in a webview panel. |

## Requirements

- Python 3.10+ with `abirqu` installed (`pip install -e .` from the repo root)
- The extension shells out to `python -c …` — ensure `python` is on your `PATH`.

## Usage

1. Open any `.py` or `.qasm` file.
2. Select a region of circuit code (or leave the cursor elsewhere for the full file).
3. Open the Command Palette (`Ctrl+Shift+P`) and run one of the AbirQu commands.

### Keyboard shortcuts (suggested)

```json
{ "key": "ctrl+shift+r", "command": "abirqu.run" }
{ "key": "ctrl+shift+o", "command": "abirqu.optimize" }
{ "key": "ctrl+shift+v", "command": "abirqu.visualize" }
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `abirqu.backend` | `local` | Backend to use (`local`, `ibm`, `aws`, `azure`, `google`). |
| `abirqu.shots` | `1024` | Default number of measurement shots. |

## License

MIT
