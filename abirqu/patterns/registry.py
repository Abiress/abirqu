from dataclasses import dataclass
from typing import Callable, Dict

from ..circuit import Circuit


@dataclass
class RegisteredPattern:
    name: str
    builder: Callable[..., Circuit]
    description: str


class PatternRegistry:
    def __init__(self) -> None:
        self._patterns: Dict[str, RegisteredPattern] = {}

    def register(self, name: str, builder: Callable[..., Circuit], description: str = "") -> None:
        self._patterns[name] = RegisteredPattern(name=name, builder=builder, description=description)

    def build(self, name: str, *args, **kwargs) -> Circuit:
        if name not in self._patterns:
            raise KeyError(f"Unknown pattern: {name}")
        return self._patterns[name].builder(*args, **kwargs)

    def list_patterns(self) -> list[str]:
        return sorted(self._patterns.keys())
