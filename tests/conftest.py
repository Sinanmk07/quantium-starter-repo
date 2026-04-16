"""
Prepare Chromedriver on PATH for dash_duo (Selenium 4.2 from dash[testing]).

Caches a matching Chrome-for-Testing chromedriver under tests/bin/ (gitignored).
"""

from __future__ import annotations

import io
import os
import platform
import re
import stat
import subprocess
import sys
import zipfile
from pathlib import Path
from shutil import which
from urllib.error import URLError
from urllib.request import urlopen

import pytest

_CFT_BASE = "https://storage.googleapis.com/chrome-for-testing-public"
_FALLBACK_CHROME_VERSION = "131.0.6778.204"


def _strip_proxy_env() -> None:
    for key in list(os.environ):
        if "proxy" in key.lower():
            os.environ.pop(key, None)


def _chromedriver_slug() -> str:
    sysname = sys.platform
    machine = platform.machine().lower()
    if sysname == "darwin":
        return "mac-arm64" if machine == "arm64" else "mac-x64"
    if sysname == "linux":
        return "linux64"
    if sysname == "win32":
        return "win64"
    raise RuntimeError(f"Unsupported platform for UI tests: {sysname}/{machine}")


def _detect_chrome_version() -> str:
    """Return full version string (e.g. 147.0.7727.56) for Chrome-for-Testing URL."""
    if sys.platform == "darwin":
        plist = Path("/Applications/Google Chrome.app/Contents/Info.plist")
        if plist.is_file():
            import plistlib

            with plist.open("rb") as f:
                info = plistlib.load(f)
            ver = info.get("CFBundleShortVersionString")
            if ver and re.match(r"^\d+\.\d+\.\d+\.\d+$", ver):
                return str(ver)
    for cmd in ("google-chrome", "chromium", "chromium-browser"):
        path = which(cmd)
        if path:
            try:
                out = subprocess.check_output([path, "--version"], text=True, timeout=5)
                m = re.search(r"(\d+\.\d+\.\d+\.\d+)", out)
                if m:
                    return m.group(1)
            except (OSError, subprocess.SubprocessError):
                continue
    return _FALLBACK_CHROME_VERSION


def _download_chromedriver(dest_dir: Path, chrome_version: str) -> Path:
    slug = _chromedriver_slug()
    zip_name = f"chromedriver-{slug}.zip"
    url = f"{_CFT_BASE}/{chrome_version}/{slug}/{zip_name}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ("chromedriver.exe" if sys.platform == "win32" else "chromedriver")

    _strip_proxy_env()
    try:
        with urlopen(url, timeout=120) as resp:  # noqa: S310 — Google CfT URL
            data = resp.read()
    except URLError as e:
        raise RuntimeError(
            f"Could not download chromedriver from {url!r} ({e}). "
            "Install Google Chrome, set CHROMEDRIVER_PATH, or check your network."
        ) from e

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        candidates = [
            n
            for n in names
            if (n.endswith("/chromedriver") or n.endswith("/chromedriver.exe")) and not n.endswith("/")
        ]
        if not candidates:
            raise RuntimeError(f"No chromedriver binary in zip from {url!r}; members={names!r}")
        member = candidates[0]
        dest.write_bytes(zf.read(member))

    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def _cached_driver_matches_chrome(cache: Path, chrome_ver: str) -> bool:
    marker = cache.parent / ".chromedriver-for-chrome-version"
    if not cache.is_file():
        return False
    try:
        return marker.read_text(encoding="utf-8").strip() == chrome_ver
    except OSError:
        return False


def _write_version_marker(cache: Path, chrome_ver: str) -> None:
    marker = cache.parent / ".chromedriver-for-chrome-version"
    marker.write_text(chrome_ver + "\n", encoding="utf-8")


def _ensure_chromedriver_on_path() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    bin_dir = repo_root / "tests" / "bin"
    cache = bin_dir / ("chromedriver.exe" if sys.platform == "win32" else "chromedriver")

    explicit = os.environ.get("CHROMEDRIVER_PATH")
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if p.is_file():
            os.environ["PATH"] = str(p.parent) + os.pathsep + os.environ.get("PATH", "")
            return

    if which("chromedriver"):
        return

    chrome_ver = _detect_chrome_version()
    if cache.is_file() and _cached_driver_matches_chrome(cache, chrome_ver):
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
        return

    driver = _download_chromedriver(bin_dir, chrome_ver)
    _write_version_marker(driver, chrome_ver)
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def pytest_sessionstart(session: pytest.Session) -> None:
    try:
        _ensure_chromedriver_on_path()
    except RuntimeError as exc:
        if not which("chromedriver"):
            pytest.exit(
                f"{exc}\nInstall Google Chrome, add chromedriver to PATH, or set CHROMEDRIVER_PATH.",
                returncode=1,
            )
