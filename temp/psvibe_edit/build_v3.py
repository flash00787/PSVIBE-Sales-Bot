#!/usr/bin/env python3
"""Simple concat with xfade transitions + overlay + music."""
import subprocess, os

FFMPEG = "/home/node/.local/bin/ffmpeg"
WORK = "/home/node/.openclaw/workspace/temp/psvibe_edit"

clips = [f"{WORK}/clip_{i}.mp4" for i in range(6)]
overlay_png = f"{WORK}/text_overlay.png"
music_file = "/home/node/.openclaw/media/tool-music-generation/psvibe_gaming_bg---4fd67743-338e-4a5f-a2c0-7b10d43fc88e.mp3"
output = f"{WORK}/tiktok_final_v2.mp4"

durs = [12, 12, 8, 12, 12, 12]
td = 0.8
N = 6

# Method: process 1 clip at a time into a growing chain
# Use Python to run ffmpeg incrementally
# Step 1: Start with clip_0
# Step 2: xfade with clip_1 → temp_1
# Step 3: xfade temp_1 with clip_2 → temp_2
# Continue...

current = clips[0]
for i in range(1, N):
    next_clip = clips[i]
    temp_out = f"{WORK}/temp_{i}.mp4"
    
    trans = ["fade", "slideright", "fadeblack", "slidedown", "fade"][i-1]
    offset = durs[i-1] - td
    
    cmd = [FFMPEG,
        "-i", current, "-i", next_clip,
        "-filter_complex", f"[0:v][1:v]xfade=transition={trans}:duration={td}:offset={offset}[v];[0:a][1:a]amix=inputs=2:duration=first[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-y", temp_out
    ]
    print(f"Step {i}: xfade ({trans})...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"Error at step {i}: {r.stderr[-300:]}")
        exit(1)
    current = temp_out
    durs[i] = durs[i] + durs[i-1] - td  # update cumulative duration

print("All transitions done. Adding overlay + music...")

# Add overlay and music
cmd2 = [FFMPEG,
    "-i", current, "-i", overlay_png, "-i", music_file,
    "-filter_complex",
    f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black[bg];"
    f"[bg][1:v]overlay=0:H-h[outv];"
    f"[2:a]volume=0.25,aloop=loop=-1:size=2e9,atrim=duration={durs[-1]}[bgm];"
    f"[0:a][bgm]amix=inputs=2:duration=first:weights=0.7 0.3[outa]",
    "-map", "[outv]", "-map", "[outa]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k",
    "-movflags", "+faststart",
    "-y", output
]

r2 = subprocess.run(cmd2, capture_output=True, text=True)
if r2.returncode == 0:
    size = os.path.getsize(output) // (1024*1024)
    print(f"✅ Done! Output: {output} ({size}MB, ~{durs[-1]:.0f}s)")
else:
    print(f"Error: {r2.stderr[-500:]}")
