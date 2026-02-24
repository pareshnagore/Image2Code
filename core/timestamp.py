# timestamp.py

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional, Union

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ---------- Core parsing ----------

def parse_timestamp(
    value: Union[str, int, float, datetime, None]
) -> Optional[datetime]:
    """
    Normalize various timestamp formats to timezone-aware UTC datetime.
    Supports:
    - datetime
    - ISO8601 string
    - epoch seconds (int/float)
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return ensure_utc(value)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        try:
            # ISO8601 support
            dt = datetime.fromisoformat(value)
            return ensure_utc(dt)
        except ValueError:
            return None

    return None


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_epoch_seconds(dt: Optional[datetime]) -> Optional[float]:
    """Convert datetime to epoch seconds."""
    if dt is None:
        return None
    return ensure_utc(dt).timestamp()


# ---------- Image timestamp extraction ----------

def get_image_exif_timestamp(path: str) -> Optional[datetime]:
    """
    Extract timestamp from image EXIF metadata.
    Priority:
    DateTimeOriginal > DateTimeDigitized > DateTime
    """
    if not PIL_AVAILABLE:
        return None

    try:
        with Image.open(path) as img: # type: ignore
            exif = img.getexif()
            if not exif:
                return None

            exif_data = {
                TAGS.get(tag, tag): value # type: ignore
                for tag, value in exif.items()
            }

            for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                if key in exif_data:
                    # Format: "YYYY:MM:DD HH:MM:SS"
                    raw = exif_data[key]
                    dt = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
                    return dt.replace(tzinfo=timezone.utc)

    except Exception:
        pass

    return None


def get_filesystem_timestamp(path: str) -> Optional[datetime]:
    """Fallback: file modification time."""
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None


def get_image_timestamp(path: str) -> Optional[datetime]:
    """
    Unified timestamp extraction.
    Priority:
    1. EXIF timestamp
    2. Filesystem modified time
    """
    ts = get_image_exif_timestamp(path)
    if ts:
        return ts

    return get_filesystem_timestamp(path)


# ---------- Ordering helper ----------

def timestamp_sort_key(
    ts: Union[datetime, str, int, float, None]
) -> float:
    """
    Deterministic sortable key.
    Missing timestamps go to end.
    """
    parsed = parse_timestamp(ts)
    if parsed is None:
        return float("inf")
    return parsed.timestamp()