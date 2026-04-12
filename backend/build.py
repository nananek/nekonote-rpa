"""Build script for packaging the backend with PyInstaller."""

import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
ENGINE_DIR = DIST / "nekonote-engine"


def get_playwright_browsers_path() -> Path:
    """Find the Playwright browsers directory."""
    import playwright
    pw_path = Path(playwright.__file__).parent / "driver" / "package" / ".local-browsers"
    if not pw_path.exists():
        # Try standard location
        import os
        ms_pw = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
        if ms_pw.exists():
            return ms_pw
    return pw_path


def build():
    print("=== Building Nekonote Engine ===")

    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "nekonote-engine",
        "--noconfirm",
        "--console",
        "--distpath", str(DIST),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT),
        # Hidden imports for dynamic modules
        "--hidden-import", "nekonote.engine.nodes.data",
        "--hidden-import", "nekonote.engine.nodes.control",
        "--hidden-import", "nekonote.engine.nodes.browser",
        "--hidden-import", "nekonote.engine.nodes.desktop",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        # Entry point
        str(ROOT / "nekonote" / "main.py"),
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Copy Playwright browsers
    print("\n=== Copying Playwright browsers ===")
    pw_browsers = get_playwright_browsers_path()
    dest_browsers = ENGINE_DIR / "ms-playwright"
    if pw_browsers.exists():
        # Only copy chromium
        for item in pw_browsers.iterdir():
            if "chromium" in item.name.lower():
                dest = dest_browsers / item.name
                print(f"Copying {item.name}...")
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
        # Set env var for Playwright
        print("Playwright browsers copied")
    else:
        print(f"WARNING: Playwright browsers not found at {pw_browsers}")

    print(f"\n=== Build complete: {ENGINE_DIR} ===")


if __name__ == "__main__":
    build()
