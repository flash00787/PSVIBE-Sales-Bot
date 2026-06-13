#!/usr/bin/env python3
"""Multi-clip concat with xfade transitions using ffmpeg."""
import subprocess, os

FFMPEG = "/home/node/.local/bin/ffmpeg"
WORK = "/home/node/.openclaw/workspace/temp/psvibe_edit"

clips = [os.path.join(WORK, f"clip_{i}.mp4") for i in range(6)]
overlay = os.path.join(WORK, "text_overlay.png")
music = "/home/node/.openclaw/media/tool-music-generation/psvibe_gaming_bg---4fd67743-338e-4a5f-a2c0-7b10d43fc88e.mp3"
output = os.path.join(WORK, "tiktok_final_v2.mp4")

# Duration per clip (all ~12s except clip 2 = 8s)
durs = [12, 12, 8, 12, 12, 12]
td = 0.8  # transition duration
transitions = ["fade", "slideright", "fadeblack", "slidedown", "fade"]

# Build filter graph
# Process: trim each → xfade chain → overlay → scale to 9:16 → audio mix
filters = []

# Step 1: Trim + fade per clip
for i, d in enumerate(durs):
    ff = f"[{i}:v]trim=duration={d},setpts=PTS-STARTPTS,fade=t=in:d=0.5,fade=t=out:st={d-1}:d=1[v{i}]"
    filters.append(ff)

# Step 2: Audio processing - mix all clip audio
audio_filters = "".join([f"[{i}:a]" for i in range(6)])
filters.append(f"{audio_filters}amix=inputs=6:dropout_transition=2[clips_audio]")

# Step 3: Add bg music
filters.append(f"[7:a]volume=0.25,aloop=loop=-1:size=2e9,atrim=duration={sum(durs) - td*5}[bgm]")
filters.append(f"[clips_audio][bgm]amix=inputs=2:duration=first:weights=0.7 0.3[final_a]")

# Step 4: Chain xfade transitions
# offset calculation: sum of previous clip durations - td * num_transitions_so_far
running_offset = durs[0]
for i in range(1, 6):
    trans = transitions[i-1]
    offset = running_offset - td
    prev = f"v{i-1}" if i == 1 else f"t{i-1}"
    next_label = f"t{i}" if i < 5 else "final_v"
    filters.append(f"[{prev}][v{i}]xfade=transition={trans}:duration={td}:offset={offset}[{next_label}]")
    running_offset += durs[i] - td

# Step 5: Add overlay
total_dur = sum(durs) - td * 5
filters.append(f"[final_v][6:v]overlay=0:H-h[overlayed]")

# Step 6: Scale to 9:16
filters.append(f"[overlayed]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p[final_v]")

complex_filter = ";".join(filters)

# Build command
inputs = clips + [overlay, music]
cmd = [FFMPEG] + sum([["-i", f] for f in inputs], []) + [
    "-filter_complex", complex_filter,
    "-map", "[final_v]",
    "-map", "[final_a]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k",
    "-movflags", "+faststart",
    "-y", output
]

print(f"Total duration: ~{total_dur:.1f}s")
print(f"Running ffmpeg...")
result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stderr[-500:] if result.returncode != 0 else "✅ Done!")
if result.returncode == 0:
    size = os.path.getsize(output) // (1024*1024)
    print(f"Output: {output} ({size}MB)")
