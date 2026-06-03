---
name: gpt-image-2-agent
identifier: ChenYCL/gpt-image-2-agent
description: >-
  Generate or edit images with OpenAI's gpt-image-2 model. Use this skill
  whenever the user asks to create, draw, design, render, illustrate, or edit
  an image, picture, photo, illustration, icon, logo, poster, banner, mockup,
  or any visual asset from a text prompt — or to modify/compose from reference
  images. Supports text-to-image, image-to-image editing, reference composition,
  and mask-based inpainting. Saves images locally and returns their file paths
  so other agents/tools can use the results.
license: MIT
---

# gpt-image-2-agent Image Generation

Generate and edit images using OpenAI's `gpt-image-2` model via the Image API.
Results are saved as local files and reported back as JSON (with absolute
paths), making the output easy to hand off to other agents or tools.

## When to use this skill

Activate when the user wants to:

- **Create an image from text** ("draw a…", "generate an image of…", "make a poster…").
- **Edit / transform an existing image** (provide one or more reference images).
- **Compose a new image from multiple references** (e.g. product + background).
- **Inpaint a region** of an image using a mask.

## Prerequisites (one-time setup)

The script needs an **API key** and (optionally) a **base URL** / model. These can
be supplied three ways, resolved in this **precedence order**:

> **CLI flag → environment variable → `config.json` → built-in default**

### Option A — config file (recommended for agents)

Copy `config.example.json` to `config.json` (next to `SKILL.md`) and fill it in:

```json
{
  "api_key": "sk-REPLACE_WITH_YOUR_KEY",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-image-2"
}
```

The script auto-discovers the config from the first path that exists:
1. `$GPT_IMAGE_CONFIG` (explicit path override)
2. `config.json` next to the skill
3. `~/.config/gpt-image-2/config.json` (user-global)

> `config.json` holds a secret — keep it out of version control (already gitignored).

### Option B — environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | API key with image generation scope |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Proxy / OpenAI-compatible gateway |
| `GPT_IMAGE_MODEL` | `gpt-image-2` | Override the model name |

### Option C — inline CLI flags

```bash
python3 scripts/generate.py "a red fox" \
  --api-key "sk-..." \
  --base-url "https://your-gateway/v1" \
  --model gpt-image-2
```

> If no API key is found anywhere, the script exits with a clear JSON error that
> also lists the config paths it searched. Never hard-code keys into the prompt.


## Agent execution workflow

When this skill is activated in an agent/chat session, follow this workflow exactly:

1. **Resolve credentials first**
   - Prefer saved LobeHub credentials over asking the user for secrets.
   - In Cloud Sandbox, inject the saved `LOBEHUB_SKILLS_CONFIG` credential when available, then run commands through:
     `bash -c "source ~/.creds/env && python3 scripts/generate.py ..."`
   - The injected environment should provide `OPENAI_API_KEY` and optionally `OPENAI_BASE_URL`.
   - Never ask the user to paste API keys into chat. If credentials are missing, tell the user to save/configure them securely.

2. **Run the generator**
   - Use `scripts/generate.py` as the only entry point.
   - For ordinary chat image generation, use `--quality low` for quick drafts unless the user asks for final/high quality.
   - Always choose an explicit `--out-dir` that the agent can access, such as `/tmp/gpt-image-2-output` in sandbox or `./generated-images` in a local workspace.

3. **Parse the JSON result**
   - On success, parse stdout as JSON and read `images[].path` or `images[].url`.
   - On failure, parse stderr as JSON. If `error_code` is `missing_api_key`, respond with a clear credential setup message and do not retry blindly.

4. **Display and download the image**
   - In Cloud Sandbox, call the sandbox `exportFile` tool for every generated local image path, then show the download URL to the user.
   - If the chat supports image/file previews, include the generated image as a preview in the final answer. Prefer Markdown image syntax for exported URLs: `![preview](DOWNLOAD_URL)`.
   - In local-desktop mode, return the image using the local file tag/path format required by the host environment so the user can open/download it.
   - Always include: prompt summary, model, size, quality, file format, and path/download link.

Recommended final response shape after successful generation:

```markdown
✅ 图片已生成

![预览](DOWNLOAD_URL)

📥 下载：DOWNLOAD_URL
📄 参数：gpt-image-2 · 1024x1024 · low · png
```

### Missing credentials behavior

If credentials are not configured, the script returns a structured JSON error similar to:

```json
{
  "ok": false,
  "error_code": "missing_api_key",
  "error": "No API key found. Configure image-generation credentials before running.",
  "credential_sources": {
    "cli_flag": "--api-key",
    "environment": "OPENAI_API_KEY",
    "config_file_keys": ["api_key", "base_url", "model"]
  }
}
```

When this happens, tell the user:

> Image generation credentials are not configured. Please save/configure an OpenAI-compatible image API key in LobeHub credentials, or create a local `config.json` from `config.example.json`. I will not ask you to paste the key into chat.

## How to run

The entry point is `scripts/generate.py` (pure Python stdlib, no pip install needed).

### 1. Text-to-image (basic)

```bash
python3 scripts/generate.py "a cozy reading nook by a rainy window, warm light" \
  --out-dir ./generated-images
```

### 2. Control size / quality / format

```bash
python3 scripts/generate.py "minimalist mountain logo, flat vector" \
  --size 1024x1024 --quality high --format png
```

- `--size`: `auto` (default), `1024x1024`, `1536x1024` (landscape),
  `1024x1536` (portrait), `2048x2048` (2K), `3840x2160` (4K), etc.
  Constraints: each edge a multiple of 16px, max edge ≤ 3840px, ratio ≤ 3:1.
- `--quality`: `auto` (default), `low`, `medium`, `high`.
  Use `low` for fast drafts, `high` for final assets.
- `--format`: `png` (default), `jpeg`, `webp`. Add `--compression 0-100` for jpeg/webp.
- `-n / --count`: number of images (default 1).
- `--moderation`: `auto` (default) or `low`.

### 3. Edit / image-to-image (reference images)

Pass one or more `--ref` flags. This switches to the edits endpoint:

```bash
python3 scripts/generate.py "place this product on a marble kitchen counter" \
  --ref ./product.png --quality high
```

Compose from multiple references:

```bash
python3 scripts/generate.py "a gift basket containing all these items, studio lighting" \
  --ref ./lotion.png --ref ./soap.png --ref ./candle.png
```

### 4. Inpainting with a mask

The mask must be a PNG with an alpha channel; transparent areas get repainted:

```bash
python3 scripts/generate.py "replace the sky with a dramatic sunset" \
  --ref ./photo.png --mask ./sky-mask.png
```


## Natural-language parameter mapping

The user may describe generation/editing requirements in ordinary language. Convert those requirements into script flags before running `scripts/generate.py`.

### Output format

Map user requests to `--format`:

| User says | Flag | Notes |
| --- | --- | --- |
| PNG / default / high compatibility | `--format png` | Default and recommended |
| JPG / JPEG / smaller photo file | `--format jpeg` | Use `--compression` when user asks for smaller/lower file size |
| WebP / web optimized | `--format webp` | Use `--compression` if requested |

Supported formats: `png`, `jpeg`, `webp`.

### Size and aspect ratio

Map user requests to `--size`:

| User says | Suggested flag |
| --- | --- |
| square / avatar / icon | `--size 1024x1024` |
| landscape / banner / wide / 16:9 | `--size 1536x1024` or `--size 2048x1152` |
| portrait / poster / phone wallpaper / vertical | `--size 1024x1536` |
| 2K square | `--size 2048x2048` |
| 4K landscape | `--size 3840x2160` |
| 4K portrait | `--size 2160x3840` |

If the user gives an exact valid size, pass it directly. Constraints: each edge should be a multiple of 16, max edge ≤ 3840, aspect ratio ≤ 3:1. If the user gives an invalid size, choose the closest valid size and mention the adjustment.

### Quality

Map user requests to `--quality`:

| User says | Flag |
| --- | --- |
| draft / quick / low cost / fast | `--quality low` |
| normal / balanced | `--quality medium` |
| final / high detail / best quality | `--quality high` |
| unspecified | `--quality low` for chat drafts, unless the user asks for final output |

### Reference image editing

If the user provides one or more image paths/files/attachments and asks to modify, restyle, replace, combine, preserve, or use them as reference, use `--ref` for each reference image. This switches the script to image edit mode.

Examples:

```bash
python3 scripts/generate.py "make this product photo look premium on a marble counter" --ref ./product.png --quality high
python3 scripts/generate.py "combine these products into one gift basket, studio lighting" --ref ./a.png --ref ./b.png --ref ./c.png
```

### Mask / inpainting

If the user provides a mask and asks to repaint only a region, pass the original/reference image with `--ref` and the mask with `--mask`. The mask must be a PNG with alpha; transparent areas are edited.

```bash
python3 scripts/generate.py "replace the sky with a dramatic sunset" --ref ./photo.png --mask ./sky-mask.png
```

### Clarification policy

Do not ask unnecessary clarification questions. Infer sensible defaults from the user's natural language. Ask one concise clarification only when a required reference image/mask is missing or when the user's request is ambiguous in a way that changes the output materially.

## Output format

On **success**, the script prints a JSON object to **stdout**:

```json
{
  "ok": true,
  "mode": "generate",
  "model": "gpt-image-2",
  "prompt": "...",
  "size": "1024x1024",
  "quality": "high",
  "format": "png",
  "images": [
    { "index": 0, "path": "/abs/path/generated-images/gptimg2-20260603-101500-0.png" }
  ],
  "usage": { "...": "token usage if provided" }
}
```

On **failure**, a JSON error goes to **stderr** with `"ok": false`, an `error`
message, and (for HTTP errors) a `status` code and `detail` object.

## Agent collaboration tips

- **Parse the JSON** from stdout and read `images[].path` to reference or
  display the generated files, or to pass them to a downstream agent/tool.
- For **iterative refinement**, feed a previously generated file back in via
  `--ref` with a new prompt describing the change.
- Default output directory is `./generated-images`; pass `--out-dir` to direct
  files into a project/workspace folder shared with other agents.
- Keep prompts **specific and descriptive** (subject, style, lighting,
  composition, mood) for best results.
- Complex prompts can take up to ~2 minutes; the default timeout is 180s
  (`--timeout` to adjust).

## Notes & limits

- `gpt-image-2` does **not** support transparent backgrounds; omit
  `background: transparent` requests.
- Text rendering is strong but not pixel-perfect for dense/precise layouts.
- All prompts/outputs are subject to OpenAI's content policy.
