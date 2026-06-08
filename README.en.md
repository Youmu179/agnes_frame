# Agnes Agent

An unofficial desktop shell for testing Agnes free models from a simple Agent-style GUI.

中文说明: [README.md](README.md)

> This project was mainly generated and iterated with Codex GPT-5.5. It is not an official Agnes / Sapiens AI client.

## Features

- Chat Agent: `agnes-2.0-flash`, multi-turn chat, streaming output, optional Thinking / Reasoning panel, context usage view, and 90% threshold auto-compression.
- Image Studio: defaults to the free `agnes-image-2.1-flash`, with `agnes-image-2.0-flash` still selectable; text-to-image, URL image editing, multi-image composition, preview and save.
- Video Studio: `agnes-video-v2.0`, text-to-video, image-to-video, multi-image video, keyframe animation, async polling.

## Use The Release EXE

1. Download `AgnesModelTester.exe` from GitHub Releases.
2. Run it.
3. Open Settings from the lower-left corner.
4. Enter your Agnes API Key.
5. Enable local API-key persistence only if you want the key saved locally.
6. Start using Chat, Image Studio, or Video Studio.

Default API Base URL:

```text
https://apihub.agnes-ai.com
```

## Notes

- Agnes Video image input requires a public image URL.
- Local image upload is integrated through a configurable image-hosting API. The default `auto` mode prefers `img.scdn.io`.
- Third-party image hosts are public services. Do not upload private images.
- Local sessions are saved to `agnes_data\sessions.json` by default.
- Build artifacts and local data should generally stay out of source control.

## Run From Source

```bat
conda activate py313
pip install -r requirements.txt
python agnes_gui.py
```

## Build

Run:

```text
build_onefile.bat
```

The output is:

```text
dist\AgnesModelTester.exe
```

## Official Docs

- [Common API Docs](https://agnes-ai.com/doc/%E5%B8%B8%E7%94%A8%E6%8E%A5%E5%85%A5%E6%96%87%E6%A1%A3)
- [Agnes-2.0-Flash](https://agnes-ai.com/doc/agnes-20-flash)
- [Agnes Image 2.1 Flash](https://agnes-ai.com/doc/agnes-image-21-flash)
- [Agnes-Image-2.0-Flash](https://agnes-ai.com/doc/agnes-image-20-flash)
- [Agnes-Video-V2.0](https://agnes-ai.com/doc/agnes-video-v20)
- [img.scdn.io API](https://img.scdn.io/api_docs.php)
