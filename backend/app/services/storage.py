from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4


def get_storage_root() -> Path:
    configured_root = os.getenv("VOXMIND_STORAGE_DIR")
    return Path(configured_root) if configured_root else Path(__file__).resolve().parents[3] / "storage"


def save_uploaded_file(file_obj: BinaryIO, original_filename: str, folder: str = "uploads") -> str:
    root = get_storage_root() / folder
    root.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_filename).suffix.lower() or ".bin"
    filename = f"{uuid4().hex}{suffix}"
    target = root / filename

    with target.open("wb") as destination:
        destination.write(file_obj.read())

    return f"{folder}/{filename}"
