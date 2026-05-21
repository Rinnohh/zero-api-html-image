#!/usr/bin/env python3
"""Render structured content through HTML templates, optionally screenshot as PNG."""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from string import Template
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "assets" / "templates"
STYLES = {
    "warm-steps": "warm-steps.html",
    "dark-stats": "dark-stats.html",
    "xiaohongshu-nature": "xiaohongshu-nature.html",
    "comparison": "comparison.html",
    "xiaohongshu-cover": "xiaohongshu-cover.html",
    "linear-clean": "linear-clean.html",
    "terminal-grid": "terminal-grid.html",
    "pixel-art": "pixel-art.html",
    "consulting-report": "consulting-report.html",
    "tech-poster": "tech-poster.html",
}
STYLE_SIZES = {
    "warm-steps": (1080, 900),
    "dark-stats": (1080, 900),
    "xiaohongshu-nature": (1080, 1440),
    "comparison": (1080, 1580),
    "xiaohongshu-cover": (1080, 1440),
    "linear-clean": (1080, 900),
    "terminal-grid": (1080, 900),
    "pixel-art": (1080, 900),
    "consulting-report": (1080, 900),
    "tech-poster": (1080, 900),
}
FIXED_SIZE_STYLES = {"xiaohongshu-cover", "xiaohongshu-nature"}
CONTENT_BOTTOM_PADDING = 96
TRIM_BOTTOM_PADDING = 72


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def list_items(items: list[Any], numbered: bool = False) -> str:
    rows = []
    for index, item in enumerate(items, start=1):
        text = esc(item)
        if numbered:
            rows.append(f'<li class="step"><span class="num">{index}</span><span class="step-text">{text}</span></li>')
        else:
            rows.append(f"<li>{text}</li>")
    return "\n".join(rows)


def stats_html(stats: list[Any]) -> str:
    rows = []
    for stat in stats:
        if isinstance(stat, dict):
            value = esc(stat.get("value", ""))
            label = esc(stat.get("label", ""))
        else:
            value = esc(stat)
            label = ""
        rows.append(f'<div class="stat-box"><div class="stat">{value}</div><div class="stat-label">{label}</div></div>')
    return "\n".join(rows)


def tags_html(tags: list[Any]) -> str:
    return "\n".join(f'<span class="tag">{esc(tag)}</span>' for tag in tags)


def metric_html(metrics: list[Any]) -> str:
    rows = []
    for item in metrics:
        if isinstance(item, dict):
            value = esc(item.get("value", ""))
            label = esc(item.get("label", ""))
        else:
            value = esc(item)
            label = ""
        rows.append(f'<div class="metric"><strong>{value}</strong><span>{label}</span></div>')
    return "\n".join(rows)


def sections_html(sections: list[Any]) -> str:
    rows = []
    for section in sections:
        if isinstance(section, dict):
            heading = esc(section.get("heading") or section.get("title") or "")
            body = esc(section.get("body") or section.get("text") or "")
        else:
            heading = ""
            body = esc(section)
        rows.append(f'<article class="section"><h2>{heading}</h2><p>{body}</p></article>')
    return "\n".join(rows)


def topic_cards_html(items: list[Any]) -> str:
    cards = []
    for index, item in enumerate(items[:5], start=1):
        if isinstance(item, dict):
            title = esc(item.get("title") or item.get("heading") or "")
            tag = esc(item.get("tag") or item.get("label") or "")
        else:
            title = esc(item)
            tag = ""
        cards.append(f'<article class="index-card"><div class="num">{index:02d}</div><h3>{title}</h3><span class="pill">{tag}</span></article>')
    return "\n".join(cards)


def detail_panels_html(sections: list[Any]) -> str:
    panels = []
    for section in sections[:4]:
        if isinstance(section, dict):
            heading = esc(section.get("heading") or section.get("title") or "")
            label = esc(section.get("label") or section.get("tag") or "")
            body = esc(section.get("body") or section.get("text") or "")
            bullets = section.get("items") or []
        else:
            heading = ""
            label = ""
            body = esc(section)
            bullets = []
        panels.append(
            '<article class="panel">'
            '<div class="section-head">'
            f'<h2>{heading}</h2><span class="eng">{label}</span>'
            '</div>'
            f'<p>{body}</p>'
            f'<ul>{list_items(bullets)}</ul>'
            '</article>'
        )
    return "\n".join(panels)


def magazine_steps_html(items: list[Any]) -> str:
    rows = []
    for index, item in enumerate(items[:4], start=1):
        text = esc(item.get("text") if isinstance(item, dict) else item)
        rows.append(f'<div class="step"><div class="num">{index}</div><div class="step-text">{text}</div></div>')
    return "\n".join(rows)


def highlight_text(text: Any, highlights: list[Any]) -> str:
    rendered = esc(text)
    for highlight in highlights[:3]:
        key = str(highlight or "").strip()
        if not key:
            continue
        safe_key = esc(key)
        rendered = rendered.replace(safe_key, f'<span class="hot">{safe_key}</span>', 1)
    return rendered


def xhs_title_html(data: dict[str, Any]) -> str:
    title = data.get("title") or "小红书封面标题"
    keywords = data.get("keywords") or data.get("highlightKeywords") or data.get("highlight_keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]
    return highlight_text(title, keywords)


def xhs_items_html(items: list[Any]) -> str:
    rows = []
    for index, item in enumerate(items[:5], start=1):
        if isinstance(item, dict):
            text = item.get("text") or item.get("body") or ""
            highlights = item.get("highlights") or item.get("highlight") or []
            if isinstance(highlights, str):
                highlights = [highlights]
            body = highlight_text(text, highlights)
        else:
            body = esc(item)
        rows.append(f'<li><span class="num">{index}</span><span class="li-text">{body}</span></li>')
    return "\n".join(rows)


def linebreak_text(value: Any) -> str:
    return esc(value).replace("\n", "<br>")


def nature_title_html(data: dict[str, Any]) -> str:
    title = str(data.get("title") or "自然意境封面")
    highlight = str(data.get("titleHighlight") or data.get("title_highlight") or "").strip()
    escaped = esc(title)
    if highlight and highlight in title:
        return escaped.replace(esc(highlight), f'<span class="warm">{esc(highlight)}</span>', 1)
    parts = title.split(" ", 1)
    if len(parts) == 2:
        return f'<span class="warm">{esc(parts[0])}</span>{esc(parts[1])}'
    return escaped


def colored_vs_title(title: Any) -> str:
    text = esc(title or "方案 A vs 方案 B")
    for marker in (" vs ", " VS ", " Vs "):
        if marker in text:
            left, right = text.split(marker, 1)
            return f"{left} <span>vs</span> {right}"
    return text


def percent(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    if text.endswith("%"):
        return text
    if text.isdigit():
        return f"{text}%"
    return fallback


def comparison_values(data: dict[str, Any], side: str) -> dict[str, str]:
    prefix = "left" if side == "left" else "right"
    items = data.get(f"{prefix}Items") or data.get(f"{prefix}_items") or []
    if not isinstance(items, list):
        items = []
    defaults = {
        "left": {
            "icon": "◎",
            "title": "方案 A",
            "tagline": "适合探索与发散",
            "bar_label": "版式可控度",
            "bar_value": "约 1x",
            "bar_width": "34%",
            "point": items[0] if len(items) > 0 else "自由度高，但标题、列表、对齐和留白每次都可能变化。",
            "fit_label": "谁更适合",
            "fit": items[1] if len(items) > 1 else "需要插画、氛围、概念视觉、不可预期的创意探索。",
            "note": items[2] if len(items) > 2 else "有惊喜，但不一定适合放大量中文和固定信息结构。",
        },
        "right": {
            "icon": "&lt;/&gt;",
            "title": "方案 B",
            "tagline": "适合结构化信息表达",
            "bar_label": "版式可控度",
            "bar_value": "约 3x",
            "bar_width": "82%",
            "point": items[0] if len(items) > 0 else "颜色、字号、间距、对齐和模块位置都能写死，批量生成也能保持统一。",
            "fit_label": "谁更适合",
            "fit": items[1] if len(items) > 1 else "需要中文清晰、风格一致、可复用、低成本的信息表达。",
            "note": items[2] if len(items) > 2 else "换内容不换风格，适合公众号、社群、报告和产品说明。",
        },
    }[prefix]

    def pick(camel: str, snake: str, default: Any) -> Any:
        return data.get(f"{prefix}{camel}") or data.get(f"{prefix}_{snake}") or default

    return {
        f"{prefix}_icon": esc(pick("Icon", "icon", defaults["icon"])),
        f"{prefix}_title": esc(pick("Title", "title", defaults["title"])),
        f"{prefix}_tagline": esc(pick("Tagline", "tagline", defaults["tagline"])),
        f"{prefix}_bar_label": esc(pick("BarLabel", "bar_label", defaults["bar_label"])),
        f"{prefix}_bar_value": esc(pick("BarValue", "bar_value", defaults["bar_value"])),
        f"{prefix}_bar_width": esc(percent(pick("BarWidth", "bar_width", defaults["bar_width"]), defaults["bar_width"])),
        f"{prefix}_point": esc(pick("Point", "point", defaults["point"])),
        f"{prefix}_fit_label": esc(pick("FitLabel", "fit_label", defaults["fit_label"])),
        f"{prefix}_fit": esc(pick("Fit", "fit", defaults["fit"])),
        f"{prefix}_note": esc(pick("Note", "note", defaults["note"])),
    }


def render_html(style: str, data: dict[str, Any]) -> str:
    template_path = TEMPLATE_DIR / STYLES[style]
    template = Template(template_path.read_text(encoding="utf-8"))
    common = {
        "eyebrow": esc(data.get("eyebrow") or data.get("label") or "HTML Screenshot"),
        "title": esc(data.get("title") or "未命名标题"),
        "subtitle": esc(data.get("subtitle") or data.get("summary") or ""),
        "brand": esc(data.get("brand") or ""),
    }

    values: dict[str, str] = dict(common)
    if style == "warm-steps":
        items = data.get("topics") or data.get("items", [])
        values["digest"] = esc(data.get("digest") or "KNOWLEDGE DIGEST · VOL. 01")
        values["meta"] = esc(data.get("meta") or "知识地图 / 方法 / 输出")
        values["side_one_label"] = esc(data.get("sideOneLabel") or data.get("side_one_label") or "内容索引")
        values["side_one_title"] = esc(data.get("sideOneTitle") or data.get("side_one_title") or f"{len(items) or 5} 个主题")
        values["side_one_body"] = esc(data.get("sideOneBody") or data.get("side_one_body") or "提炼核心主题，形成可快速扫读的信息地图。")
        values["side_two_label"] = esc(data.get("sideTwoLabel") or data.get("side_two_label") or "最佳收益")
        values["side_two_title"] = esc(data.get("sideTwoTitle") or data.get("side_two_title") or "系统理解")
        values["side_two_body"] = esc(data.get("sideTwoBody") or data.get("side_two_body") or "把分散信息整理成能复用的判断和行动。")
        values["topics_html"] = topic_cards_html(items)
        values["panels_html"] = detail_panels_html(data.get("sections", []))
        values["callout"] = esc(data.get("callout") or "")
    elif style == "dark-stats":
        values["stats_html"] = stats_html(data.get("stats", []))
        values["items_html"] = list_items(data.get("items", []))
        values["tags_html"] = tags_html(data.get("tags", []))
    elif style == "comparison":
        values["comparison_title_html"] = colored_vs_title(data.get("title") or "方案 A vs 方案 B")
        values.update(comparison_values(data, "left"))
        values.update(comparison_values(data, "right"))
    elif style == "xiaohongshu-nature":
        background = data.get("backgroundUrl") or data.get("background_url") or (ROOT / "assets" / "images" / "xiaohongshu-nature-bg.jpg").as_uri()
        values["background_url"] = esc(background)
        values["nature_title_html"] = nature_title_html(data)
        values["kicker"] = esc(data.get("kicker") or "A QUIET METHOD")
        values["description"] = linebreak_text(data.get("description") or data.get("desc") or "")
        values["pill"] = esc(data.get("pill") or data.get("tag") or "笔记方法")
        values["side_note"] = esc(data.get("sideNote") or data.get("side_note") or "NATURE MOOD COVER")
        values["brand_subtitle"] = esc(data.get("brandSubtitle") or data.get("brand_subtitle") or data.get("authorDesc") or "")
    elif style == "linear-clean":
        values["issue"] = esc(data.get("issue") or data.get("eyebrow") or "HTML 生图方法论")
        values["watermark"] = esc(data.get("watermark") or "HTML IMAGE")
        values["subline"] = esc(data.get("subline") or "STRUCTURED CONTENT · BROWSER RENDER · ZERO API")
        values["steps_html"] = magazine_steps_html(data.get("items", []))
        values["core"] = esc(data.get("core") or "核心：系统化 > 手动做图")
        values["core_subtitle"] = esc(data.get("coreSubtitle") or data.get("core_subtitle") or "Visual Composition · 像素级可控")
        values["footer_left"] = esc(data.get("footerLeft") or data.get("footer_left") or "ZERO API IMAGE · HTML2IMAGE")
    elif style == "xiaohongshu-cover":
        values["author"] = esc(data.get("author") or data.get("name") or "归藏(guizang.ai)")
        values["author_desc"] = esc(data.get("authorDesc") or data.get("author_desc") or data.get("eyebrow") or "正儿八经学AI")
        values["avatar"] = esc(data.get("avatar") or "😊")
        values["title_html"] = xhs_title_html(data)
        values["items_html"] = xhs_items_html(data.get("items", []))
        values["tags_html"] = tags_html(data.get("tags", []))
    elif style in {"consulting-report", "tech-poster", "terminal-grid", "pixel-art"}:
        values["items_html"] = list_items(data.get("items", []))
        values["tags_html"] = tags_html(data.get("tags", []))
        values["metrics_html"] = metric_html(data.get("metrics") or data.get("stats") or [])
        values["sections_html"] = sections_html(data.get("sections", []))
    return template.safe_substitute(values)


async def screenshot(html_path: Path, output_path: Path, width: int, height: int, fixed_size: bool) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed; HTML was written but PNG screenshot was not captured.") from exc

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
        await page.goto(html_path.as_uri(), wait_until="networkidle")
        if fixed_size:
            await page.screenshot(path=str(output_path), full_page=False)
        else:
            content_height = await page.evaluate(content_height_script())
            screenshot_height = content_height + CONTENT_BOTTOM_PADDING
            await page.set_viewport_size({"width": width, "height": screenshot_height})
            await page.screenshot(path=str(output_path), full_page=False)
        await browser.close()


def chrome_path() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac_chrome.exists():
        return str(mac_chrome)
    return None


def chrome_screenshot(html_path: Path, output_path: Path, width: int, height: int, fixed_size: bool) -> None:
    browser = chrome_path()
    if not browser:
        raise RuntimeError("No Playwright package or Chrome/Chromium executable found; HTML was written but PNG screenshot was not captured.")

    actual_height = height if fixed_size else measure_page_height_with_chrome(browser, html_path, width, height) + CONTENT_BOTTOM_PADDING
    command = [
        browser,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-crash-reporter",
        "--hide-scrollbars",
        f"--window-size={width},{actual_height}",
        f"--screenshot={output_path}",
        html_path.as_uri(),
    ]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        if detail:
            detail = f" Output: {detail[:800]}"
        raise RuntimeError(f"Chrome/Chromium screenshot failed with exit code {proc.returncode}.{detail}")


def content_height_script() -> str:
    return """
    () => {
      const candidates = Array.from(document.body.children).filter(Boolean);
      let bottom = 0;
      for (const element of candidates) {
        const rect = element.getBoundingClientRect();
        bottom = Math.max(bottom, rect.bottom, element.scrollHeight || 0, element.offsetHeight || 0);
      }
      if (!bottom) {
        bottom = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
      }
      return Math.ceil(bottom);
    }
    """


def measure_page_height_with_chrome(browser: str, html_path: Path, width: int, height: int) -> int:
    script = """
    <script>
      window.addEventListener('load', () => {
        requestAnimationFrame(() => {
          const candidates = Array.from(document.body.children).filter(Boolean);
          let bottom = 0;
          for (const element of candidates) {
            const rect = element.getBoundingClientRect();
            bottom = Math.max(bottom, rect.bottom, element.scrollHeight || 0, element.offsetHeight || 0);
          }
          if (!bottom) {
            bottom = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
          }
          const h = Math.ceil(bottom);
          document.title = 'HEIGHT:' + h;
          const marker = document.createElement('meta');
          marker.setAttribute('name', 'zero-api-capture-height');
          marker.setAttribute('content', String(h));
          document.head.appendChild(marker);
        });
      });
    </script>
    """
    source = html_path.read_text(encoding="utf-8")
    if "</body>" in source:
        source = source.replace("</body>", script + "\n</body>", 1)
    else:
        source += script
    measure_path = html_path.with_name(f"{html_path.stem}.measure.html")
    measure_path.write_text(source, encoding="utf-8")

    try:
        proc = subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                f"--window-size={width},{height}",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=1500",
                "--dump-dom",
                measure_path.as_uri(),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return height
    finally:
        try:
            measure_path.unlink()
        except OSError:
            pass

    match = re.search(r'name="zero-api-capture-height" content="(\d+)"', proc.stdout)
    if not match:
        match = re.search(r"<title>HEIGHT:(\d+)</title>", proc.stdout)
    return int(match.group(1)) if match else height


def trim_bottom_whitespace(image_path: Path, tolerance: int = 8, padding: int = TRIM_BOTTOM_PADDING) -> None:
    try:
        from PIL import Image
    except ImportError:
        return

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception:
        return

    width, height = image.size
    background = image.getpixel((width - 2, height - 2))

    def is_background(pixel: tuple[int, int, int]) -> bool:
        return all(abs(pixel[i] - background[i]) <= tolerance for i in range(3))

    bottom = height - 1
    sample_step = max(1, width // 120)
    min_content_ratio = 0.08
    for y in range(height - 1, -1, -1):
        sampled = 0
        non_background = 0
        for x in range(0, width, sample_step):
            sampled += 1
            if not is_background(image.getpixel((x, y))):
                non_background += 1
        if sampled and non_background / sampled >= min_content_ratio:
            bottom = min(height, y + padding)
            break

    if 0 < bottom < height and height - bottom > padding:
        image.crop((0, 0, width, bottom)).save(image_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an HTML/CSS template to a PNG screenshot.")
    parser.add_argument("--style", choices=sorted(STYLES), default="warm-steps")
    parser.add_argument("--data", required=True, help="Path to a JSON data file.")
    parser.add_argument("--out-dir", default="/tmp/zero-api-html-image")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--html-name", default="card.html")
    parser.add_argument("--png-name", default="output.png")
    parser.add_argument("--html-only", action="store_true", help="Only write HTML. Use this when another agent runtime will handle browser navigation and screenshot capture.")
    args = parser.parse_args()

    data_path = Path(args.data).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(data_path.read_text(encoding="utf-8"))
    default_width, default_height = STYLE_SIZES[args.style]
    width = args.width or default_width
    height = args.height or default_height
    fixed_size = args.style in FIXED_SIZE_STYLES
    html_content = render_html(args.style, data)
    html_path = out_dir / args.html_name
    png_path = out_dir / args.png_name
    html_path.write_text(html_content, encoding="utf-8")

    if args.html_only:
        print(json.dumps({"html": str(html_path), "png": None, "browser_url": html_path.as_uri()}, ensure_ascii=False, indent=2))
        return

    warnings = []
    try:
        asyncio.run(screenshot(html_path, png_path, width, height, fixed_size))
    except RuntimeError as exc:
        warnings.append(str(exc))
        try:
            chrome_screenshot(html_path, png_path, width, height, fixed_size)
        except (RuntimeError, subprocess.CalledProcessError) as chrome_exc:
            warnings.append(str(chrome_exc))

    if png_path.exists() and not fixed_size:
        trim_bottom_whitespace(png_path)

    result = {"html": str(html_path), "png": str(png_path) if png_path.exists() else None}
    if warnings and not png_path.exists():
        result["warning"] = " ".join(warnings)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
