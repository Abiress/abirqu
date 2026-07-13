/**
 * CircuitProvider — Webview panel for visualizing quantum circuits.
 *
 * Renders an HTML/SVG representation of the circuit within a VS Code
 * webview panel.  The panel is re-used across invocations.
 */

import * as vscode from "vscode";

export class CircuitProvider {
  public static currentPanel: CircuitProvider | undefined;
  private static readonly viewType = "abirqu.circuitView";

  private readonly _panel: vscode.WebviewPanel;
  private readonly _extensionUri: vscode.Uri;
  private _disposables: vscode.Disposable[] = [];

  /**
   * Show (or create) the visualization panel with the given circuit code.
   */
  public static createOrShow(extensionUri: vscode.Uri, circuitCode: string): CircuitProvider {
    const column = vscode.ViewColumn.Beside;

    if (CircuitProvider.currentPanel) {
      CircuitProvider.currentPanel._panel.reveal(column);
      CircuitProvider.currentPanel._update(circuitCode);
      return CircuitProvider.currentPanel;
    }

    const panel = vscode.window.createWebviewPanel(
      CircuitProvider.viewType,
      "AbirQu Circuit Viewer",
      column,
      { enableScripts: false }
    );

    CircuitProvider.currentPanel = new CircuitProvider(panel, extensionUri);
    CircuitProvider.currentPanel._update(circuitCode);
    return CircuitProvider.currentPanel;
  }

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this._panel = panel;
    this._extensionUri = extensionUri;
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
  }

  public dispose(): void {
    CircuitProvider.currentPanel = undefined;
    this._panel.dispose();
    for (const d of this._disposables) {
      d.dispose();
    }
  }

  /**
   * Parse circuit code into a simple gate list and render it as SVG.
   */
  private _update(circuitCode: string): void {
    const gates = this._parseCircuit(circuitCode);
    const svg = this._renderSVG(gates);
    this._panel.webview.html = this._wrapHTML(svg);
  }

  /**
   * Lightweight parser that extracts gate names and qubit indices from
   * QASM-like lines (e.g. `h q[0];`, `cx q[0],q[1];`).
   */
  private _parseCircuit(code: string): Array<{ name: string; qubits: number[] }> {
    const gates: Array<{ name: string; qubits: number[] }> = [];
    const lines = code.split("\n");
    for (const raw of lines) {
      const line = raw.trim();
      if (!line || line.startsWith("//") || line.startsWith("OPENQASM") || line.startsWith("include") || line.startsWith("qreg") || line.startsWith("creg")) {
        continue;
      }
      // Match patterns like: h q[0];  cx q[0],q[1];  rx(0.5) q[0];
      const match = line.match(/^(\w+)(?:\([^)]*\))?\s+(.+);/);
      if (match) {
        const name = match[1].toLowerCase();
        const qubitStrs = match[2].match(/q\[(\d+)\]/g) || [];
        const qubits = qubitStrs.map((s) => parseInt(s.replace(/\D/g, ""), 10));
        if (qubits.length > 0) {
          gates.push({ name, qubits });
        }
      }
    }
    return gates;
  }

  /**
   * Render the gate list as an SVG circuit diagram.
   */
  private _renderSVG(gates: Array<{ name: string; qubits: number[] }>): string {
    if (gates.length === 0) {
      return `<p style="color:#999;">No gates detected. Paste a QASM circuit to visualize.</p>`;
    }

    const numQubits = Math.max(...gates.flatMap((g) => g.qubits)) + 1;
    const wireY = (q: number) => 40 + q * 50;
    const gateSpacing = 70;
    const startX = 60;
    const svgWidth = startX + gates.length * gateSpacing + 40;
    const svgHeight = wireY(numQubits - 1) + 40;

    const parts: string[] = [];

    // Wires
    for (let q = 0; q < numQubits; q++) {
      const y = wireY(q);
      parts.push(
        `<line x1="20" y1="${y}" x2="${svgWidth - 20}" y2="${y}" stroke="#555" stroke-width="1.5"/>`
      );
      parts.push(`<text x="5" y="${y + 5}" font-size="12" fill="#ccc">q${q}</text>`);
    }

    // Gates
    const qubitLastX: number[] = new Array(numQubits).fill(startX);
    for (let i = 0; i < gates.length; i++) {
      const g = gates[i];
      const cx = Math.max(...g.qubits.map((q) => qubitLastX[q])) + gateSpacing;
      const color = g.name === "cx" || g.name === "cnot" ? "#4fc3f7" : g.name === "h" ? "#81c784" : "#ffb74d";

      for (const q of g.qubits) {
        qubitLastX[q] = cx;
        const y = wireY(q);
        // Box
        parts.push(
          `<rect x="${cx - 20}" y="${y - 16}" width="40" height="32" rx="4" fill="${color}" fill-opacity="0.25" stroke="${color}"/>`
        );
        parts.push(
          `<text x="${cx}" y="${y + 5}" text-anchor="middle" font-size="13" fill="#eee" font-family="monospace">${g.name}</text>`
        );
      }

      // CNOT control dot + line
      if (g.qubits.length === 2 && (g.name === "cx" || g.name === "cnot")) {
        const [c, t] = g.qubits;
        const cy1 = wireY(c);
        const cy2 = wireY(t);
        parts.push(`<line x1="${cx}" y1="${cy1}" x2="${cx}" y2="${cy2}" stroke="${color}" stroke-width="2"/>`);
        parts.push(`<circle cx="${cx}" cy="${cy1}" r="4" fill="${color}"/>`);
      }
    }

    return `<svg width="${svgWidth}" height="${svgHeight}" xmlns="http://www.w3.org/2000/svg">\n${parts.join("\n")}\n</svg>`;
  }

  /**
   * Wrap SVG content in a minimal HTML page.
   */
  private _wrapHTML(svgBody: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <style>
    body { margin: 0; padding: 16px; background: #1e1e1e; color: #eee; font-family: sans-serif; }
    svg  { display: block; max-width: 100%; height: auto; }
    h2   { margin: 0 0 12px; font-size: 16px; color: #90caf9; }
  </style>
</head>
<body>
  <h2>AbirQu Circuit Visualization</h2>
  ${svgBody}
</body>
</html>`;
  }
}
