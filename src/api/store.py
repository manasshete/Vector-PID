"""In-memory analysis and job state for the API server."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class AnalysisStore:
    _current: dict[str, Any] | None = None
    _jobs: dict[str, dict[str, Any]] = {}

    @classmethod
    def get_current(cls) -> dict[str, Any] | None:
        return cls._current

    @classmethod
    def set_current(cls, data: dict[str, Any]) -> None:
        cls._current = data

    @classmethod
    def load_from_disk(cls, path: Path) -> bool:
        if not path.is_file():
            return False
        cls._current = json.loads(path.read_text(encoding="utf-8"))
        return True

    @classmethod
    def create_job(cls) -> str:
        job_id = str(uuid4())
        cls._jobs[job_id] = {"status": "pending", "result": None, "error": None}
        return job_id

    @classmethod
    def get_job(cls, job_id: str) -> dict[str, Any] | None:
        return cls._jobs.get(job_id)

    @classmethod
    def complete_job(cls, job_id: str, result: dict[str, Any]) -> None:
        cls._jobs[job_id] = {"status": "completed", "result": result, "error": None}
        cls._current = result

    @classmethod
    def fail_job(cls, job_id: str, error: str) -> None:
        cls._jobs[job_id] = {"status": "failed", "result": None, "error": error}
