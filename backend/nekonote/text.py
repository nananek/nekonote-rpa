"""String and datetime utilities for nekonote scripts.

Usage::

    from nekonote import text

    text.replace("Hello World", "World", "Python")
    text.contains("hello world", "world")  # True
"""

from __future__ import annotations

import base64
import re
import urllib.parse
from datetime import datetime as _dt
from datetime import timedelta


# ---------------------------------------------------------------------------
# String operations
# ---------------------------------------------------------------------------


def replace(s: str, old: str, new: str) -> str:
    return s.replace(old, new)


def split(s: str, sep: str = ",") -> list[str]:
    return s.split(sep)


def join(parts: list[str], sep: str = ", ") -> str:
    return sep.join(parts)


def trim(s: str) -> str:
    return s.strip()


def to_upper(s: str) -> str:
    return s.upper()


def to_lower(s: str) -> str:
    return s.lower()


def length(s: str) -> int:
    return len(s)


def substring(s: str, start: int = 0, end: int | None = None) -> str:
    return s[start:end]


def contains(s: str, sub: str) -> bool:
    return sub in s


def starts_with(s: str, prefix: str) -> bool:
    return s.startswith(prefix)


def ends_with(s: str, suffix: str) -> bool:
    return s.endswith(suffix)


def pad_left(s: str, width: int, char: str = " ") -> str:
    return s.rjust(width, char)


def pad_right(s: str, width: int, char: str = " ") -> str:
    return s.ljust(width, char)


# ---------------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------------


def regex_match(s: str, pattern: str) -> list[str]:
    """Return all capture groups from the first match, or [] if no match."""
    m = re.search(pattern, s)
    if m:
        return list(m.groups()) if m.groups() else [m.group()]
    return []


def regex_find_all(s: str, pattern: str) -> list[str]:
    """Return all matches."""
    return re.findall(pattern, s)


def regex_replace(s: str, pattern: str, replacement: str) -> str:
    """Replace all matches of *pattern* with *replacement*."""
    return re.sub(pattern, replacement, s)


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------


def base64_encode(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def base64_decode(s: str) -> str:
    return base64.b64decode(s.encode("ascii")).decode("utf-8")


def url_encode(s: str) -> str:
    return urllib.parse.quote(s)


def url_decode(s: str) -> str:
    return urllib.parse.unquote(s)


# ---------------------------------------------------------------------------
# DateTime
# ---------------------------------------------------------------------------


def now(fmt: str = "") -> str:
    """Return current datetime. With *fmt*, format the output."""
    dt = _dt.now()
    if fmt:
        return dt.strftime(_convert_fmt(fmt))
    return dt.isoformat()


def today(fmt: str = "") -> str:
    """Return today's date."""
    dt = _dt.now().date()
    if fmt:
        return dt.strftime(_convert_fmt(fmt))
    return dt.isoformat()


def format_datetime(dt_str: str, fmt: str) -> str:
    """Format a datetime string."""
    dt = _parse_auto(dt_str)
    return dt.strftime(_convert_fmt(fmt))


def parse_datetime(s: str, fmt: str = "") -> str:
    """Parse a datetime string and return ISO format."""
    if fmt:
        dt = _dt.strptime(s, _convert_fmt(fmt))
    else:
        dt = _parse_auto(s)
    return dt.isoformat()


def add_time(dt_str: str, *, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    """Add time to a datetime string. Returns ISO format."""
    dt = _parse_auto(dt_str)
    dt += timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return dt.isoformat()


def diff_time(dt1_str: str, dt2_str: str) -> dict[str, float]:
    """Return the difference between two datetimes."""
    dt1 = _parse_auto(dt1_str)
    dt2 = _parse_auto(dt2_str)
    delta = dt1 - dt2
    total_seconds = delta.total_seconds()
    return {
        "days": delta.days,
        "hours": total_seconds / 3600,
        "minutes": total_seconds / 60,
        "seconds": total_seconds,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _convert_fmt(fmt: str) -> str:
    """Convert common format tokens (yyyy, MM, dd, HH, mm, ss) to strftime."""
    fmt = fmt.replace("yyyy", "%Y")
    fmt = fmt.replace("yy", "%y")
    fmt = fmt.replace("MM", "%m")
    fmt = fmt.replace("dd", "%d")
    fmt = fmt.replace("HH", "%H")
    fmt = fmt.replace("mm", "%M")
    fmt = fmt.replace("ss", "%S")
    return fmt


_ISO_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
]


def _parse_auto(s: str) -> _dt:
    """Try common datetime formats."""
    s = s.strip()
    for fmt in _ISO_FORMATS:
        try:
            return _dt.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {s!r}")
