"""
AbirQu Code Editor
Copyright 2026 Abir Maheshwari

Python code editor with quantum syntax highlighting and auto-completion.
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


QUANTUM_KEYWORDS = [
    'quantum', 'qubit', 'circuit', 'gate', 'measure', 'reset',
    'barrier', 'entangle', 'teleport', 'simulate', 'execute',
    'backend', 'hardware', 'noise', 'error', 'correction',
    'surface_code', 'stabilizer', 'syndrome', 'decoder',
    'tomography', 'benchmark', 'fidelity',
]

QUANTUM_GATES = [
    'H', 'X', 'Y', 'Z', 'S', 'T', 'Sdg', 'Tdg',
    'CNOT', 'CX', 'CY', 'CZ', 'CH', 'CSWAP',
    'SWAP', 'Toffoli', 'CCX', 'CCZ',
    'Rx', 'Ry', 'Rz', 'CRx', 'CRy', 'CRz',
    'U1', 'U2', 'U3', 'CU',
    'Measure', 'Reset', 'Barrier',
]

PYTHON_KEYWORDS = [
    'def', 'class', 'return', 'if', 'else', 'elif', 'for', 'while',
    'import', 'from', 'as', 'with', 'try', 'except', 'finally',
    'raise', 'pass', 'break', 'continue', 'yield', 'lambda',
    'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is',
]

BUILTIN_FUNCTIONS = [
    'print', 'len', 'range', 'int', 'float', 'complex', 'str',
    'list', 'dict', 'set', 'tuple', 'abs', 'round', 'max', 'min',
    'sum', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
    'isinstance', 'hasattr', 'getattr', 'setattr',
]


@dataclass
class SyntaxToken:
    """A highlighted token in the code."""
    text: str
    token_type: str  # 'keyword', 'gate', 'function', 'string', 'comment', 'number', 'operator', 'plain'
    start: int
    end: int

    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'type': self.token_type,
            'start': self.start,
            'end': self.end,
        }


@dataclass
class CompletionItem:
    """An auto-completion suggestion."""
    text: str
    category: str
    description: str = ''
    rank: int = 0

    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'category': self.category,
            'description': self.description,
            'rank': self.rank,
        }


@dataclass
class DiagnosticMessage:
    """A diagnostic message (error, warning, info)."""
    line: int
    column: int
    message: str
    severity: str = 'info'  # 'error', 'warning', 'info'

    def to_dict(self) -> Dict:
        return {
            'line': self.line,
            'column': self.column,
            'message': self.message,
            'severity': self.severity,
        }


class CodeEditor:
    """Quantum Python code editor with syntax highlighting."""

    def __init__(self):
        self.content: str = ''
        self.cursor_line: int = 0
        self.cursor_col: int = 0
        self.selection_start: Optional[Tuple[int, int]] = None
        self.selection_end: Optional[Tuple[int, int]] = None
        self.undo_stack: List[str] = []
        self.redo_stack: List[str] = []
        self.file_path: Optional[str] = None
        self.modified: bool = False
        self._callbacks = []

    def on(self, event: str, callback):
        self._callbacks.append((event, callback))

    def _emit(self, event: str, data: Any):
        for ev, cb in self._callbacks:
            if ev == event:
                try:
                    cb(data)
                except Exception:
                    pass

    def set_content(self, content: str):
        if self.content:
            self.undo_stack.append(self.content)
            self.redo_stack.clear()
        self.content = content
        self.modified = True
        self._emit('content_changed', content)

    def get_content(self) -> str:
        return self.content

    def insert_at_cursor(self, text: str):
        lines = self.content.split('\n')
        if self.cursor_line < len(lines):
            line = lines[self.cursor_line]
            lines[self.cursor_line] = line[:self.cursor_col] + text + line[self.cursor_col:]
            self.cursor_col += len(text)
            self.content = '\n'.join(lines)
            self.modified = True
            self._emit('content_changed', self.content)

    def delete_selection(self):
        if self.selection_start and self.selection_end:
            start_line, start_col = self.selection_start
            end_line, end_col = self.selection_end
            lines = self.content.split('\n')
            if start_line == end_line:
                line = lines[start_line]
                lines[start_line] = line[:start_col] + line[end_col:]
            else:
                lines[start_line] = lines[start_line][:start_col]
                lines[end_line] = lines[end_line][end_col:]
                lines = lines[:start_line + 1] + lines[end_line:]
            self.content = '\n'.join(lines)
            self.cursor_line = start_line
            self.cursor_col = start_col
            self.selection_start = None
            self.selection_end = None
            self.modified = True
            self._emit('content_changed', self.content)

    def undo(self) -> bool:
        if self.undo_stack:
            self.redo_stack.append(self.content)
            self.content = self.undo_stack.pop()
            self.modified = True
            self._emit('content_changed', self.content)
            return True
        return False

    def redo(self) -> bool:
        if self.redo_stack:
            self.undo_stack.append(self.content)
            self.content = self.redo_stack.pop()
            self.modified = True
            self._emit('content_changed', self.content)
            return True
        return False

    def highlight_syntax(self, content: Optional[str] = None) -> List[SyntaxToken]:
        text = content if content is not None else self.content
        tokens = []
        i = 0
        while i < len(text):
            if text[i] == '#':
                end = text.find('\n', i)
                if end == -1:
                    end = len(text)
                tokens.append(SyntaxToken(text[i:end], 'comment', i, end))
                i = end
            elif text[i] in ('"', "'"):
                quote = text[i]
                j = i + 1
                while j < len(text) and text[j] != quote:
                    if text[j] == '\\':
                        j += 1
                    j += 1
                j = min(j + 1, len(text))
                tokens.append(SyntaxToken(text[i:j], 'string', i, j))
                i = j
            elif text[i].isdigit() or (text[i] == '.' and i + 1 < len(text) and text[i+1].isdigit()):
                j = i
                while j < len(text) and (text[j].isdigit() or text[j] in '.xXeE+-'):
                    j += 1
                tokens.append(SyntaxToken(text[i:j], 'number', i, j))
                i = j
            elif text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]
                if word in QUANTUM_GATES:
                    tokens.append(SyntaxToken(word, 'gate', i, j))
                elif word in PYTHON_KEYWORDS or word in QUANTUM_KEYWORDS:
                    tokens.append(SyntaxToken(word, 'keyword', i, j))
                elif j < len(text) and text[j] == '(':
                    tokens.append(SyntaxToken(word, 'function', i, j))
                else:
                    tokens.append(SyntaxToken(word, 'plain', i, j))
                i = j
            elif text[i] in '+-*/%=<>!&|^~@':
                j = i + 1
                if j < len(text) and text[j] in '=<>!&|':
                    j += 1
                tokens.append(SyntaxToken(text[i:j], 'operator', i, j))
                i = j
            else:
                tokens.append(SyntaxToken(text[i], 'plain', i, i + 1))
                i += 1
        return tokens

    def get_completions(self, prefix: str = '') -> List[CompletionItem]:
        completions = []
        all_words = set()
        for word in QUANTUM_GATES:
            if word not in all_words:
                completions.append(CompletionItem(word, 'gate', f'Quantum gate: {word}', 0))
                all_words.add(word)
        for word in PYTHON_KEYWORDS + QUANTUM_KEYWORDS:
            if word not in all_words:
                completions.append(CompletionItem(word, 'keyword', f'Keyword: {word}', 1))
                all_words.add(word)
        for word in BUILTIN_FUNCTIONS:
            if word not in all_words:
                completions.append(CompletionItem(word, 'builtin', f'Builtin: {word}', 2))
                all_words.add(word)

        if prefix:
            prefix_lower = prefix.lower()
            completions = [c for c in completions if c.text.lower().startswith(prefix_lower)]
        completions.sort(key=lambda c: (c.rank, c.text))
        return completions

    def analyze_code(self) -> List[DiagnosticMessage]:
        diagnostics = []
        lines = self.content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('def ') and not stripped.endswith(':'):
                diagnostics.append(DiagnosticMessage(i, 0, 'Missing colon after function definition', 'warning'))
            if stripped.startswith('class ') and not stripped.endswith(':'):
                diagnostics.append(DiagnosticMessage(i, 0, 'Missing colon after class definition', 'warning'))
            if 'import' in stripped and 'as' not in stripped and 'from' not in stripped:
                parts = stripped.split()
                if len(parts) >= 2 and '.' in parts[1]:
                    diagnostics.append(DiagnosticMessage(i, 0, 'Consider using "as" alias for import', 'info'))
        return diagnostics

    def get_line_info(self, line: int) -> Dict:
        lines = self.content.split('\n')
        if 0 <= line < len(lines):
            return {
                'line': line,
                'content': lines[line],
                'length': len(lines[line]),
                'indent': len(lines[line]) - len(lines[line].lstrip()),
            }
        return {'line': line, 'content': '', 'length': 0, 'indent': 0}

    def get_render_data(self) -> Dict:
        tokens = self.highlight_syntax()
        diagnostics = self.analyze_code()
        return {
            'content': self.content,
            'tokens': [t.to_dict() for t in tokens],
            'diagnostics': [d.to_dict() for d in diagnostics],
            'cursor_line': self.cursor_line,
            'cursor_col': self.cursor_col,
            'modified': self.modified,
            'file_path': self.file_path,
            'line_count': len(self.content.split('\n')),
        }

    def save(self, path: Optional[str] = None) -> str:
        save_path = path or self.file_path or 'untitled.py'
        with open(save_path, 'w') as f:
            f.write(self.content)
        self.file_path = save_path
        self.modified = False
        return save_path

    def load(self, path: str) -> str:
        with open(path, 'r') as f:
            self.content = f.read()
        self.file_path = path
        self.modified = False
        self.undo_stack.clear()
        self.redo_stack.clear()
        return self.content

    def __len__(self):
        return len(self.content)

    def __repr__(self):
        lines = len(self.content.split('\n'))
        return f"CodeEditor(lines={lines}, modified={self.modified})"
