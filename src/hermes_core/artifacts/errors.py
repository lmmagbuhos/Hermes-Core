from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ArtifactValidationError(Exception):
    code: str
    message: str
    path: str | None = None

    def to_detail(self) -> dict[str, Any]:
        detail: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.path is not None:
            detail["path"] = self.path
        return detail
