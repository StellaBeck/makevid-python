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

Commit & push this `upload` folder to GitHub
1. (Optional) Set repo-local git identity if you don't want to set it globally:

```bash
cd "c:\Users\Admin\Documents\VSCodefiles\VideoGenerator\upload"
git config user.email "you@example.com"
git config user.name "Your Name"
```

2. Initialize, commit and push (replace the remote URL):

```bash
git init
git add main.py vidgen.py README.md
git commit -m "Add main.py, vidgen.py and README"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

If you prefer `gh` (GitHub CLI):

```bash
gh repo create REPO --public --source=. --push
```

Notes
- Replace `USERNAME/REPO` and the `user.email` / `user.name` placeholders with your actual values before pushing.
- If you hit the "unable to auto-detect email address" error, set `user.email` and `user.name` as shown above.
