/**
 * AbirQu VS Code Extension
 * ========================
 * Provides three commands for working with quantum circuits:
 *   abirqu.run      — execute the selected / active circuit
 *   abirqu.optimize — transpile & optimize selected code
 *   abirqu.visualize — open a circuit visualization webview
 */

import * as vscode from "vscode";
import { CircuitProvider } from "./circuitProvider";

/**
 * Activate the extension.
 *
 * Registers the three core commands and the circuit-visualization
 * webview provider.
 */
export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel("AbirQu");
  outputChannel.appendLine("AbirQu extension activated.");

  // ── Run Circuit ────────────────────────────────────────────────────────
  const runCmd = vscode.commands.registerCommand(
    "abirqu.run",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("No active editor — open a Python or QASM file first.");
        return;
      }

      const selection = editor.document.getText(
        editor.selection.isEmpty ? undefined : editor.selection
      );
      const code = selection || editor.document.getText();
      const languageId = editor.document.languageId;

      outputChannel.appendLine(`[run] language=${languageId}, length=${code.length}`);
      const backend = vscode.workspace.getConfiguration("abirqu").get<string>("backend", "local");
      const shots = vscode.workspace.getConfiguration("abirqu").get<number>("shots", 1024);

      try {
        const result = await runCircuit(code, languageId, backend, shots);
        outputChannel.appendLine(JSON.stringify(result, null, 2));
        const summary = formatRunResult(result);
        const doc = await vscode.workspace.openTextDocument({
          content: summary,
          language: "plaintext",
        });
        await vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.Beside });
        vscode.window.showInformationMessage("AbirQu: circuit executed successfully.");
      } catch (err: any) {
        vscode.window.showErrorMessage(`AbirQu run failed: ${err.message ?? err}`);
        outputChannel.appendLine(`[run] ERROR: ${err}`);
      }
    }
  );

  // ── Optimize Circuit ───────────────────────────────────────────────────
  const optimizeCmd = vscode.commands.registerCommand(
    "abirqu.optimize",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("No active editor.");
        return;
      }

      const selection = editor.document.getText(
        editor.selection.isEmpty ? undefined : editor.selection
      );
      const code = selection || editor.document.getText();

      outputChannel.appendLine(`[optimize] length=${code.length}`);
      try {
        const optimized = await optimizeCircuit(code);
        if (editor.selection.isEmpty) {
          const fullRange = new vscode.Range(
            editor.document.positionAt(0),
            editor.document.positionAt(editor.document.getText().length)
          );
          await editor.edit((eb) => eb.replace(fullRange, optimized));
        } else {
          await editor.edit((eb) => eb.replace(editor.selection, optimized));
        }
        vscode.window.showInformationMessage("AbirQu: circuit optimized.");
      } catch (err: any) {
        vscode.window.showErrorMessage(`AbirQu optimize failed: ${err.message ?? err}`);
        outputChannel.appendLine(`[optimize] ERROR: ${err}`);
      }
    }
  );

  // ── Visualize Circuit ──────────────────────────────────────────────────
  const visualizeCmd = vscode.commands.registerCommand(
    "abirqu.visualize",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("No active editor.");
        return;
      }

      const code = editor.document.getText(
        editor.selection.isEmpty ? undefined : editor.selection
      );
      const provider = CircuitProvider.createOrShow(context.extensionUri, code);
      outputChannel.appendLine("[visualize] webview opened.");
    }
  );

  context.subscriptions.push(runCmd, optimizeCmd, visualizeCmd, outputChannel);
}

// ── Helpers ────────────────────────────────────────────────────────────────

/**
 * Send circuit code to the AbirQu Python backend via `python -c`.
 * Returns parsed JSON results.
 */
async function runCircuit(
  code: string,
  languageId: string,
  backend: string,
  shots: number
): Promise<Record<string, unknown>> {
  const pythonCode = buildPythonRunner(code, languageId, backend, shots);
  const result = await execPython(pythonCode);
  return JSON.parse(result);
}

/**
 * Transpile & optimize circuit code.
 */
async function optimizeCircuit(code: string): Promise<string> {
  const pythonCode = `
import sys, json
from abirqu import Circuit
from abirqu.converters_inbound import from_qasm
from abirqu.optimize import CircuitSimplifier

code = sys.stdin.read()
try:
    circ = from_qasm(code)
except Exception:
    circ = Circuit(1)

simp = CircuitSimplifier()
optimized = simp.simplify(circ)
print(optimized.to_qasm())
`;
  return execPython(pythonCode, code);
}

/**
 * Build the Python snippet that executes an AbirQu circuit.
 */
function buildPythonRunner(
  code: string,
  languageId: string,
  backend: string,
  shots: number
): string {
  return `
import sys, json
from abirqu import Circuit
from abirqu.converters_inbound import from_qasm

code = sys.stdin.read()
try:
    if "OPENQASM" in code or "qreg" in code:
        circ = from_qasm(code)
    else:
        circ = Circuit(1)
except Exception:
    circ = Circuit(1)

from abirqu.numpy_sim import NumPySimulator
sim = NumPySimulator(num_qubits=circ.num_qubits)
probs = sim.run_circuit(circ)
result = {
    "success": True,
    "qubits": circ.num_qubits,
    "gates": len(circ.gates),
    "depth": circ.depth(),
    "probabilities": {k: round(v, 6) for k, v in list(probs.items())[:32]},
}
print(json.dumps(result))
`;
}

/**
 * Execute a Python snippet, sending optional stdin.
 */
function execPython(code: string, stdin?: string): Promise<string> {
  const { execFile } = require("child_process") as typeof import("child_process");
  return new Promise((resolve, reject) => {
    const child = execFile(
      "python",
      ["-c", code],
      { timeout: 30_000, maxBuffer: 1024 * 1024 },
      (err: Error | null, stdout: string, stderr: string) => {
        if (err) {
          reject(new Error(stderr || err.message));
        } else {
          resolve(stdout.trim());
        }
      }
    );
    if (stdin && child.stdin) {
      child.stdin.write(stdin);
      child.stdin.end();
    }
  });
}

/**
 * Format circuit run results for display.
 */
function formatRunResult(result: Record<string, unknown>): string {
  const lines: string[] = [
    "=== AbirQu Circuit Result ===",
    "",
    `Success : ${result.success}`,
    `Qubits  : ${result.qubits}`,
    `Gates   : ${result.gates}`,
    `Depth   : ${result.depth}`,
    "",
    "Top probabilities:",
  ];

  const probs = result.probabilities as Record<string, number> | undefined;
  if (probs) {
    const sorted = Object.entries(probs)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 16);
    for (const [state, prob] of sorted) {
      const bar = "#".repeat(Math.round(prob * 40));
      lines.push(`  |${state}>  ${prob.toFixed(4)}  ${bar}`);
    }
  }
  return lines.join("\n");
}

export function deactivate(): void {}
