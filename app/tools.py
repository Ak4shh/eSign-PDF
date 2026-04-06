from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.models import OverlayType


@dataclass
class PendingPlacement:
    """Represents a tool the user has armed but not yet placed on the page."""
    overlay_type: OverlayType
    text: Optional[str] = None
    font_name: Optional[str] = None
    color: Optional[str] = None
    image_path: Optional[str] = None


def validate_typed_signature(text: str, font_name: Optional[str]) -> Optional[str]:
    """Return an error message, or None if valid."""
    if not text or not text.strip():
        return "Please enter your signature text."
    if not font_name:
        return "Please select a signature font."
    return None


def validate_name(text: str) -> Optional[str]:
    if not text or not text.strip():
        return "Please enter a name."
    return None


def validate_date(text: str) -> Optional[str]:
    if not text or not text.strip():
        return "Please enter a date."
    return None


def validate_signature_image(image_path: Optional[str]) -> Optional[str]:
    if not image_path:
        return "Please select a signature image."
    return None
