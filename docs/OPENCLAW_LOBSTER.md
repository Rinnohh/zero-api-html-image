# OpenClaw/Lobster Screenshot Fallbacks

These notes are for OpenClaw/Lobster-style hosted runtimes where the normal browser paths may be restricted. Keep `SKILL.md` platform-neutral; use this document only when the current runtime needs these workarounds.

## Recommended Order

1. Try direct capture first:

   ```bash
   python3 scripts/doctor.py
   python3 scripts/render_html_image.py --style warm-steps --data assets/demo-data/warm-steps.json --out-dir /tmp/zero-api-shot
   ```

2. If direct capture fails, generate HTML only:

   ```bash
   python3 scripts/render_html_image.py --style warm-steps --data assets/demo-data/warm-steps.json --out-dir /tmp/zero-api-shot --html-only
   ```

3. Try the runtime's normal browser screenshot primitive.

4. If `file://` or local HTTP navigation is blocked, use the CDP data URI fallback below.

## Gallery Delivery

When asking the user to choose a template, send only:

- `assets/demos/template-gallery.png`

Use the current runtime's supported file/image attachment mechanism. If that mechanism cannot read from the skill install directory, copy the gallery to a temporary readable path such as `/tmp/template-gallery.png`, then attach that copy. Do not hard-code one install path such as `/workspace/nacos-skills/...`.

## CDP Data URI Fallback

Use this only when all of these are true:

- Playwright or direct Chrome/Chromium screenshot is unavailable.
- The normal browser tool blocks `file://` and local HTTP URLs.
- Chrome/Chromium is already running with a DevTools endpoint, commonly `127.0.0.1:9222`.
- The HTML is self-contained enough for a `data:` URI, or you have converted local assets into data URLs.

Important limitation: `data:` navigation may not load relative local assets such as background images or local fonts. Templates with bundled images, especially `xiaohongshu-nature`, must be visually checked after capture. If assets do not render, use Playwright/Chromium direct capture or serve/upload assets through a permitted URL.

### Avoid Proxy Interception

Some containers set `HTTP_PROXY` or `HTTPS_PROXY`, which can intercept requests to `127.0.0.1:9222` and return `503 Service Unavailable`.

Use one of these approaches:

```bash
curl --noproxy '*' http://127.0.0.1:9222/json
```

```python
import os
os.environ["no_proxy"] = "127.0.0.1,localhost"
```

### Capture Through CDP

This example assumes `websocket-client` is installed. Install dependencies through the runtime's normal dependency setup, preferably:

```bash
python3 -m pip install -r requirements.txt
```

Then capture:

```python
import base64
import json
import os
import time
import urllib.request
from pathlib import Path

from websocket import create_connection


os.environ["no_proxy"] = "127.0.0.1,localhost"

html_path = Path("/tmp/zero-api-shot/card.html")
output_path = Path("/tmp/zero-api-shot/output.png")

targets = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=10).read())
pages = [target for target in targets if target.get("type") == "page" and target.get("webSocketDebuggerUrl")]
if not pages:
    raise RuntimeError("No CDP page target found.")

ws = create_connection(pages[0]["webSocketDebuggerUrl"], timeout=30)

try:
    html = html_path.read_text(encoding="utf-8")
    data_uri = "data:text/html;base64," + base64.b64encode(html.encode("utf-8")).decode("ascii")

    ws.send(json.dumps({"id": 1, "method": "Page.enable", "params": {}}))
    ws.recv()

    ws.send(json.dumps({"id": 2, "method": "Page.navigate", "params": {"url": data_uri}}))

    deadline = time.time() + 15
    while time.time() < deadline:
        message = json.loads(ws.recv())
        if message.get("method") == "Page.loadEventFired":
            break

    time.sleep(1)

    ws.send(json.dumps({"id": 3, "method": "Page.getLayoutMetrics", "params": {}}))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == 3:
            content = message["result"]["contentSize"]
            break

    width = int(content["width"])
    height = int(content["height"])

    ws.send(json.dumps({
        "id": 4,
        "method": "Page.captureScreenshot",
        "params": {
            "format": "png",
            "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1},
        },
    }))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == 4:
            output_path.write_bytes(base64.b64decode(message["result"]["data"]))
            break
finally:
    ws.close()
```

## Troubleshooting

### `file://` URL Is Blocked

Symptom: the browser tool reports unsupported or blocked `file:` navigation.

Use direct Playwright/Chromium capture if available. If not, try local HTTP. If local HTTP is also blocked in this runtime, use CDP data URI capture.

### Local HTTP URL Is Blocked

Symptom: `http://127.0.0.1:<port>/card.html` is blocked by browser navigation policy.

Use CDP data URI capture, or use an external screenshot service that can access the rendered HTML and bundled assets.

### CDP Port Returns 503

Symptom: `curl http://127.0.0.1:9222/json` returns `503 Service Unavailable`.

Bypass the proxy for localhost using `--noproxy '*'` or `no_proxy=127.0.0.1,localhost`.

### Image Attachment Fails With Permission Errors

If the runtime cannot attach images from the skill directory, copy the file to a temporary readable path first:

```bash
cp assets/demos/template-gallery.png /tmp/template-gallery.png
```

Then send `/tmp/template-gallery.png` with the runtime's supported attachment mechanism.

### `websocket` Module Is Missing

Install dependencies through the runtime's dependency setup:

```bash
python3 -m pip install -r requirements.txt
```

Avoid documenting `--break-system-packages` as the default path. Use it only as a runtime-specific emergency workaround when the environment owner explicitly allows it.
