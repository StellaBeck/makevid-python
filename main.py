from TTS.api import TTS
from vidgen import *
import json

TTS_MODEL = "tts_models/en/vctk/vits"

def main():
    # Example inputs — replace with your own images and script or
    # adapt this to read from files/CLI arguments.
    images = load_images_from_folder("./images")
    #["./images/1.jpg", "./images/2.jpg", "./images/3.jpg"]
    script = load_script_json("./scripts/test.json")
    
    print("Loading TTS model...")
    tts = TTS(TTS_MODEL)

    clips = build_scenes(images, script, tts)
    generate_video(clips, "test_output.mp4")

def load_images_from_folder(folder):
    valid_ext = (".jpg", ".jpeg", ".png", ".webp")

    files = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(valid_ext)
    ])

    return files

def load_script_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["script_lines"]

if __name__ == "__main__":
    main()
