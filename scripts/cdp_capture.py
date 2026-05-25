#!/usr/bin/env python3
"""
CDP（Chrome DevTools Protocol）截图工具
用于 render_html_image.py --html-only 模式之后的截图步骤。
基于浏览器级别的 WebSocket 连接，支持：
- 视口尺寸覆盖（确保 1080px 精确宽度）
- JS 测量实际内容高度（避免底部空白）
- 精准裁剪，仅加 40px 底部留白

用法：
  python3 scripts/render_html_image.py --style terminal-grid --data data.json --out-dir /tmp/html-shot --html-only
  python3 scripts/cdp_capture.py --html /tmp/html-shot/card.html --output /tmp/html-shot/output.png
"""
import base64, json, os, sys, time, argparse
from pathlib import Path
import urllib.request

os.environ["no_proxy"] = "127.0.0.1,localhost"

def capture(html_path: Path, output_path: Path, width: int = 1080, bottom_padding: int = 40):
    # Get browser WS URL
    req = urllib.request.Request("http://127.0.0.1:9222/json/version")
    resp = urllib.request.urlopen(req)
    browser_ws_url = json.loads(resp.read())["webSocketDebuggerUrl"]

    from websocket import create_connection
    ws = create_connection(browser_ws_url, timeout=30)
    time.sleep(0.2)

    html = html_path.read_text(encoding="utf-8")
    data_uri = "data:text/html;base64," + base64.b64encode(html.encode()).decode()

    # Create new page target
    ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": data_uri}}))
    deadline = time.time() + 10
    target_id = None
    while time.time() < deadline:
        msg = json.loads(ws.recv())
        if msg.get("id") == 1:
            target_id = msg["result"]["targetId"]
            break

    if not target_id:
        ws.close()
        raise RuntimeError("Failed to create CDP target")

    time.sleep(4)  # Wait for initial page load

    # Attach to target with flattened session
    ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget",
                        "params": {"targetId": target_id, "flatten": True}}))
    deadline = time.time() + 10
    session_id = None
    while time.time() < deadline:
        msg = json.loads(ws.recv())
        if msg.get("id") == 2:
            session_id = msg["result"]["sessionId"]
            break

    if not session_id:
        ws.close()
        raise RuntimeError("Failed to attach to CDP target")

    # Override viewport to exact width
    ws.send(json.dumps({"id": 3, "method": "Emulation.setDeviceMetricsOverride", "params": {
        "width": width, "height": 2000, "deviceScaleFactor": 1, "mobile": False
    }, "sessionId": session_id}))
    time.sleep(2)

    # Drain events
    ws.settimeout(0.3)
    try:
        while True: ws.recv()
    except: pass

    # JS: measure real content bottom
    ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {
        "expression": """
(function(){
  var el = document.querySelector('main') || document.querySelector('.screen');
  if(!el) return document.body.scrollHeight;
  return el.getBoundingClientRect().top + el.scrollHeight;
})()
""",
        "returnByValue": True
    }, "sessionId": session_id}))

    deadline = time.time() + 10
    content_h = 1000
    while time.time() < deadline:
        try:
            ws.settimeout(3)
            msg = json.loads(ws.recv())
            if msg.get("id") == 4:
                content_h = int(msg["result"]["result"]["value"])
                break
        except: pass

    # Also check brand bottom
    ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {
        "expression": "(function(){ var b=document.querySelector('.brand'); return b?b.getBoundingClientRect().bottom:-1; })()",
        "returnByValue": True
    }, "sessionId": session_id}))

    deadline = time.time() + 5
    brand_bottom = -1
    while time.time() < deadline:
        try:
            ws.settimeout(2)
            msg = json.loads(ws.recv())
            if msg.get("id") == 5:
                brand_bottom = int(msg["result"]["result"]["value"])
                break
        except: pass

    if brand_bottom > 0:
        clip_h = max(content_h, brand_bottom + bottom_padding)
    else:
        clip_h = content_h + bottom_padding

    clip_h = min(clip_h, 3000)

    # Reset viewport to match clip height for proper rendering
    ws.send(json.dumps({"id": 6, "method": "Emulation.setDeviceMetricsOverride", "params": {
        "width": width, "height": clip_h, "deviceScaleFactor": 1, "mobile": False
    }, "sessionId": session_id}))
    time.sleep(0.5)

    # Drain
    try:
        while True: ws.recv()
    except: pass

    # Capture screenshot
    ws.send(json.dumps({"id": 7, "method": "Page.captureScreenshot", "params": {
        "format": "png",
        "captureBeyondViewport": True,
        "clip": {"x": 0, "y": 0, "width": width, "height": clip_h, "scale": 1}
    }, "sessionId": session_id}))

    captured = None
    deadline = time.time() + 15
    while time.time() < deadline and captured is None:
        try:
            ws.settimeout(5)
            msg = json.loads(ws.recv())
            if msg.get("id") == 7:
                captured = msg
        except: break

    ws.close()

    if captured and "result" in captured:
        img_data = base64.b64decode(captured["result"]["data"])
        output_path.write_bytes(img_data)
        print(f"SAVED: {output_path} ({len(img_data)} bytes, {width}x{clip_h})")
    else:
        raise RuntimeError(f"Screenshot capture failed: {captured}")

def main():
    parser = argparse.ArgumentParser(description="CDP-based HTML screenshot capture")
    parser.add_argument("--html", required=True, help="Path to HTML file")
    parser.add_argument("--output", default="/tmp/html-shot/output.png", help="Output PNG path")
    parser.add_argument("--width", type=int, default=1080, help="Output width in pixels")
    parser.add_argument("--padding", type=int, default=40, help="Bottom padding in pixels")
    args = parser.parse_args()

    html_path = Path(args.html).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        capture(html_path, output_path, args.width, args.padding)
        print(json.dumps({"output": str(output_path), "width": args.width}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
