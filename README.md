# VideoGenerator (upload)

This folder contains a minimal upload of the project's runnable files for convenient sharing.

- `main.py` — example runner that loads images and a script, constructs the TTS model, and calls `build_scenes` / `generate_video`.
- `vidgen.py` — video generation utilities (image resizing, TTS audio generation, scene rendering, and concat).

Requirements
- Python 3.8+
- `moviepy`, `Pillow`, and the TTS package you use (example uses `TTS.api`).
- `ffmpeg` available on PATH for final concatenation and video writing.

Quick start
1. Put your image files into `./images` and a script JSON into `./scripts` (the project expects `script_lines` key).
2. Update `TTS_MODEL` or other placeholders in `main.py` as needed.
3. Run:

```bash
python main.py
```
