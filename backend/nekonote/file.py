"""File and folder operations for nekonote scripts.

Usage::

    from nekonote import file

    file.copy("src.txt", "dst.txt")
    files = file.list_files("dir/", pattern="*.xlsx")
    text = file.read_text("data.txt")
"""

from __future__ import annotations

import glob as _glob
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from nekonote.errors import FileNotFoundError as NkFileNotFoundError


def _require_exists(path: str, action: str) -> Path:
    p = Path(path)
    if not p.exists():
        parent = p.parent
        nearby: list[str] = []
        if parent.is_dir():
            nearby = [f.name for f in parent.iterdir()][:20]
        raise NkFileNotFoundError(
            f"File not found: {path}",
            action=action,
            context={"path": str(p.resolve()), "nearby_files": nearby},
            suggestion=f"Check path. Files in {parent}: {', '.join(nearby[:5])}" if nearby else "",
        )
    return p


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


def copy(src: str, dst: str) -> str:
    """Copy a file. Returns destination path."""
    _require_exists(src, "file.copy")
    shutil.copy2(src, dst)
    return str(Path(dst).resolve())


def move(src: str, dst: str) -> str:
    """Move a file. Returns destination path."""
    _require_exists(src, "file.move")
    shutil.move(src, dst)
    return str(Path(dst).resolve())


def delete(path: str) -> None:
    """Delete a file."""
    _require_exists(path, "file.delete")
    os.remove(path)


def rename(src: str, new_name: str) -> str:
    """Rename a file. *new_name* is just the filename, not a full path."""
    p = _require_exists(src, "file.rename")
    dst = p.parent / new_name
    p.rename(dst)
    return str(dst.resolve())


def exists(path: str) -> bool:
    """Check if a file or directory exists."""
    return Path(path).exists()


def get_info(path: str) -> dict[str, Any]:
    """Get file metadata."""
    p = _require_exists(path, "file.get_info")
    stat = p.stat()
    return {
        "name": p.name,
        "path": str(p.resolve()),
        "size": stat.st_size,
        "extension": p.suffix,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
    }


# ---------------------------------------------------------------------------
# Directory operations
# ---------------------------------------------------------------------------


def create_dir(path: str) -> str:
    """Create a directory (including parents)."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return str(p.resolve())


def delete_dir(path: str) -> None:
    """Delete a directory and all its contents."""
    _require_exists(path, "file.delete_dir")
    shutil.rmtree(path)


def list_files(directory: str, *, pattern: str = "*") -> list[str]:
    """List files in a directory matching *pattern*."""
    _require_exists(directory, "file.list_files")
    return sorted(str(p) for p in Path(directory).glob(pattern) if p.is_file())


def list_dirs(directory: str) -> list[str]:
    """List subdirectories in a directory."""
    _require_exists(directory, "file.list_dirs")
    return sorted(str(p) for p in Path(directory).iterdir() if p.is_dir())


# ---------------------------------------------------------------------------
# Text file operations
# ---------------------------------------------------------------------------


def read_text(path: str, *, encoding: str = "utf-8") -> str:
    """Read a text file."""
    _require_exists(path, "file.read_text")
    return Path(path).read_text(encoding=encoding)


def write_text(path: str, content: str, *, encoding: str = "utf-8") -> None:
    """Write a text file (overwrites)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding=encoding)


def append_text(path: str, content: str, *, encoding: str = "utf-8") -> None:
    """Append to a text file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding=encoding) as f:
        f.write(content)


# ---------------------------------------------------------------------------
# ZIP operations
# ---------------------------------------------------------------------------


def zip(archive: str, files: list[str]) -> str:
    """Create a ZIP archive from a list of file paths."""
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            _require_exists(f, "file.zip")
            zf.write(f, Path(f).name)
    return str(Path(archive).resolve())


def unzip(archive: str, dest: str = ".") -> str:
    """Extract a ZIP archive to *dest*."""
    _require_exists(archive, "file.unzip")
    Path(dest).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(dest)
    return str(Path(dest).resolve())
