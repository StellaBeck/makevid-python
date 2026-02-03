#from TTS.api import TTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip
import uuid
import os
from PIL import Image
import shutil
import tempfile
import subprocess
import gc
import glob


# --------------------------
# TTS SETTINGS
# --------------------------

TTS_SPEAKER = "p299"    # male voice

# Default output video resolution — lower by default to reduce memory usage.
# Change to (1920, 1080) if you have sufficient RAM.
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# ----------------------------
# Helper: center-crop image to target size
# ----------------------------
def center_crop_resize(image_path, target_width, target_height):
    img = Image.open(image_path)
    w, h = img.size

    # Determine crop box (center crop)
    target_ratio = target_width / target_height
    img_ratio = w / h

    if img_ratio > target_ratio:
        # image too wide, crop sides
        new_w = int(h * target_ratio)
        offset = (w - new_w) // 2
        box = (offset, 0, offset + new_w, h)
    else:
        # image too tall, crop top/bottom
        new_h = int(w / target_ratio)
        offset = (h - new_h) // 2
        box = (0, offset, w, offset + new_h)

    cropped = img.crop(box)
    resized = cropped.resize((target_width, target_height))
    return resized
# --------------------------
# 1) Build scenes → MoviePy clips
# --------------------------
def build_scenes(images, script_lines, tts, width=VIDEO_WIDTH, height=VIDEO_HEIGHT):
    """
    Returns a list of MoviePy clips:
    - Generates TTS for each line
    - Matches each audio with image
    - Duration = audio duration
    """

    if len(images) != len(script_lines):
        raise ValueError("Images list and script list must be the same length.")

    os.makedirs("temp_audio", exist_ok=True)

    clips = []

    for img_path, text in zip(images, script_lines):
        print(f"\nGenerating audio for: {text}")

        # unique audio filename
        audio_path = f"temp_audio/{uuid.uuid4().hex}.wav"

        # Generate TTS
        tts.tts_to_file(
            text=text,
            speaker=TTS_SPEAKER,
            file_path=audio_path
        )

        # Load audio briefly to read duration, then close to free memory
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        try:
            audio.close()
        except Exception:
            pass
        del audio
        gc.collect()

        # Build clip (resized to chosen output resolution)
        # Resize and save a scene-specific temp image (unique per scene)
        img = center_crop_resize(img_path, width, height)
        img_path_temp = f"temp_resized_{uuid.uuid4().hex}.png"
        img.save(img_path_temp)

        # Store a lightweight descriptor instead of keeping MoviePy clips in memory
        clips.append({
            'image': img_path_temp,
            'audio': audio_path,
            'text': text,
            'duration': duration,
            'width': width,
            'height': height,
        })

    return clips


# --------------------------
# 2) Generate video + CLEANUP
# --------------------------
def generate_video(clips, output_file="final_video.mp4"):
    """
    Combines clips → exports final video → cleans temp_audio folder.
    """
    # Sequential rendering: write each scene to a temp file and concat with ffmpeg.
    print("\nRendering scenes sequentially to reduce memory usage...")

    temp_dir = tempfile.mkdtemp(prefix="temp_scenes_")
    scene_files = []

    try:
        for i, scene in enumerate(clips, start=1):
            scene_path = os.path.join(temp_dir, f"scene_{i:03d}.mp4")
            print(f"Rendering scene {i}/{len(clips)} -> {scene_path}")

            # Build the clip for this scene only
            img_clip = ImageClip(scene['image']).with_duration(scene['duration'])

            # Slow zoom-in (Ken Burns). 1.0 -> zoom_amount over the clip duration.
            zoom_amount = 1.05  # 1.05 subtle, 1.15 stronger
            duration = scene['duration']
            img_clip = img_clip.resized(lambda t: 1 + (zoom_amount - 1) * (t / duration)).with_position(('center', 'center'))

            txt_clip = (TextClip(
                    text=scene['text'] + '\n',
                    font_size=46,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    method='caption',
                    size=(int(scene['width'] * 0.9), None)
                )
                .with_position(('center', scene['height'] - 150))
                .with_duration(scene['duration'])
            )

            audio = AudioFileClip(scene['audio'])

            composite = CompositeVideoClip([img_clip, txt_clip], size=(scene['width'], scene['height'])).with_audio(audio)

            # Write each clip to disk (use libx264 + aac for compatibility)
            composite.write_videofile(
                scene_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                threads=0
            )

            # free memory used by this scene
            try:
                composite.close()
            except Exception:
                pass
            try:
                img_clip.close()
            except Exception:
                pass
            try:
                txt_clip.close()
            except Exception:
                pass
            try:
                audio.close()
            except Exception:
                pass

            del composite, img_clip, txt_clip, audio
            gc.collect()

            # remove the temp resized image for this scene
            try:
                os.remove(scene['image'])
            except Exception:
                pass

            scene_files.append(scene_path)

        # Create ffmpeg concat file list
        concat_list = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list, 'w', encoding='utf-8') as f:
            for p in scene_files:
                # ffmpeg concat demuxer expects paths like: file 'path'
                f.write(f"file '{os.path.abspath(p).replace("'", "'\\\'")}'\n")

        print(f"\nConcatenating {len(scene_files)} scenes -> {output_file}")

        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-f', 'concat', '-safe', '0', '-i', concat_list,
            '-c', 'copy', output_file
        ]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            # If stream-copy concat fails (codec/profile mismatch), fallback to re-encoding
            print("Concat with stream copy failed — falling back to re-encode with ffmpeg.")
            cmd = [
                'ffmpeg', '-hide_banner', '-loglevel', 'error',
                '-f', 'concat', '-safe', '0', '-i', concat_list,
                '-c:v', 'libx264', '-c:a', 'aac', '-movflags', '+faststart', output_file
            ]
            subprocess.run(cmd, check=True)

    finally:
        # cleanup temporary scene files
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

        # --------------------------
        # CLEANUP temp_audio folder
        # --------------------------
        if os.path.exists("temp_audio"):
            print("\nCleaning up temp_audio...")
            shutil.rmtree("temp_audio", ignore_errors=True)

        # --------------------------
        # CLEANUP leftover temp_resized images
        # --------------------------
        for p in glob.glob("temp_resized_*.png"):
            try:
                os.remove(p)
            except Exception:
                pass

    print("DONE ✓")


# Example usage has been moved to `main.py` so this module can be
# imported without executing the example run.  See `main.py` for a
# runnable `main()` that constructs the TTS model and calls
# `build_scenes` / `generate_video`.
