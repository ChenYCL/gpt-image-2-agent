# gpt-image-2-agent Skill

An [OpenClaw](https://openclaw.ai) / [LobeHub](https://lobehub.com) skill (package name: `gpt-image-2-agent`) that generates and edits images with OpenAI's **`gpt-image-2`** model.

Supports **text-to-image**, **image-to-image editing**, **multi-reference composition**, and **mask-based inpainting**. Results are saved as local files and returned as structured JSON, so other agents/tools can consume the output directly.

## ✨ Features

- 🎨 Text-to-image generation
- 🖼️ Image-to-image editing (one or more reference images)
- 🧩 Compose a new image from multiple references
- 🩹 Mask-based inpainting
- 📦 **Zero third-party dependencies** — pure Python stdlib
- 🤝 Structured JSON output for agent-to-agent handoff
- 🔐 No hard-coded secrets — credentials come from env/config

## 🚀 Install

In LobeHub / OpenClaw, install from this repo URL:

```
https://github.com/ChenYCL/gpt-image-2-agent
```

Or clone manually:

```bash
git clone https://github.com/ChenYCL/gpt-image-2-agent.git
```

## 🔑 Setup (the only thing each user must do)

Provide an API key. Resolution order: **CLI flag → env var → `config.json` → default**.

### Option A — Environment variables (recommended)

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | API key with image generation scope (**required**) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Proxy / OpenAI-compatible gateway |
| `GPT_IMAGE_MODEL` | `gpt-image-2` | Override the model name |

### Option B — Config file

```bash
cp config.example.json config.json   # then fill in your key
```

> `config.json` holds your secret and is **gitignored** — it is never committed.


## ✅ Agent/chat behavior

This skill is designed for chat-agent use:

1. The agent injects saved LobeHub credentials when available.
2. The script reads `OPENAI_API_KEY` / `OPENAI_BASE_URL` from the environment, or falls back to `config.json`.
3. If credentials are missing, the script returns a structured `missing_api_key` JSON error with setup guidance.
4. On success, the agent parses `images[].path`, exports the image when running in sandbox, and shows a preview/download link in chat.

## 📖 Usage

```bash
# Text-to-image
python3 scripts/generate.py "a cozy reading nook by a rainy window, warm light" --out-dir ./generated-images

# Control size / quality / format
python3 scripts/generate.py "minimalist mountain logo, flat vector" --size 1024x1024 --quality high --format png

# Image-to-image editing
python3 scripts/generate.py "place this product on a marble counter" --ref ./product.png --quality high

# Inpainting with a mask
python3 scripts/generate.py "replace the sky with a dramatic sunset" --ref ./photo.png --mask ./sky-mask.png
```

See [`SKILL.md`](./SKILL.md) for the full reference, all flags, and output format.

## 🤖 Agent collaboration

On success the script prints a JSON object to **stdout** with `images[].path`; on failure a JSON error goes to **stderr** with `"ok": false`. Parse stdout and read the file paths to hand results off downstream.

## 📝 Notes

- `gpt-image-2` does not support transparent backgrounds.
- All prompts/outputs are subject to OpenAI's content policy.

## License

MIT
