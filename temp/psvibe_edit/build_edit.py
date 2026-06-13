#!/usr/bin/env python3
"""Build complex ffmpeg filter for multi-clip edit with transitions."""
import subprocess, json, os

FFMPEG = "/home/node/.local/bin/ffmpeg"
WORK = "/home/node/.openclaw/workspace/temp/psvibe_edit"
FONT = "/home/node/.local/share/fonts/psvibe-font.ttf"
OVERLAY_PNG = os.path.join(WORK, "text_overlay.png")
MUSIC = "/home/node/.openclaw/media/tool-music-generation/psvibe_gaming_bg---4fd67743-338e-4a5f-a2c0-7b10d43fc88e.mp3"
OUTPUT = os.path.join(WORK, "tiktok_transitions.mp4")

# Source clips (sorted by order)
clips = [
    os.path.join(WORK, "7df7a7a8-5b28-4665-8b5b-63f97b672039.mp4"),  # 15.87s - game disc
    os.path.join(WORK, "3b159a83-0fdd-4b29-b895-02a641de9f62.mp4"),  # 13.76s
    os.path.join(WORK, "a84631e8-5a96-467c-b01c-7b2f0480753b.mp4"),  # 8.66s  
    os.path.join(WORK, "d89cfea4-20c6-4d83-adbb-d0e73b506b8a.mp4"),  # 27.26s
    os.path.join(WORK, "8ad7e467-cd85-4b78-8d7d-e5e27acedcdc.mp4"),  # 35.37s
    os.path.join(WORK, "e84522e6-b317-4d4f-b618-30c74fd0edcc.mp4"),  # 56.00s
]

# Transition config
TRANSITION_DURATION = 0.8  # seconds
transition_styles = ["fade", "slideright", "fadeblack", "slidedown", "fade"]

def get_duration(path):
    """Get video duration using ffprobe via ffmpeg."""
    cmd = [FFMPEG, "-i", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration" in line:
            dur_str = line.strip().split(",")[0].split("Duration: ")[1]
            h, m, s = dur_str.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0

# Get all durations
durations = [get_duration(c) for c in clips]
print("Clips durations:", [f"{d:.2f}s" for d in durations])

# For TikTok, limit each clip to max ~12s
max_clip_dur = 12
trimmed_durs = [min(d, max_clip_dur) for d in durations]
print("Trimmed durations:", [f"{d:.2f}s" for d in trimmed_durs])

# Build filter graph for xfade
# Each clip gets trimmed, then chained with xfade
td = TRANSITION_DURATION

filter_parts = []

# Input trim + fade in/out
for i, dur in enumerate(trimmed_durs):
    input_idx = i
    # Trim to max duration
    filter_parts.append(f"[{input_idx}:v]trim=duration={dur},setpts=PTS-STARTPTS,fade=t=in:duration=0.5,fade=t=out:duration=0.5:start_time={dur-0.5}[v{i}]")

# Chain with xfade
# For n clips: need n-1 xfade ops
# offset for xfade k = sum of first k+1 trimmed_durs - td*(k+1)
running_offset = trimmed_durs[0]
prev_label = "v0"

for i in range(1, len(trimmed_durs)):
    trans = transition_styles[(i-1) % len(transition_styles)]
    offset = running_offset - td
    next_label = f"t{i}" if i < len(trimmed_durs) - 1 else "final_v"
    
    if i < len(trimmed_durs) - 1:
        filter_parts.append(f"[{prev_label}][v{i}]{f'xfade=transition={trans}:duration={td}:offset={offset}'}[{next_label}]")
    else:
        filter_parts.append(f"[{prev_label}][v{i}]{f'xfade=transition={trans}:duration={td}:offset={offset}'}[{next_label}]")
    
    running_offset += trimmed_durs[i]
    prev_label = next_label

# Total duration after transitions
total_dur = sum(trimmed_durs) - td * (len(trimmed_durs) - 1)
print(f"Total duration (after transitions): {total_dur:.2f}s")

# Add overlay on top
overlay_label = "final_v"
filter_parts.append(f"[{overlay_label}][3:v]overlay=0:H-h[layer0]")

# Actually the overlay is input 3 (text_overlay.png), but we have 6 video inputs
# Inputs: 0-5 = clips, 6 = overlay (png), 7 = music
# Let me re-index: video inputs are 0-5, overlay is 6, music is 7
# But I already used [0:v]..[5:v] for clips
# Overlay PNG is at index 6 → [6:v]
# Replace the last overlay filter
filter_parts[-1] = f"[{overlay_label}][6:v]overlay=0:H-h[{overlay_label}]"

# Add scale/pad for vertical format at the end
filter_parts.append(f"[{overlay_label}]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black[final_v2]")

# Audio part
filter_parts.append(f"[7:a]volume=0.25,aloop=loop=-1:size=2e9,atrim=duration={total_dur}[bgm]")
filter_parts.append(f"[0:a][1:a][2:a][3:a][4:a][5:a]amix=inputs=6:duration=longest[clip_audio]")
filter_parts.append(f"[clip_audio][bgm]amix=inputs=2:duration=first[final_a]")

complex_filter = ";".join(filter_parts)
print(f"\nFilter graph:\n{complex_filter[:500]}...\n")

# Build full ffmpeg command
input_files = clips + [OVERLAY_PNG, MUSIC]
inputs_args = []
for f in input_files:
    inputs_args.extend(["-i", f])

cmd = [FFMPEG] + inputs_args + [
    "-filter_complex", complex_filter,
    "-map", "[final_v2]",
    "-map", "[final_a]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k",
    "-y", OUTPUT
]

print("Running ffmpeg...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    size = os.path.getsize(OUTPUT) // (1024*1024)
    print(f"✅ Success! Output: {OUTPUT} ({size}MB)")
else:
    print(f"❌ Error (exit {result.returncode})")
    print(result.stderr[-1000:])
