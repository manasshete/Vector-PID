#!/usr/bin/env python3
"""Run the Vector-PID FastAPI server."""
import os
import sys
from pathlib import Path

# Project root must be on PYTHONPATH so `import src` works (including uvicorn reload workers).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ["PYTHONPATH"] = str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT / "src")],
    )
