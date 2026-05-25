---
name: zero-api-html-image
description: Generate structured Chinese visual images with HTML/CSS templates and browser screenshots instead of image-generation APIs. ⚠️ 激活条件：只有当用户明确说"用zero-api-html-image"、"用html生图"、"用html模板"或明确表示要用html模板/截图生成图片时，才使用本技能。否则使用常规的AI生图技能。

This skill is portable by design. Its stable core is HTML generation; PNG capture is a runtime capability supplied by Codex, Hermes, OpenClaw, Lobster, Playwright, Chrome/Chromium, Browserless, or an equivalent browser screenshot service. Do not assume a specific account, local Mac app, or vendor-only browser API exists.

## ⚠️ 激活条件（必读）

本技能有严格的激活门槛：

**只有以下情况才使用本技能：**
- 用户明确说"用zero-api-html-image"
- 用户明确说"用html生图"、"用html模板"、"用html做图"、"用模板生图"
- 用户明确表示要用前端模板/HTML/CSS来生成图片
- 用户主动提到要用"浏览器截图"方式生成图片

**以下情况不要使用本技能（使用默认的AI生图技能）：**
- 用户说"生成一张图""做一张海报""生成图片"
- 用户说"用生图技能""用AI生图""生成一张xx风格的图"
- 用户说"用image-gen"
- 用户只是描述了图片内容（画面描述、风格要求、文字内容）而未指定用什么方式生图
- 用户说"做成信息图""生成信息图"——如果用户只是要一张图，没有说"用html"，默认走AI生图

**一句话原则：** 用户没说"html"、"模板"、"截图"这三个关键词 → 不要用本技能。

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
6. **Send the template gallery image to the user via `message` tool (image attachment), then ask them to choose.** Offer two choices:
   - 从预设模板中选：发模板画廊图，让用户挑编号
   - **"你自由发挥"**：用户也可以不选模板，让你根据内容自行设计风格

   **MANDATORY gallery delivery steps:**
   1. Copy the gallery image from the skill to `/tmp/` (avoids permission issues): `cp /workspace/nacos-skills/zero-api-html-image/assets/demos/template-gallery.png /tmp/template-gallery.png`
   2. Use the `message` tool with `filePath="/tmp/template-gallery.png"` to send the image as an attachment to the user.
   3. **DO NOT** rely on `canvas`, `browser`, or any other display mechanism — only the `message` tool with `filePath` works reliably in chat channels.
   4. Only if `message` file-send also fails, fall back to listing the numbered options from Template Selection.
   5. Never just list text options when image delivery is possible.

   **Handling "自由发挥" (custom style):**
   - When the user opts for free-style design, analyze the content and choose a visual direction that best fits (e.g. data-heavy → data-card style, step-by-step → magazine clean style, comparison → two-column style, etc.)
   - Describe the intended style briefly to the user for confirmation before generating.
   - Then **write a custom standalone HTML file** (not via the template system) that implements the chosen style directly with inline CSS. The HTML should be self-contained (no external resources) and output-width ~1080px with appropriate fonts.
   - Save it to the output dir (e.g. `/tmp/html-shot/custom.html`) and capture via the standard screenshot workflow.

7. Create a JSON data file, render HTML, capture PNG with the available browser screenshot ability, then return the generated image.
8. If the user reports a visual defect such as missing signature, low-contrast footer, title overflow, unwanted wrapping, excessive whitespace, or poor crop, update the underlying template or script so future outputs inherit the fix; then regenerate the affected PNG and, when relevant, refresh `assets/demos/` and `template-gallery.png`.

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

### 自由发挥模式（Custom Template）

当用户选择"自由发挥"时，不走预设模板，直接手写自定义 HTML。

#### Workflow
1. 根据内容选择合适的视觉方向，简要描述给用户确认
2. 手写一个**自包含的 HTML 文件**（所有 CSS 内联在 `<style>` 中）
3. 宽度统一 1080px，根据内容自适应高度
4. 保存在输出目录（如 `/tmp/html-shot/custom.html`）
5. 通过标准截图工作流 capture 成 PNG

#### 设计原则
- **内容决定形式**：数据多的用卡片/仪表盘布局，步骤多的用时间轴/编号列表，概念介绍用大字报/杂志风
- **中文字体优先**：使用系统宋体/黑体（`"Songti SC", "PingFang SC", "Noto Sans CJK SC"`），慎用英文字体
- **字号层次清晰**：主标题 40-60px，副标题 20-28px，正文 14-18px
- **颜色不超过 3 种主色**：主色 + 强调色 + 背景色，保持干净
- **留白充足**：padding 至少 32-48px，行高 1.6-2.0
- **品牌署名可见**：如果有 brand，放在底部且有对比度
- **不要外部资源**：所有图片用 base64 或纯 CSS 实现，字体用系统字体

#### 示例结构
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080">
  <style>
    /* 全部内联，禁止外链 */
    body { width: 1080px; margin: 0; padding: 48px; font-family: "PingFang SC", "Noto Sans CJK SC", sans-serif; background: #fff; }
    .title { font-size: 48px; font-weight: 800; line-height: 1.2; margin-bottom: 16px; }
    .subtitle { font-size: 22px; color: #666; margin-bottom: 40px; }
    .section { margin-bottom: 36px; }
    .section h2 { font-size: 24px; font-weight: 700; border-left: 4px solid #f60; padding-left: 12px; margin-bottom: 16px; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
    .stat-card { background: #f5f5f5; border-radius: 12px; padding: 24px; text-align: center; }
    .stat-value { font-size: 36px; font-weight: 800; color: #f60; }
    .stat-label { font-size: 14px; color: #999; margin-top: 4px; }
    .brand { margin-top: 48px; padding-top: 16px; border-top: 1px solid #eee; text-align: center; color: #999; font-size: 12px; }
  </style>
</head>
<body>
  <!-- 手写布局，内容根据实际数据填充 -->
</body>
</html>
```

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
- **Avoid fixed `min-height` on adaptive templates** — use `min-height: 0` or omit it. A fixed `min-height` forces the screenshot to include unnecessary bottom blank.
- **CDP screenshots must override viewport width** with `Emulation.setDeviceMetricsOverride` before measuring content height, or the CSS width will differ from the target 1080px. Then use `Runtime.evaluate` with JS (e.g. `el.getBoundingClientRect().top + el.scrollHeight`) to get real content height before clipping.
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
2. Navigate the runtime browser to the rendered HTML and capture a full-page screenshot as PNG.
3. Copy or save the screenshot to the requested output path.

Do not hard-code Codex-only browser APIs in this skill. Use whichever browser navigation and screenshot primitives the active runtime provides.

### OpenClaw/Feishu 环境下的截图策略（按优先级）

#### 方案 A：Python Playwright / 本地 Chromium（推荐）
在同一容器内有 Playwright + Chromium 或本地 Chrome/Chromium 时，直接在 `render_html_image.py` 命令中省略 `--html-only` 参数即可自动截图。运行 `python3 scripts/doctor.py` 检查环境是否支持。

#### 方案 B：browser.open + screenshot（OpenClaw browser 工具）
如果 Playwright 不可用，且 OpenClaw 的 `browser` 工具可用：

1. 先生成 HTML：`python3 scripts/render_html_image.py --style <style> --data <data.json> --out-dir /tmp/html-shot --html-only`
2. 尝试用 `browser` 工具打开本地 HTML：
   - `file://` URL 通常被安全策略阻止，也不要用 `http://127.0.0.1:<port>/card.html` 绕过（同样被策略阻止）
   - 此方案在 OpenClaw 中大概率不可行，直接跳到方案 C

#### 方案 C：CDP WebSocket + data: URI + JS 精确裁剪（推荐，OpenClaw 环境首选）

当 `browser` 工具和 Playwright 都不可用，但 Chrome/Chromium 已在容器的 CDP 端口（9222）上运行时。相比旧方案，本方案通过 **浏览器级 WS + Target.createTarget** 创建新标签页（避免 405），并通过 **Emulation.setDeviceMetricsOverride + Runtime.evaluate JS 测量**实现精确裁剪，消除右侧和底部空白。

Skill 内置了 `scripts/cdp_capture.py` 可直接调用：

```bash
python3 scripts/render_html_image.py --style terminal-grid --data data.json --out-dir /tmp/html-shot --html-only
python3 scripts/cdp_capture.py --html /tmp/html-shot/card.html --output /tmp/html-shot/output.png --width 1080 --padding 40
```

**手动实现步骤**：

1. **绕过 HTTP 代理**：容器可能配置了 HTTP_PROXY，访问 127.0.0.1:9222 时必须绕开。
   - curl 加 `--noproxy '*'`，Python 设置 `os.environ["no_proxy"] = "127.0.0.1,localhost"`

2. **获取浏览器级 WebSocket URL**（通过 `/json/version`，不是 `/json`）：
   ```python
   import urllib.request, json, os
   os.environ["no_proxy"] = "127.0.0.1,localhost"
   req = urllib.request.Request("http://127.0.0.1:9222/json/version")
   browser_ws_url = json.loads(urllib.request.urlopen(req).read())["webSocketDebuggerUrl"]
   ```

3. **创建新标签页并导航到 data: URI**（用 `Target.createTarget` 而非 `/json/new`，后者返回 405）：
   ```python
   from websocket import create_connection
   ws = create_connection(browser_ws_url, timeout=30)
   
   html_content = open("/tmp/html-shot/card.html").read()
   data_uri = "data:text/html;base64," + base64.b64encode(html_content.encode()).decode()
   
   ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": data_uri}}))
   target_id = json.loads(ws.recv())["result"]["targetId"]
   time.sleep(4)  # 等待页面加载
   ```

4. **Attach 到目标并设置精确视口宽度**（**关键**——不做则 CSS 宽度跟随浏览器已有视口，通常 1265px 而非 1080px）：
   ```python
   ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget",
                       "params": {"targetId": target_id, "flatten": True}}))
   session_id = json.loads(ws.recv())["result"]["sessionId"]
   
   ws.send(json.dumps({"id": 3, "method": "Emulation.setDeviceMetricsOverride", "params": {
       "width": 1080, "height": 2000, "deviceScaleFactor": 1, "mobile": False
   }, "sessionId": session_id}))
   time.sleep(2)
   ```

5. **用 JS 测量真实内容高度**（比 `Page.getLayoutMetrics` 更准确，避免视口撑高导致的虚报）：
   ```python
   ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {
       "expression": """(function(){
         var el = document.querySelector('main') || document.querySelector('.screen');
         if(!el) return document.body.scrollHeight;
         return el.getBoundingClientRect().top + el.scrollHeight;
       })()""",
       "returnByValue": True
   }, "sessionId": session_id}))
   content_h = int(json.loads(ws.recv())["result"]["result"]["value"])
   ```

6. **测量 brand 底部**，取较大值 + 40px padding 作为裁剪高度：
   ```python
   ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {
       "expression": "(function(){ var b=document.querySelector('.brand'); return b?b.getBoundingClientRect().bottom:-1; })()",
       "returnByValue": True
   }, "sessionId": session_id}))
   brand_bottom = int(json.loads(ws.recv())["result"]["result"]["value"])
   
   clip_h = max(content_h, brand_bottom + 40) if brand_bottom > 0 else content_h + 40
   clip_h = min(clip_h, 3000)
   
   ws.send(json.dumps({"id": 6, "method": "Emulation.setDeviceMetricsOverride", "params": {
       "width": 1080, "height": clip_h, "deviceScaleFactor": 1, "mobile": False
   }, "sessionId": session_id}))
   time.sleep(0.5)
   ```

7. **截图输出**：
   ```python
   ws.send(json.dumps({"id": 7, "method": "Page.captureScreenshot", "params": {
       "format": "png",
       "captureBeyondViewport": True,
       "clip": {"x": 0, "y": 0, "width": 1080, "height": clip_h, "scale": 1}
   }, "sessionId": session_id}))
   
   captured = None
   deadline = time.time() + 15
   while time.time() < deadline and captured is None:
       msg = json.loads(ws.recv())
       if msg.get("id") == 7:
           captured = msg
   
   img_data = base64.b64decode(captured["result"]["data"])
   open(output_path, "wb").write(img_data)
   ws.close()
   ```

> **关键改进总结**：
> - 用 `Target.createTarget`（浏览器级 WS）替代 `/json/new`（后者返回 405）
> - 用 `Emulation.setDeviceMetricsOverride` 确保精准 1080px 视口
> - 用 `Runtime.evaluate + JS getBoundingClientRect` 替代 `Page.getLayoutMetrics`，避免视口高度撑高测量值
> - 内置脚本 `scripts/cdp_capture.py` 封装全部流程，一行命令即完成裁剪截图

#### 方案 D：本地 HTTP 服务器（备用）
如果 CDP data: URI 方案也不可用，启动临时 HTTP 服务器并用外部工具截图。注意此方案在 OpenClaw 环境中通常也会被浏览器策略阻止。

## Troubleshooting（常见问题排查）

### CDP 端口访问被代理拦截
- **症状**：`curl http://127.0.0.1:9222/json` 返回 503 Service Unavailable
- **原因**：容器的 HTTP_PROXY/HTTPS_PROXY 环境变量导致 localhost 请求被代理拦截
- **解决**：始终使用 `--noproxy '*'` 或设置 `no_proxy=127.0.0.1,localhost`

### file:// URL 被浏览器阻止
- **症状**：`browser.open` 返回 "Navigation blocked: unsupported protocol 'file:'"
- **原因**：OpenClaw 浏览器策略禁止 file:// 协议
- **解决**：切换到方案 C（CDP data: URI）

### HTTP 服务器 URL 被浏览器策略阻止
- **症状**：`browser.open(127.0.0.1:端口/card.html)` 返回 "browser navigation blocked by policy"
- **原因**：OpenClaw 的安全策略阻止了本地 HTTP 地址的导航
- **解决**：切换到方案 C（CDP data: URI）

### message 工具发送图片失败（EACCES）
- **症状**：`message` 工具返回 "Media upload failed (EACCES: permission denied)"
- **原因**：源文件路径权限不足，通常是因为 skill 目录位于受限制的路径下
- **解决**：先将文件复制到 `/tmp/` 目录再发送

### `/json/new` 返回 405（Method Not Allowed）
- **症状**：`curl --noproxy '*' http://127.0.0.1:9222/json/new` 返回 405
- **原因**：部分 Chrome/Chromium 版本禁用了通过 HTTP 创建新标签页的接口
- **解决**：用浏览器级 WebSocket 的 `Target.createTarget` 方法替代，先连接 `/json/version` 获取 `webSocketDebuggerUrl`，再通过 CDP 命令创建标签页

### `Page.getLayoutMetrics` 返回的高度不准确（底部空白多）
- **症状**：截图后底部大量空白，`contentSize.height` 远大于实际内容
- **原因**：设置了 `Emulation.setDeviceMetricsOverride` 的 height=2000 后，CSS content size 被撑到了 2000px
- **解决**：用 `Runtime.evaluate` + JavaScript `getBoundingClientRect()` 测量真实内容底部，不要依赖 `Page.getLayoutMetrics` 的 contentSize

### `captureScreenshot` 返回 event 而非 id-matched 结果
- **症状**：等待 `id==4` 的响应超时，收到的却是 `{"method": "Page.captureScreenshot", "params": {...}}` 格式的消息
- **原因**：flattened session 模式下，部分 CDP 实现将截图结果以 event 形式推回，而非标准 request-response
- **解决**：增加一个 fallback 分支，同时检查 `msg.get("id") == x` 和 `msg.get("method") == "Page.captureScreenshot"`

### websocket-client 未安装
- **症状**：Python 报 ModuleNotFoundError: No module named 'websocket'
- **解决**：`pip3 install websocket-client --break-system-packages`

### Chrome/Chromium 未安装
- **症状**：`render_html_image.py` 截图失败，doctor 脚本报告缺少浏览器
- **解决**：使用方案 C（CDP data: URI）或安装 Playwright（`playwright install chromium`）
