---
name: zero-api-html-image
description: Generate structured Chinese visual images with HTML/CSS templates and browser screenshots instead of image-generation APIs. Use when the user asks to "做成信息图", "生成信息图", "做成数据卡片", "生成封面", "做一张对比图", "微信群精华图", "公众号配图", "报告可视化卡片", or needs pixel-controlled text-heavy PNG output from titles, lists, stats, quotes, tables, or summaries.
---

# Zero API HTML Image

## Overview

Use HTML templates as deterministic image generators: convert user content into structured data, render a local HTML file, then use the current runtime's browser navigation and screenshot capability to produce a PNG. Prefer this skill for text-heavy Chinese graphics where layout consistency, exact typography, and zero image API cost matter.

This skill is portable by design. Its stable core is HTML generation; PNG capture is a runtime capability supplied by Codex, Hermes, OpenClaw, Lobster, Playwright, Chrome/Chromium, Browserless, or an equivalent browser screenshot service. Do not assume a specific account, local Mac app, or vendor-only browser API exists.

## Conversational Workflow

Default to a guided conversation. Ask exactly one question per assistant turn. Do not ask title, brand, content, and style in the same message. After the user answers, ask the next missing question. Do not jump straight to generation unless the user already explicitly confirmed the title, signature/brand, required content, and style.

Title and signature/brand are mandatory confirmation gates for every generated image. Even if a title or signature can be inferred from source content, ask the user to confirm it before generating. Ask title first, wait for the reply, then ask signature/brand in a separate turn. The user may reply "留空" for no signature.

When the user provides a source file such as Markdown, DOCX, PDF, spreadsheet, or report, first extract and summarize the content internally, then still follow the confirmation gates. Do not generate directly from a file until the user has confirmed title and signature/brand.

Collect information in this order:

1. Ask for the main goal or scene if unclear, for example "这张图主要想表达什么？"
2. Ask for `title` and require explicit confirmation.
3. Ask for `subtitle` or one-sentence summary, unless the user says no subtitle.
4. Ask for the scene-specific body content:
   - `warm-steps`: ask for 3-6 list items, or ask whether to extract items from supplied text.
   - `dark-stats`: ask for 1-4 key numbers/conclusions.
   - `comparison`: ask for the left side first; after the user answers, ask for the right side. Use the frosted-glass layout with two stacked glass panels by default.
5. Ask for signature/brand and require explicit confirmation. Accept "留空" as an intentional empty brand.
6. Show the single numbered template gallery image, then ask the user to choose one template by number. If the style is obvious, still show the gallery and ask for confirmation.
7. Create a JSON data file, render HTML, capture PNG with the available browser screenshot ability, then return the generated image.
8. If the user reports a visual defect such as missing signature, low-contrast footer, title overflow, unwanted wrapping, excessive whitespace, or poor crop, update the underlying template or script so future outputs inherit the fix; then regenerate the affected PNG and, when relevant, refresh `assets/demos/` and `template-gallery.png`.

When asking the user to choose a template, use the current runtime's supported image display format and show only:

- `assets/demos/template-gallery.png`

If the gallery image cannot be displayed, list the numbered options from Template Selection instead. Individual demo images remain available under `assets/demos/` for debugging or close inspection, but do not show all individual demos during the normal guided flow.

## Template Selection

Use these templates:

   - `01 warm-steps`: vintage newspaper / knowledge-map / long-form infographic for reading notes, learning summaries, article digests, and structured knowledge maps.
   - `02 dark-stats`: data cards, punchy conclusions, quote cards, social sharing.
   - `03 xiaohongshu-nature`: Xiaohongshu nature mood cover with dark photographic landscape background, poetic Chinese/English mixed typography, and immersive premium atmosphere.
   - `04 xiaohongshu-cover`: borderless 3:4 Xiaohongshu cover with text as the visual subject, oversized serif keywords, numbered takeaways, tags, and optional emoji/avatar.
   - `05 comparison`: frosted-glass comparison poster for tool comparisons, before/after summaries, decision explanations, and pros/cons analysis.
   - `06 linear-clean`: monochrome magazine-style editorial poster for methodology,观点表达, concept explainers, and premium narrative covers.
   - `07 terminal-grid`: terminal screen / black-green pixel / command-line monitor style for technical workflows, AI agents, automation, observability, and developer-tool introductions.
   - `08 pixel-art`: cozy farming RPG-inspired pixel style for gamified learning plans, quest logs, growth systems, community events, and playful product explainers.
   - `09 consulting-report`: restrained report-style poster for analysis, metrics, and executive summaries.
   - `10 tech-poster`: dark technical poster for engineering/product automation themes.

Map numeric replies to style names exactly. For example, `选 03` means `xiaohongshu-nature`, `选 04` means `xiaohongshu-cover`, and `选 05` means `comparison`.

## Data Shapes

Use these keys as needed:

```json
{
  "title": "标题",
  "subtitle": "副标题或一句话说明",
  "brand": "底部署名",
  "items": ["步骤一", "步骤二", "步骤三"],
  "stats": [{"value": "30秒", "label": "完成截图"}, {"value": "0元", "label": "API 成本"}],
  "tags": ["HTML", "浏览器截图"],
  "leftTitle": "方案 A",
  "leftTagline": "一句话定位",
  "leftBarValue": "约 1x",
  "leftBarWidth": "34%",
  "leftPoint": "核心特点",
  "leftFit": "适合对象",
  "leftNote": "补充说明",
  "rightTitle": "方案 B",
  "rightTagline": "一句话定位",
  "rightBarValue": "约 3x",
  "rightBarWidth": "82%",
  "rightPoint": "核心特点",
  "rightFit": "适合对象",
  "rightNote": "补充说明",
  "author": "作者名",
  "authorDesc": "作者简介",
  "avatar": "😊",
  "keywords": ["关键词一", "关键词二"],
  "kicker": "ENGLISH TITLE",
  "titleHighlight": "标题强调词",
  "description": "说明文字",
  "pill": "标签",
  "brandSubtitle": "品牌副标题",
  "sideNote": "边缘辅助信息"
}
```

## Source-To-Visual Summarization

For source reports or documents:

- Extract the strongest 3-6 metrics into `stats` or `metrics`.
- Convert long prose into 4-6 concise `items` or `sections`.
- Preserve dates, store names, cycle ranges, percentages, and money values exactly.
- Avoid putting raw table dumps into the image. Summarize the business meaning instead.
- For复盘/经营报告, prefer `02 dark-stats` for punchy data cards or `09 consulting-report` for more executive-report style.

## Script Usage

Create a JSON file under the user's working directory or `/tmp`, then render HTML:

```bash
python3 scripts/render_html_image.py --style warm-steps --data /path/to/data.json --out-dir /tmp/html-shot --html-only
```

Outputs:

- `card.html`: rendered HTML, useful for debugging.
- `browser_url`: `file://` URL for browser navigation.

Then use the current runtime's browser tools to navigate to `browser_url` and capture a full-page screenshot as PNG. Examples of equivalent capability names include browser navigation plus screenshot, Playwright navigation plus screenshot, Chrome/Chromium headless screenshot, Browserless screenshot APIs, or any OpenClaw/Hermes/Lobster browser screenshot primitive.

For local environments that support Python Playwright or Chrome/Chromium, omit `--html-only` to let the script attempt PNG capture:

```bash
python3 scripts/render_html_image.py --style warm-steps --data /path/to/data.json --out-dir /tmp/html-shot
```

The script uses Playwright if available, then falls back to local Chrome/Chromium headless. If browser capture is unavailable, it still writes `card.html`.

Run the environment doctor when installing this skill in a new runtime:

```bash
python3 scripts/doctor.py
```

For cloud deployment notes, see `docs/DEPLOYMENT.md`. A portable deployment must provide at least one of these screenshot paths:

- runtime browser tool that can open the generated `file://` URL or a locally served HTML URL and save PNG;
- Python Playwright with Chromium installed;
- Chrome/Chromium headless installed in the container;
- external browser screenshot service such as Browserless.

## Template Guidelines

- Keep output width near `1080px` unless the user requests another size.
- Use adaptive height for content templates: `01 warm-steps`, `02 dark-stats`, `05 comparison`, `06 linear-clean`, `07 terminal-grid`, `08 pixel-art`, `09 consulting-report`, and `10 tech-poster`. If content is short, capture only the content area with comfortable bottom padding instead of a fixed tall canvas.
- `render_html_image.py` uses `CONTENT_BOTTOM_PADDING = 96` when measuring adaptive-height templates, then crops with `TRIM_BOTTOM_PADDING` when needed. Measure the real content bottom from rendered body children so short images do not keep a large default-viewport blank area.
- For `01 warm-steps`, treat it as "复古报刊 / 知识地图 / 长图信息图", not as a simple step-list card. Prefer `topics` plus `sections` data for this template.
- For `03 xiaohongshu-nature`, use "小红书封面-自然意境风": dark moody landscape photography, subtle light and shadow, immersive natural atmosphere, premium restrained color, deep spatial layering, Chinese poetic mood blended with modern Western photographic composition, floating title over the landscape, Chinese/English mixed typography, large empty space balanced with concise text, edge-positioned auxiliary copy, semi-transparent overlays, and no outer white border or left/right arrow decorations. Use a provided background image when the user supplies one; otherwise use a copyright-safe bundled/default image or search for a free-to-use landscape image and cite the source in the final response.
- For `05 comparison`, use a "磨砂玻璃" style: soft pastel blurred background glows, translucent glass panels, white refraction borders, visible backdrop blur, and a colored `vs` in the title. It is best for two-option comparisons, tool tradeoffs, method selection, and pros/cons explanations.
- Keep strict fixed dimensions for cover templates: `03 xiaohongshu-nature` and `04 xiaohongshu-cover` stay `1080x1440` (strict 3:4). Template 04 must use a borderless canvas, square outer container corners, and no generated image boundary.
- For `04 xiaohongshu-cover`, first condense the user's copy into a 30-40 Chinese-character essence. Make text occupy at least 70% of the page. Use 3-4 font sizes for hierarchy; the main title should be at least 3x larger than subtitle/body copy. Extract 2-3 title keywords into `keywords` and render them with highlight color, outline, or emphasis. Use serif fonts for all Chinese title text. Emoji/avatar is allowed when it supports the style, and the avatar background should be a solid color.
- Preserve generous padding and line height for Chinese readability.
- Escape all user-provided text before injecting it into HTML.
- Prefer concise titles, numbered lists, stat blocks, and tags over dense paragraphs.
- Always render `brand` visibly when provided. Footer/signature color must have clear contrast against the background; avoid colors so close to the background that the signature appears missing.
- For `02 dark-stats`, keep the main title on one line by default. Use a single-line title treatment with sufficient font size, `white-space: nowrap`, and a size that fits the 1080px layout. If a title cannot fit cleanly, ask the user whether to shorten it rather than silently wrapping it.
- For `07 terminal-grid`, use black/green terminal UI, dense horizontal scan lines, command prompts, module panels, metrics, and status/log-like copy. It works best for technical workflows, AI agent systems, automation, monitoring, CLI tools, and developer-oriented product intros.
- For `06 linear-clean`, use a monochrome magazine layout: content-derived issue label, large serif headline, vertical oversized content keyword watermark, sparse step rows, and a bottom thesis block. Do not add extra horizontal rules beyond the necessary step/footer dividers.
- For `08 pixel-art`, use cozy farming RPG-inspired visuals: grass, soil, wood signboards, warm parchment panels, crop colors, pixel borders, quest language, and compact metric cards. Do not use copyrighted game assets; create an original pastoral pixel UI mood. It works best for gamified learning, habit systems, task quests, playful community posters, and growth maps.
- For generated business/report visuals, verify before final response that the title is not clipped, text does not overflow, and the signature is visible.
- For a new visual style, add a template under `assets/templates/` and register it in `scripts/render_html_image.py`.

## Demo Maintenance

When changing any template's appearance, regenerate that template's demo PNG under `assets/demos/`. If the template gallery is affected, rerun `scripts/build_template_gallery.py` so `assets/demos/template-gallery.png` stays current.

## Visual QA Checklist

Before returning the final PNG:

- Open or inspect the generated PNG path when the runtime allows image display.
- Confirm title behavior matches the selected template, especially whether it should be single-line or multi-line.
- Confirm signature/brand is present when provided and readable against the background.
- Confirm adaptive-height templates include comfortable bottom padding and do not look clipped or abruptly cut off.
- Confirm fixed-size templates kept their required dimensions.
- If a check fails, fix the template/data/script and regenerate before responding.

## Platform-Neutral Browser Workflow

For Hermes, OpenClaw, Codex, or other agent runtimes:

1. Write `card.html` with `--html-only`.
2. Navigate the runtime browser to the returned `file://` URL.
3. Wait until the page finishes rendering.
4. Capture the full page or visible viewport as PNG.
5. Copy or save the screenshot to the requested output path.

If the runtime cannot navigate to `file://` URLs, serve the output directory with a temporary local static server and capture the resulting `http://127.0.0.1:<port>/card.html` URL.

For platform-specific fallbacks such as OpenClaw/Lobster CDP screenshot capture, see `docs/OPENCLAW_LOBSTER.md`. Keep those details out of the conversational workflow unless the current runtime actually needs them.

Do not hard-code Codex-only browser APIs in this skill. Use whichever browser navigation and screenshot primitives the active runtime provides.
