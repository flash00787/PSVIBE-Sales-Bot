#!/usr/bin/env python3
"""
PS VIBE Video Editor v1.0
Boss shoots → Kora edits 🎬

Usage:
  python3 psvibe_video_editor.py concat --clips clip1.mp4 clip2.mp4 -o output.mp4
  python3 psvibe_video_editor.py overlay -i input.mp4 -t "PS VIBE" -o output.mp4
  python3 psvibe_video_editor.py thumbnail -i input.mp4 -o thumb.jpg
  python3 psvibe_video_editor.py full -i input.mp4 -o output.mp4 --music bg.mp3
"""
import os, sys, json, argparse, subprocess, tempfile, shutil
from pathlib import Path

FFMPEG = "/home/node/.local/bin/ffmpeg"
FFPROBE = FFMPEG.replace("ffmpeg", "ffprobe")

def ffmpeg(*args, **kwargs):
    """Run ffmpeg command."""
    cmd = [FFMPEG] + list(args)
    print(f"🎬 {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    if r.returncode != 0:
        print(f"❌ FFmpeg error: {r.stderr[:500]}")
        return False
    return True

def get_video_info(path):
    """Get video dimensions, duration, fps."""
    cmd = [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    data = json.loads(r.stdout)
    for s in data.get("streams", []):
        if s["codec_type"] == "video":
            return {
                "width": int(s["width"]),
                "height": int(s["height"]),
                "fps": eval(s.get("r_frame_rate", "30/1")),
                "duration": float(data["format"]["duration"]),
                "size": int(data["format"]["size"]),
            }
    return None

# ═══════════════════════════════════════════
# 1. CONCATENATE CLIPS
# ═══════════════════════════════════════════
def concat_clips(clips, output, transition=None):
    """Join multiple video clips. Optionally add fade transitions."""
    if len(clips) < 2:
        print("❌ Need at least 2 clips to concatenate.")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        list_file = os.path.join(tmpdir, "files.txt")
        with open(list_file, "w") as f:
            for clip in clips:
                abs_path = os.path.abspath(clip)
                f.write(f"file '{abs_path}'\n")

        success = ffmpeg("-f", "concat", "-safe", "0", "-i", list_file,
                        "-c", "copy", "-y", output)
        if success:
            print(f"✅ Concatenated → {output}")
        return success

# ═══════════════════════════════════════════
# 2. TEXT OVERLAY (PS VIBE Branding)
# ═══════════════════════════════════════════
def add_text_overlay(input_file, output, text="PS VIBE", position="bottom",
                     font_size=36, color="white", shadow=True):
    """Add PS VIBE text overlay to video."""
    info = get_video_info(input_file)
    if not info:
        return False

    # Position mapping
    pos_map = {
        "bottom": "x=(w-text_w)/2:y=h-th-40",
        "top": "x=(w-text_w)/2:y=40",
        "top-left": "x=40:y=40",
        "top-right": "x=w-text_w-40:y=40",
        "bottom-left": "x=40:y=h-th-40",
        "bottom-right": "x=w-text_w-40:y=h-th-40",
        "center": "x=(w-text_w)/2:y=(h-th)/2",
    }
    pos = pos_map.get(position, pos_map["bottom"])

    filter_str = (
        f"drawtext=text='{text}':"
        f"fontcolor={color}:fontsize={font_size}:" 
        f"fontfile=/home/node/.local/share/fonts/psvibe-font.ttf:"
        f"{'shadowcolor=black:shadowx=2:shadowy=2:' if shadow else ''}"
        f"{pos}:enable='between(t,0,9999)'"
    )

    success = ffmpeg("-i", input_file,
                    "-vf", filter_str,
                    "-c:a", "copy", "-y", output)
    if success:
        print(f"✅ Text overlay added → {output}")
    return success

# ═══════════════════════════════════════════
# 3. ADD BACKGROUND MUSIC
# ═══════════════════════════════════════════
def add_music(input_file, music_file, output, volume=0.3, loop=True):
    """Add background music to video with volume control."""
    info = get_video_info(input_file)
    if not info:
        return False

    dur = info["duration"]
    
    # If loop needed, use amovie to loop
    if loop:
        filter_str = (
            f"[1:a]volume={volume},aloop=loop=-1:size=2e9,atrim=d={dur}[a1];"
            f"[0:a][a1]amix=inputs=2:duration=first[a]"
        )
    else:
        filter_str = (
            f"[1:a]volume={volume}[a1];"
            f"[0:a][a1]amix=inputs=2:duration=first[a]"
        )

    success = ffmpeg("-i", input_file, "-i", music_file,
                    "-filter_complex", filter_str,
                    "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-y", output)
    if success:
        print(f"✅ Background music added → {output}")
    return success

# ═══════════════════════════════════════════
# 4. TRIM VIDEO
# ═══════════════════════════════════════════
def trim_video(input_file, output, start=0, end=None):
    """Trim video from start to end time (seconds)."""
    info = get_video_info(input_file)
    if not info:
        return False
    
    if end is None:
        end = info["duration"]

    success = ffmpeg("-i", input_file,
                    "-ss", str(start), "-to", str(end),
                    "-c", "copy", "-y", output)
    if success:
        print(f"✅ Trimmed ({start}s → {end}s) → {output}")
    return success

# ═══════════════════════════════════════════
# 5. GENERATE THUMBNAIL
# ═══════════════════════════════════════════
def generate_thumbnail(input_file, output, time=1, width=1280):
    """Generate a thumbnail image from video at given timestamp."""
    success = ffmpeg("-i", input_file, "-ss", str(time), "-vframes", "1",
                    "-vf", f"scale={width}:-1", "-y", output)
    if success:
        size = os.path.getsize(output) // 1024
        print(f"✅ Thumbnail generated → {output} ({size}KB)")
    return success

# ═══════════════════════════════════════════
# 6. FULL EDIT (All-in-one)
# ═══════════════════════════════════════════
def full_edit(input_file, output, text="PS VIBE", text_pos="bottom",
              music_file=None, music_volume=0.3, trim_start=0, trim_end=None,
              intro_file=None, outro_file=None, resize=None):
    """Full pipeline: trim → intro → concat → text → music → resize."""
    info = get_video_info(input_file)
    if not info:
        return False

    files_to_clean = []
    
    # Step 1: Extract trimmed segment
    current = input_file
    if trim_start > 0 or trim_end is not None:
        trimmed = output + ".trimmed.mp4"
        if not trim_video(input_file, trimmed, trim_start, trim_end):
            return False
        current = trimmed
        files_to_clean.append(trimmed)

    # Step 2: Add intro/outro if needed
    clips = []
    if intro_file:
        clips.append(intro_file)
    clips.append(current)
    if outro_file:
        clips.append(outro_file)

    if len(clips) > 1:
        with tempfile.TemporaryDirectory() as tmpdir:
            list_file = os.path.join(tmpdir, "files.txt")
            with open(list_file, "w") as f:
                for c in clips:
                    f.write(f"file '{os.path.abspath(c)}'\n")
            concatted = output + ".concat.mp4"
            if not ffmpeg("-f", "concat", "-safe", "0", "-i", list_file,
                         "-c", "copy", "-y", concatted):
                return False
            current = concatted
    else:
        current = clips[0] if clips else current

    # Step 3: Add text overlay
    texted = output + ".text.mp4"
    if not add_text_overlay(current, texted, text, text_pos):
        return False
    current = texted

    # Step 4: Add background music
    if music_file:
        music_added = output + ".music.mp4"
        if not add_music(current, music_file, music_added, music_volume):
            return False
        current = music_added

    # Step 5: Resize if needed
    if resize:
        resized = output + ".resized.mp4"
        success = ffmpeg("-i", current, "-vf", f"scale={resize}", "-c:a", "copy", "-y", resized)
        if not success:
            return False
        current = resized

    # Move final output
    shutil.move(current, output)
    print(f"✅ Full edit complete → {output}")
    return True


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PS VIBE Video Editor")
    sub = parser.add_subparsers(dest="command", required=True)

    # concat
    p_concat = sub.add_parser("concat", help="Join video clips")
    p_concat.add_argument("--clips", nargs="+", required=True)
    p_concat.add_argument("-o", "--output", required=True)

    # overlay
    p_overlay = sub.add_parser("overlay", help="Add PS VIBE text")
    p_overlay.add_argument("-i", "--input", required=True)
    p_overlay.add_argument("-o", "--output", required=True)
    p_overlay.add_argument("-t", "--text", default="PS VIBE")
    p_overlay.add_argument("--pos", default="bottom")
    p_overlay.add_argument("--size", type=int, default=36)
    p_overlay.add_argument("--color", default="white")

    # music
    p_music = sub.add_parser("music", help="Add background music")
    p_music.add_argument("-i", "--input", required=True)
    p_music.add_argument("-m", "--music", required=True)
    p_music.add_argument("-o", "--output", required=True)
    p_music.add_argument("--volume", type=float, default=0.3)
    p_music.add_argument("--no-loop", action="store_false", dest="loop")

    # trim
    p_trim = sub.add_parser("trim", help="Trim video")
    p_trim.add_argument("-i", "--input", required=True)
    p_trim.add_argument("-o", "--output", required=True)
    p_trim.add_argument("-s", "--start", type=float, default=0)
    p_trim.add_argument("-e", "--end", type=float)

    # thumbnail
    p_thumb = sub.add_parser("thumbnail", help="Generate thumbnail")
    p_thumb.add_argument("-i", "--input", required=True)
    p_thumb.add_argument("-o", "--output", required=True)
    p_thumb.add_argument("-t", "--time", type=float, default=1)
    p_thumb.add_argument("-w", "--width", type=int, default=1280)

    # full
    p_full = sub.add_parser("full", help="Full pipeline edit")
    p_full.add_argument("-i", "--input", required=True)
    p_full.add_argument("-o", "--output", required=True)
    p_full.add_argument("--text", default="PS VIBE")
    p_full.add_argument("--text-pos", default="bottom")
    p_full.add_argument("--music", help="Background music file")
    p_full.add_argument("--music-volume", type=float, default=0.3)
    p_full.add_argument("--trim-start", type=float, default=0)
    p_full.add_argument("--trim-end", type=float)
    p_full.add_argument("--intro", help="Intro video")
    p_full.add_argument("--outro", help="Outro video")
    p_full.add_argument("--resize", help="e.g. 1080x1920, 1920x1080")

    args = parser.parse_args()

    if args.command == "concat":
        concat_clips(args.clips, args.output)
    elif args.command == "overlay":
        add_text_overlay(args.input, args.output, args.text, args.pos, args.size, args.color)
    elif args.command == "music":
        add_music(args.input, args.music, args.output, args.volume, args.loop)
    elif args.command == "trim":
        trim_video(args.input, args.output, args.start, args.end)
    elif args.command == "thumbnail":
        generate_thumbnail(args.input, args.output, args.time, args.width)
    elif args.command == "full":
        full_edit(args.input, args.output, args.text, args.text_pos,
                 args.music, args.music_volume, args.trim_start, args.trim_end,
                 args.intro, args.outro, args.resize)
