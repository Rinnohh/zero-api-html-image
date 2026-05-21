#!/usr/bin/env python3
"""Build one numbered template-selection gallery from demo PNG files."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEMOS = ROOT / "assets" / "demos"
OUTPUT = DEMOS / "template-gallery.png"

TEMPLATES = [
    ("01", "warm-steps", "复古知识地图"),
    ("02", "dark-stats", "深色数据卡片"),
    ("03", "xiaohongshu-nature", "小红书自然意境风"),
    ("04", "xiaohongshu-cover", "小红书封面"),
    ("05", "comparison", "磨砂玻璃对比图"),
    ("06", "linear-clean", "杂志风封面"),
    ("07", "terminal-grid", "终端监控风"),
    ("08", "pixel-art", "8-bit 像素风"),
    ("09", "consulting-report", "咨询报告"),
    ("10", "tech-poster", "科技海报"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size, index=1 if bold else 0)
            except Exception:
                continue
    return ImageFont.load_default()


def crop_and_fit(image: Image.Image, width: int, height: int) -> Image.Image:
    source = image.convert("RGB")
    ratio = max(width / source.width, height / source.height)
    resized = source.resize((int(source.width * ratio), int(source.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = 0
    return resized.crop((left, top, left + width, top + height))


def main() -> None:
    cell_w = 460
    preview_h = 560
    caption_h = 138
    gap = 34
    margin = 54
    cols = 2
    rows = (len(TEMPLATES) + cols - 1) // cols
    title_h = 162

    width = margin * 2 + cols * cell_w + (cols - 1) * gap
    height = margin * 2 + title_h + rows * (preview_h + caption_h) + (rows - 1) * gap
    canvas = Image.new("RGB", (width, height), "#f6f7fb")
    draw = ImageDraw.Draw(canvas)

    title_font = font(42, bold=True)
    text_font = font(25, bold=True)
    small_font = font(19)
    num_font = font(25, bold=True)

    draw.text((margin, margin), "选择一个 HTML 生图模板", fill="#151923", font=title_font)
    draw.text((margin, margin + 58), "图片高度会按照内容灵活调整", fill="#2f7a4e", font=text_font)
    draw.text((margin, margin + 96), "回复编号即可，例如：选 04", fill="#687085", font=small_font)

    start_y = margin + title_h
    for index, (number, name, label) in enumerate(TEMPLATES):
        row = index // cols
        col = index % cols
        x = margin + col * (cell_w + gap)
        y = start_y + row * (preview_h + caption_h + gap)

        draw.rounded_rectangle((x, y, x + cell_w, y + preview_h + caption_h), radius=18, fill="#ffffff", outline="#d9dee8", width=2)

        image_path = DEMOS / f"{name}.png"
        preview = crop_and_fit(Image.open(image_path), cell_w, preview_h)
        mask = Image.new("L", (cell_w, preview_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, cell_w, preview_h + 24), radius=18, fill=255)
        canvas.paste(preview, (x, y), mask)

        caption_y = y + preview_h + 24
        draw.text((x + 24, caption_y), f"{number}  {label}", fill="#151923", font=text_font)
        draw.text((x + 24, caption_y + 42), name, fill="#687085", font=small_font)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
