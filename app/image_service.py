from __future__ import annotations
import os
from typing import Optional, Tuple

from PySide6.QtGui import QPixmap

from app.settings import SUPPORTED_IMAGE_EXTENSIONS


def validate_image_path(path: str) -> Optional[str]:
    """Return an error message or None if the file is usable."""
    if not path:
        return "No image file selected."
    if not os.path.isfile(path):
        return f"File not found: {path}"
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        return (
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
        )
    return None


def load_preview_pixmap(path: str) -> Tuple[Optional[QPixmap], Optional[str]]:
    """
    Load the image at *path* and return (pixmap, None) on success,
    or (None, error_message) on failure.
    """
    error = validate_image_path(path)
    if error:
        return None, error

    pixmap = QPixmap(path)
    if pixmap.isNull():
        return None, f"Could not load image: {path}"
    return pixmap, None
