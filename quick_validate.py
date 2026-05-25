#!/usr/bin/env python3
"""Quick structural checks for the zero-api-html-image skill."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
ASSETS = ROOT / "assets"
TEMPLATES_DIR = ASSETS / "templates"
DEMO_DATA_DIR = ASSETS / "demo-data"
DEMOS_DIR = ASSETS / "demos"

sys.path.insert(0, str(SCRIPTS))

import build_template_gallery  # noqa: E402
import render_html_image  # noqa: E402


EXPECTED_ORDER = [
    "warm-steps",
    "dark-stats",
    "xiaohongshu-nature",
    "xiaohongshu-cover",
    "comparison",
    "linear-clean",
    "terminal-grid",
    "pixel-art",
    "consulting-report",
    "tech-poster",
]

FIXED_SIZE = {
    "xiaohongshu-nature": (1080, 1440),
    "xiaohongshu-cover": (1080, 1440),
}


def fail(message: str) -> None:
    raise AssertionError(message)


def check_file(path: Path) -> None:
    if not path.exists():
        fail(f"Missing file: {path.relative_to(ROOT)}")


def check_core_files() -> None:
    for relative in [
        "SKILL.md",
        "requirements.txt",
        "docs/DEPLOYMENT.md",
        "scripts/doctor.py",
        "scripts/render_html_image.py",
        "scripts/build_template_gallery.py",
        "assets/demos/template-gallery.png",
    ]:
        check_file(ROOT / relative)


def check_template_registration() -> None:
    gallery_styles = [name for _, name, _ in build_template_gallery.TEMPLATES]
    if gallery_styles != EXPECTED_ORDER:
        fail(f"Gallery order changed: {gallery_styles}")

    registered = set(render_html_image.STYLES)
    expected = set(EXPECTED_ORDER)
    if registered != expected:
        fail(f"Renderer styles mismatch. expected={sorted(expected)} actual={sorted(registered)}")

    for style in EXPECTED_ORDER:
        check_file(TEMPLATES_DIR / f"{style}.html")
        check_file(DEMO_DATA_DIR / f"{style}.json")
        check_file(DEMOS_DIR / f"{style}.png")


def check_demo_json_and_html() -> None:
    for style in EXPECTED_ORDER:
        data_path = DEMO_DATA_DIR / f"{style}.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        html = render_html_image.render_html(style, data)
        if "$" in html:
            fail(f"Unresolved template placeholder in rendered HTML for {style}")
        if "<html" not in html or "</html>" not in html:
            fail(f"Rendered HTML is incomplete for {style}")


def check_skill_rules() -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    required_phrases = [
        "Ask exactly one question per assistant turn",
        "Ask title first",
        "Ask for signature/brand",
        "assets/demos/template-gallery.png",
        "CONTENT_BOTTOM_PADDING",
        "TRIM_BOTTOM_PADDING",
        "This skill is portable by design",
        "docs/DEPLOYMENT.md",
        "Lobster",
        "Do not hard-code Codex-only browser APIs",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if missing:
        fail(f"SKILL.md missing required guidance: {missing}")


def check_demo_dimensions() -> None:
    try:
        from PIL import Image
    except ImportError:
        print("WARN: Pillow is unavailable; skipping PNG dimension checks.")
        return

    for style in EXPECTED_ORDER:
        image = Image.open(DEMOS_DIR / f"{style}.png")
        width, height = image.size
        if style in FIXED_SIZE:
            if (width, height) != FIXED_SIZE[style]:
                fail(f"{style}.png must be {FIXED_SIZE[style]}, got {(width, height)}")
        elif width != 1080:
            fail(f"{style}.png must be 1080px wide, got {width}")
        elif height < 900:
            fail(f"{style}.png looks too short for an adaptive content template: {height}px")

    gallery = Image.open(DEMOS_DIR / "template-gallery.png")
    if gallery.width < 900 or gallery.height < 3000:
        fail(f"template-gallery.png has unexpected dimensions: {gallery.size}")


def main() -> None:
    checks = [
        check_core_files,
        check_template_registration,
        check_demo_json_and_html,
        check_skill_rules,
        check_demo_dimensions,
    ]
    for check in checks:
        check()
    print("OK: zero-api-html-image quick validation passed.")


if __name__ == "__main__":
    main()
