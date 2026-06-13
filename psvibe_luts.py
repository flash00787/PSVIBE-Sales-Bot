#!/usr/bin/env python3
"""
PS VIBE LUT Generator v1.0
Creates professional color presets (1D LUTs) for instant color grading.

Usage:
  python3 psvibe_luts.py              # Generate all LUTs
  python3 psvibe_luts.py --list       # List available LUTs
"""
import os, struct, json, argparse
import numpy as np
from pathlib import Path

LUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "luts")
os.makedirs(LUT_DIR, exist_ok=True)

def apply_curve(r, g, b, **params):
    """Apply color curves."""
    # Extract params
    contrast = params.get('contrast', 1.0)
    brightness = params.get('brightness', 0.0)
    saturation = params.get('saturation', 1.0)
    shadows_r = params.get('shadows_r', 0)
    shadows_g = params.get('shadows_g', 0)
    shadows_b = params.get('shadows_b', 0)
    highlights_r = params.get('highlights_r', 0)
    highlights_g = params.get('highlights_g', 0)
    highlights_b = params.get('highlights_b', 0)
    temp = params.get('temp', 0)  # -1 to 1
    tint = params.get('tint', 0)  # -1 to 1
    vibrance = params.get('vibrance', 1.0)

    # Contrast (S-curve)
    r = ((r - 0.5) * contrast + 0.5)
    g = ((g - 0.5) * contrast + 0.5)
    b = ((b - 0.5) * contrast + 0.5)

    # Brightness
    r += brightness
    g += brightness
    b += brightness

    # Shadows tint
    shadow_mask = 1.0 - np.clip(r * 2, 0, 1)
    r += shadows_r * shadow_mask
    g += shadows_g * shadow_mask
    b += shadows_b * shadow_mask

    # Highlights tint
    highlight_mask = np.clip((r - 0.5) * 2, 0, 1)
    r += highlights_r * highlight_mask
    g += highlights_g * highlight_mask
    b += highlights_b * highlight_mask

    # Temperature (Blue <-> Yellow)
    r += temp * 0.05
    b -= temp * 0.05

    # Tint (Green <-> Magenta)
    g += tint * 0.05
    r -= tint * 0.025
    b -= tint * 0.025

    # Vibrance - boost desaturated colors more
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    r = gray + (r - gray) * vibrance
    g = gray + (g - gray) * vibrance
    b = gray + (b - gray) * vibrance

    # Saturation
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    r = np.clip(gray + (r - gray) * saturation, 0, 1)
    g = np.clip(gray + (g - gray) * saturation, 0, 1)
    b = np.clip(gray + (b - gray) * saturation, 0, 1)

    return np.clip(r, 0, 1), np.clip(g, 0, 1), np.clip(b, 0, 1)


def generate_cube_lut(name, description, size=33, **params):
    """Generate a .CUBE format 3D LUT (but using 1D for simplicity/compatibility)."""
    filename = os.path.join(LUT_DIR, f"{name}.cube")
    
    with open(filename, 'w') as f:
        f.write(f"TITLE \"PS VIBE - {description}\"\n")
        f.write(f"LUT_1D_SIZE {size}\n")
        f.write(f"DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write(f"DOMAIN_MAX 1.0 1.0 1.0\n")
        f.write("\n")
        
        for i in range(size):
            v = i / (size - 1)
            r, g, b = apply_curve(v, v, v, **params)
            f.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
    
    print(f"  ✅ {name}.cube — {description}")
    return filename


def generate_all_luts():
    """Generate all PS VIBE LUT presets."""
    print("🎨 Generating PS VIBE LUT Presets...\n")

    # 1. Cinematic - Cool shadows, warm highlights (Teal/Orange)
    generate_cube_lut("psvibe_cinematic", "Cinematic Teal/Orange",
        contrast=1.15, saturation=0.85, brightness=-0.02,
        shadows_r=-0.05, shadows_g=-0.02, shadows_b=0.08,
        highlights_r=0.08, highlights_g=0.02, highlights_b=-0.05,
        temp=-0.3, vibrance=1.1)

    # 2. Gaming - Punchy, saturated, high contrast
    generate_cube_lut("psvibe_gaming", "Vibrant Gaming",
        contrast=1.25, saturation=1.3, brightness=0.02,
        vibrance=1.2, temp=0.1)

    # 3. Warm - Golden hour vibe
    generate_cube_lut("psvibe_warm", "Warm Golden",
        temp=0.5, tint=0.1, saturation=1.1, contrast=1.1,
        brightness=0.02)

    # 4. Cyberpunk - Purple/Blue cool tones
    generate_cube_lut("psvibe_cyber", "Cyberpunk Neon",
        contrast=1.2, saturation=1.2, brightness=-0.03,
        shadows_r=0.1, shadows_g=-0.05, shadows_b=0.15,
        highlights_r=-0.1, highlights_g=0.0, highlights_b=0.1,
        temp=-0.5, vibrance=1.3)

    # 5. BW - Black & White with punch
    generate_cube_lut("psvieve_bw", "Black & White Punch",
        contrast=1.3, saturation=0.0, brightness=0.0,
        vibrance=0.0)

    # 6. Soft - Clean, bright, soft contrast for faces
    generate_cube_lut("psvibe_soft", "Soft Clean",
        contrast=0.95, saturation=0.9, brightness=0.05,
        shadows_r=0.02, shadows_g=0.02, shadows_b=0.02,
        vibrance=0.9)

    # 7. HDR - Extra punchy for gaming clips
    generate_cube_lut("psvibe_hdr", "HDR Punch",
        contrast=1.35, saturation=1.4, brightness=0.03,
        vibrance=1.3, shadows_r=-0.03, shadows_g=0.0, shadows_b=0.03,
        highlights_r=0.0, highlights_g=0.02, highlights_b=0.0)

    # 8. Moody - Dark, moody gaming atmosphere
    generate_cube_lut("psvibe_moody", "Dark Moody",
        contrast=1.2, saturation=0.7, brightness=-0.08,
        shadows_r=0.02, shadows_g=0.0, shadows_b=0.03,
        vibrance=0.8, temp=-0.2)

    print(f"\n✅ {len(os.listdir(LUT_DIR))} LUTs generated in {LUT_DIR}/")
    return True


def list_luts():
    """List available LUTs with descriptions."""
    luts = [f for f in os.listdir(LUT_DIR) if f.endswith('.cube')]
    if not luts:
        print("No LUTs found. Run without --list to generate.")
        return
    
    print(f"🎨 PS VIBE LUT Presets ({len(luts)} available):\n")
    for lut in sorted(luts):
        name = lut.replace('.cube', '')
        # Read title from file
        with open(os.path.join(LUT_DIR, lut)) as f:
            title = f.readline().strip().replace('TITLE "PS VIBE - ', '').replace('"', '')
        print(f"  📍 {name:20s} → {title}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PS VIBE LUT Generator")
    parser.add_argument("--list", action="store_true", help="List available LUTs")
    args = parser.parse_args()

    if args.list:
        list_luts()
    else:
        generate_all_luts()
