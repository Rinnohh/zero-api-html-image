#!/usr/bin/env python3
"""Diagnose portability requirements for zero-api-html-image."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import render_html_image  # noqa: E402


def status(ok: bool, label: str, detail: str = "") -> bool:
    mark = "OK" if ok else "WARN"
    suffix = f" - {detail}" if detail else ""
    print(f"{mark}: {label}{suffix}")
    return ok


def find_chrome() -> str | None:
    browser = render_html_image.chrome_path()
    if browser:
        return browser
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def check_core_files() -> bool:
    required = [
        ROOT / "SKILL.md",
        ROOT / "quick_validate.py",
        ROOT / "docs" / "DEPLOYMENT.md",
        ROOT / "scripts" / "render_html_image.py",
        ROOT / "scripts" / "build_template_gallery.py",
        ROOT / "assets" / "templates" / "warm-steps.html",
        ROOT / "assets" / "demo-data" / "warm-steps.json",
        ROOT / "assets" / "demos" / "template-gallery.png",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    return status(not missing, "core skill files", ", ".join(missing) if missing else "complete")


def check_python() -> bool:
    version = ".".join(str(part) for part in sys.version_info[:3])
    return status(sys.version_info >= (3, 9), "Python version", version)


def check_pillow() -> bool:
    found = importlib.util.find_spec("PIL") is not None
    return status(found, "Pillow package", "required for gallery and PNG dimension validation")


def check_playwright_package() -> bool:
    found = importlib.util.find_spec("playwright") is not None
    return status(found, "Playwright Python package", "optional direct PNG capture path")


def check_playwright_browser() -> bool:
    if importlib.util.find_spec("playwright") is None:
        return status(False, "Playwright Chromium browser", "Playwright package is not installed")

    code = (
        "from playwright.sync_api import sync_playwright\n"
        "with sync_playwright() as p:\n"
        "    browser = p.chromium.launch()\n"
        "    browser.close()\n"
    )
    try:
        proc = subprocess.run([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        return status(False, "Playwright Chromium browser", "launch timed out")
    detail = "launchable" if proc.returncode == 0 else (proc.stderr or proc.stdout).strip().splitlines()[-1:]
    if isinstance(detail, list):
        detail = detail[0] if detail else "not launchable"
    return status(proc.returncode == 0, "Playwright Chromium browser", detail)


def check_chrome_binary() -> bool:
    browser = find_chrome()
    return status(bool(browser), "Chrome/Chromium binary", browser or "not found")


def check_html_render() -> bool:
    data_path = ROOT / "assets" / "demo-data" / "warm-steps.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    html = render_html_image.render_html("warm-steps", data)
    ok = "<html" in html and "</html>" in html and "$" not in html
    return status(ok, "demo HTML render", "warm-steps")


def check_direct_png_capture() -> bool:
    data_path = ROOT / "assets" / "demo-data" / "xiaohongshu-cover.json"
    with tempfile.TemporaryDirectory(prefix="zero-api-doctor-") as tmp:
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "render_html_image.py"),
            "--style",
            "xiaohongshu-cover",
            "--data",
            str(data_path),
            "--out-dir",
            tmp,
        ]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return status(False, "direct PNG capture", "capture timed out")
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result = {}
        png = result.get("png")
        ok = bool(png and Path(png).exists())
        warning = result.get("warning") or (proc.stderr.strip() if proc.stderr else "")
        return status(ok, "direct PNG capture", "available" if ok else warning or "not available")


def main() -> None:
    print("zero-api-html-image environment doctor")
    print(f"root: {ROOT}")
    checks = [
        check_python(),
        check_core_files(),
        check_pillow(),
        check_playwright_package(),
        check_playwright_browser(),
        check_chrome_binary(),
        check_html_render(),
        check_direct_png_capture(),
    ]
    print()
    if checks[-1]:
        print("RESULT: Direct PNG capture is available in this environment.")
    else:
        print("RESULT: HTML generation is available. Provide a runtime browser screenshot tool or install Playwright/Chromium for direct PNG capture.")


if __name__ == "__main__":
    main()
