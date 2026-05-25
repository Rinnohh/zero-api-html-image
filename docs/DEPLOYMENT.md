# zero-api-html-image Deployment

## Portable Contract

This skill does not require an image-generation API. It does require a standards-capable browser renderer somewhere in the runtime.

The portable contract is:

1. Render structured JSON into `card.html`.
2. Open the generated HTML in a browser engine.
3. Capture a PNG screenshot at the requested viewport size.
4. Verify title, signature, and bottom padding before returning the image.

The skill must not depend on a specific Codex account, a local macOS Chrome install, or a vendor-only browser API.

## Recommended Runtime Paths

Choose one screenshot path for the target environment.

### Runtime Browser Tool

Use this when the agent platform already exposes browser navigation and screenshot primitives.

```bash
python3 scripts/render_html_image.py --style warm-steps --data assets/demo-data/warm-steps.json --out-dir /tmp/zero-api-shot --html-only
```

Open the returned `browser_url`, wait for rendering, then save a screenshot.

If `file://` URLs are blocked, serve the output directory through a local static server and open the local HTTP URL.

### Python Playwright

Use this when the cloud image can install Python packages and browser binaries.

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 scripts/render_html_image.py --style warm-steps --data assets/demo-data/warm-steps.json --out-dir /tmp/zero-api-shot
```

### System Chrome Or Chromium

Use this when the container already provides a Chrome/Chromium binary. The script falls back to this path automatically if Playwright is unavailable.

The binary should be discoverable as one of:

- `chromium`
- `chromium-browser`
- `google-chrome`
- `chrome`

On macOS local development, `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` is also detected as a convenience fallback. Do not rely on that path for cloud deployment.

### External Screenshot Service

Use this when the cloud runtime cannot run a browser locally. Generate HTML with `--html-only`, host or upload the HTML and bundled assets, then call a Browserless-style screenshot service. The service must support:

- viewport width and height;
- full-page or explicit-height screenshot;
- local or uploaded assets;
- enough wait time for fonts and background images to render.

## Environment Doctor

Run:

```bash
python3 scripts/doctor.py
```

The doctor checks:

- Python version;
- required skill files;
- Pillow availability;
- Playwright Python package availability;
- Playwright browser availability when possible;
- Chrome/Chromium binary availability;
- whether demo HTML can be rendered.

The doctor is diagnostic. A cloud runtime can still be valid if local PNG capture is unavailable, as long as the platform provides a separate browser screenshot primitive.

## Minimum Files To Ship

Ship the whole skill directory, including:

- `SKILL.md`
- `scripts/`
- `assets/templates/`
- `assets/demo-data/`
- `assets/images/`
- `assets/demos/template-gallery.png`
- `docs/DEPLOYMENT.md`

Demo PNGs are useful for template selection and QA. Keep them with the skill unless the target platform has a separate gallery asset pipeline.

## Validation

Before packaging:

```bash
python3 quick_validate.py
python3 scripts/doctor.py
```

If templates changed:

```bash
python3 scripts/build_template_gallery.py
```

When a template's visual design changes, regenerate that template's demo PNG before rebuilding the gallery.
