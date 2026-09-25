from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    upload_dir: Path
    max_upload_mb: int = 10
    app_name: str = "Data Quality Command Center"

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(__file__).resolve().parents[1]
        return cls(
            database_path=Path(os.getenv("DATABASE_PATH", root / "data" / "quality.db")),
            upload_dir=Path(os.getenv("UPLOAD_DIR", root / "data" / "uploads")),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10")),
        )
