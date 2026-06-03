#!/usr/bin/env python3
"""
gpt-image-2 image generator / editor.

A single-file CLI that calls OpenAI's Image API (model: gpt-image-2) to
generate images from a text prompt, or edit / compose from reference images.

It is designed to be called by an AI agent: it prints a single JSON object
to stdout on success (with saved file paths), and a JSON error to stderr on
failure, so the calling model can parse the result reliably.

Auth & config via environment variables:
  OPENAI_API_KEY   (required) API key with image scope.
  OPENAI_BASE_URL  (optional) Override base URL. Default: https://api.openai.com/v1
                              Useful for proxies / OpenAI-compatible gateways.
  GPT_IMAGE_MODEL  (optional) Override model name. Default: gpt-image-2

No third-party dependencies required (uses urllib from the stdlib).
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import uuid
import urllib.request
import urllib.error

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-image-2"

# Config file is searched in this order. First found wins.
# JSON shape: {"api_key": "...", "base_url": "...", "model": "..."}
CONFIG_PATHS = [
    os.environ.get("GPT_IMAGE_CONFIG", ""),                      # explicit override
    os.path.join(os.path.dirname(os.path.abspath(__file__)),     # next to the skill
                 "..", "config.json"),
    os.path.expanduser("~/.config/gpt-image-2/config.json"),     # user-global
]


def load_config():
    """Load config.json from the first existing path. Returns a dict (maybe empty)."""
    for path in CONFIG_PATHS:
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                if isinstance(cfg, dict):
                    cfg["_source"] = os.path.abspath(path)
                    return cfg
            except Exception:
                # Ignore malformed config; fall through to env/defaults.
                pass
    return {}


def resolve_setting(cli_value, env_name, config, config_key, default):
    """Precedence: CLI arg > env var > config file > built-in default."""
    if cli_value:
        return cli_value
    env_val = os.environ.get(env_name)
    if env_val:
        return env_val
    cfg_val = config.get(config_key)
    if cfg_val:
        return cfg_val
    return default

POPULAR_SIZES = [
    "auto", "1024x1024", "1536x1024", "1024x1536",
    "2048x2048", "2048x1152", "3840x2160", "2160x3840",
]
QUALITIES = ["auto", "low", "medium", "high"]
FORMATS = ["png", "jpeg", "webp"]


def eprint_json(obj):
    sys.stderr.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stderr.flush()


def fail(message, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    eprint_json(payload)
    sys.exit(1)


def build_multipart(fields, files):
    """Build a multipart/form-data body. files: list of (field, path)."""
    boundary = "----gptimage2-" + uuid.uuid4().hex
    crlf = b"\r\n"
    body = []
    for name, value in fields.items():
        if value is None:
            continue
        body.append(b"--" + boundary.encode())
        body.append(('Content-Disposition: form-data; name="%s"' % name).encode())
        body.append(b"")
        body.append(str(value).encode("utf-8"))
    for name, path in files:
        filename = os.path.basename(path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            data = f.read()
        body.append(b"--" + boundary.encode())
        body.append((
            'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename)
        ).encode())
        body.append(("Content-Type: %s" % ctype).encode())
        body.append(b"")
        body.append(data)
    body.append(b"--" + boundary.encode() + b"--")
    body.append(b"")
    return crlf.join(body), boundary


def http_post(url, headers, data, timeout):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = {"raw": "<unparseable error body>"}
        fail("HTTP %s from image API" % e.code, status=e.code, detail=detail)
    except urllib.error.URLError as e:
        fail("Network error: %s" % str(e.reason))
    except Exception as e:  # noqa
        fail("Unexpected error: %s" % str(e))


def save_images(api_json, out_dir, ext):
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    data = api_json.get("data") or []
    if not data:
        fail("API returned no image data", detail=api_json)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for i, item in enumerate(data):
        b64 = item.get("b64_json")
        if not b64:
            # Some gateways return a URL instead of base64.
            url = item.get("url")
            if url:
                saved.append({"index": i, "url": url})
                continue
            fail("Image item missing b64_json/url", detail=item)
        raw = base64.b64decode(b64)
        fname = "gptimg2-%s-%d.%s" % (stamp, i, ext)
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "wb") as f:
            f.write(raw)
        saved.append({"index": i, "path": os.path.abspath(fpath)})
    return saved


def main():
    p = argparse.ArgumentParser(
        description="Generate or edit images with gpt-image-2."
    )
    p.add_argument("prompt", help="Text prompt describing the image.")
    p.add_argument("-o", "--out-dir", default="./generated-images",
                   help="Output directory (default: ./generated-images)")
    p.add_argument("-n", "--count", type=int, default=1,
                   help="Number of images to generate (default: 1)")
    p.add_argument("-s", "--size", default="auto",
                   help="Image size, e.g. 1024x1024 or 'auto' (default: auto). "
                        "Popular: " + ", ".join(POPULAR_SIZES))
    p.add_argument("-q", "--quality", default="auto", choices=QUALITIES,
                   help="Rendering quality (default: auto)")
    p.add_argument("-f", "--format", default="png", choices=FORMATS,
                   dest="img_format", help="Output format (default: png)")
    p.add_argument("--compression", type=int, default=None,
                   help="Compression 0-100 for jpeg/webp.")
    p.add_argument("--moderation", default=None, choices=["auto", "low"],
                   help="Moderation strictness.")
    p.add_argument("--ref", action="append", default=[],
                   help="Reference/input image path for editing. Repeatable. "
                        "When provided, uses the /images/edits endpoint.")
    p.add_argument("--mask", default=None,
                   help="Mask image path (PNG w/ alpha) for inpainting edits.")
    p.add_argument("--timeout", type=int, default=180,
                   help="Request timeout in seconds (default: 180).")
    p.add_argument("--api-key", default=None,
                   help="API key. Overrides OPENAI_API_KEY env and config file.")
    p.add_argument("--base-url", default=None,
                   help="API base URL. Overrides OPENAI_BASE_URL env and config file. "
                        "Default: " + DEFAULT_BASE_URL)
    p.add_argument("--model", default=None,
                   help="Model name. Overrides GPT_IMAGE_MODEL env and config file. "
                        "Default: " + DEFAULT_MODEL)
    args = p.parse_args()

    # Resolve credentials/config with precedence: CLI > env > config.json > default.
    config = load_config()
    api_key = resolve_setting(args.api_key, "OPENAI_API_KEY", config, "api_key", None)
    base_url = resolve_setting(
        args.base_url, "OPENAI_BASE_URL", config, "base_url", DEFAULT_BASE_URL
    ).rstrip("/")
    model = resolve_setting(args.model, "GPT_IMAGE_MODEL", config, "model", DEFAULT_MODEL)

    if not api_key:
        fail(
            "No API key found. Configure image-generation credentials before running.",
            error_code="missing_api_key",
            credential_sources={
                "cli_flag": "--api-key",
                "environment": "OPENAI_API_KEY",
                "config_file_keys": ["api_key", "base_url", "model"],
            },
            config_searched=[p for p in CONFIG_PATHS if p],
            setup_hint=(
                "Set OPENAI_API_KEY in the runtime environment, or create config.json "
                "from config.example.json. In LobeHub Cloud Sandbox, inject the saved "
                "LOBEHUB_SKILLS_CONFIG credential and run with: "
                "bash -c 'source ~/.creds/env && python3 scripts/generate.py ...'."
            ),
        )

    # gpt-image-2 returns base64 by default; we want b64 to save locally.
    common = {
        "model": model,
        "prompt": args.prompt,
        "n": args.count,
        "size": args.size,
        "quality": args.quality,
    }
    if args.moderation:
        common["moderation"] = args.moderation

    if args.ref:
        # --- Edits endpoint (multipart) ---
        url = base_url + "/images/edits"
        for path in args.ref:
            if not os.path.isfile(path):
                fail("Reference image not found: %s" % path)
        files = [("image[]", path) for path in args.ref]
        if args.mask:
            if not os.path.isfile(args.mask):
                fail("Mask image not found: %s" % args.mask)
            files.append(("mask", args.mask))
        # Edits endpoint takes output_format/output_compression as form fields.
        fields = dict(common)
        fields["output_format"] = args.img_format
        if args.compression is not None:
            fields["output_compression"] = args.compression
        body, boundary = build_multipart(fields, files)
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        }
        api_json = http_post(url, headers, body, args.timeout)
        mode = "edit"
    else:
        # --- Generations endpoint (JSON) ---
        url = base_url + "/images/generations"
        payload = dict(common)
        payload["output_format"] = args.img_format
        if args.compression is not None:
            payload["output_compression"] = args.compression
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        }
        api_json = http_post(url, headers, body, args.timeout)
        mode = "generate"

    ext = "jpg" if args.img_format == "jpeg" else args.img_format
    saved = save_images(api_json, args.out_dir, ext)

    result = {
        "ok": True,
        "mode": mode,
        "model": model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "format": args.img_format,
        "images": saved,
        "usage": api_json.get("usage"),
        "config_source": config.get("_source") if config else None,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
