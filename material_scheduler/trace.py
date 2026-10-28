from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TraceRecorder:
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, node: str, update: dict[str, Any]) -> None:
        self.events.append({"node": node, "update": self._json_safe(update)})

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.events, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _json_safe(value: Any) -> Any:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
