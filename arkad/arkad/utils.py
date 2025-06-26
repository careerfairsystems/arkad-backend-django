from typing import Any
import uuid
from pathlib import Path


def unique_file_upload_path(subfolder: str, _: Any, filename: str) -> str:
    """
    Generates a unique file upload path for a given instance and filename.
    Works by creating a folder with a unique UUID and appending the original filename (and extension).
    """
    unique_folder = str(uuid.uuid4().hex)
    file_path = Path(subfolder) / unique_folder / filename
    return str(file_path)
