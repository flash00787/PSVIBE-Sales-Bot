#!/usr/bin/env python3
"""Step-by-step xfade chain."""
import subprocess, os

FFMPEG = "/home/node/.local/bin/ffmpeg"
WORK = "/home/node/.openclaw/workspace/temp/psvibe_edit"

clips = [f"{WORK}/clip_a{i}.mp4" for i in range(6)]
durs = [12, 12, 8, 12, 12, 12]
td = 0.8
transitions = ["fade", "slideright", "fadeblack", "slidedown", "fade"]

current = clips[0]
offset_sum = durs[0]

for i in range(1, 6):
    next_clip = clips[i]
    temp_out = f"{WORK}/xfade_{i}.mp4"
    trans = transitions[i-1]
    offset = offset_sum - td
    
    print(f"Step {i}: {trans} offset={offset:.1f}s")
    
    cmd = [FFMPEG,
        "-i", current, "-i", next_clip,
        "-filter_complex", 
        f"[0:v][1:v]xfade=transition={trans}:duration={td}:offset={offset}[v];"
        f"[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-y", temp_out
    ]
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"❌ Error: {r.stderr[-500:]}")
        exit(1)
    
    current = temp_out
    offset_sum += durs[i] - td
    size = os.path.getsize(temp_out) // (1024*1024)
    print(f"  → {size}MB | cumulative: {offset_sum:.1f}s")

print(f"✅ All transitions done! Final: xfade_5.mp4")

# Now add overlay + music + resize
print("\nAdding overlay, music, and resize...")
overlay = f"{WORK}/text_overlay.png"
music = "/home/node/.openclaw/media/tool-music-generation/psvibe_gaming_bg---4fd67743-338e-4a5f-a2c0-7b10d43fc88e.mp3"
output = f"{WORK}/tiktok_final_v2.mp4"

final_dur = offset_sum

cmd2 = [FFMPEG,
    "-i", current, "-i", overlay, "-i", music,
    "-filter_complex",
    f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black[bg];"
    f"[bg][1:v]overlay=0:H-h[outv];"
    f"[2:a]volume=0.3,aloop=loop=-1:size=2e9,atrim=duration={final_dur}[bgm];"
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
    print(f"✅ FINAL OUTPUT: {output} ({size}MB, ~{final_dur:.0f}s)")
else:
    print(f"❌ Final error: {r2.stderr[-500:]}")
