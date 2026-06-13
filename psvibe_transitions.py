#!/usr/bin/env python3
"""
PS VIBE Transitions & Motion Graphics v2.0
MoviePy v2 compatible. Professional animated templates for social media.

Usage:
  python3 psvibe_transitions.py create-intro -t "PS VIBE" -o intro.mp4
  python3 psvibe_transitions.py create-lower-third -t "Now Playing" -v "Game" -o lower.mp4
  python3 psvibe_transitions.py create-package -t "6 Hours" -p "25,000 Ks" -o package.mp4
  python3 psvibe_transitions.py create-game-showcase -g "God of War" -o showcase.mp4
"""
import os, sys, argparse
import numpy as np
from moviepy import *

FONT = '/home/node/.local/share/fonts/psvibe-font.ttf'
FONT_BOLD = '/home/node/.local/share/fonts/psvibe-font.ttf'
W, H = 1080, 1920
FPS = 30

PURPLE = (100, 20, 255)
GOLD = '#FFD700'
WHITE = 'white'
DARK = '#0d001a'

def cpos(x, y, t=0):
    """Center position helper."""  
    return ('center', y)

# ═══════════════════════════════════════════
# ANIMATED INTRO (5s)
# ═══════════════════════════════════════════
def create_intro(text="PS VIBE", subtitle="Play The Game. Share The VIBE!", 
                 output="psvibe_intro.mp4"):
    print(f"🎬 Intro: '{text}'")
    D = 5

    bg = ColorClip(size=(W, H), color=PURPLE, duration=D)
    
    # Main text - slide up
    txt = TextClip(font=FONT, text=text, font_size=140, color=WHITE,
                   stroke_color=GOLD, stroke_width=3, duration=D)
    def txt_pos(t):
        if t < 0.3: y = H + 200
        elif t < 1.3: y = H + 200 - (H + 200 - 500) * ((t-0.3)/1.0)
        else: y = 500
        return ('center', y)
    txt = txt.with_position(txt_pos)

    # Subtitle - fades in later
    sub = TextClip(font=FONT, text=subtitle, font_size=40, color=(255,215,0), duration=D)
    def sub_pos(t):
        return ('center', 680) if t > 1.0 else ('center', -200)
    sub = sub.with_position(sub_pos)

    # Gold accent bars
    bars = []
    for i, (y_pos, w) in enumerate([(650, 300), (700, 300)]):
        bar = ColorClip(size=(w, 4), color=(255,215,0), duration=D)
        def bpos(t, y=y_pos, base_w=w):
            if t < 1.5:
                return ('center', -10)
            return ('center', y)
        bars.append(bar.with_position(bpos))

    video = CompositeVideoClip([bg] + bars + [txt, sub], size=(W, H))
    video = video.with_effects([vfx.FadeIn(0.3), vfx.FadeOut(0.5)])
    video.write_videofile(output, fps=FPS, codec='libx264', audio=False, logger=None)
    print(f"  ✅ {output}")
    return output


# ═══════════════════════════════════════════
# LOWER THIRD (5s)
# ═══════════════════════════════════════════
def create_lower_third(text="Now Playing:", value="God of War Ragnarök",
                       output="psvibe_lower.mp4"):
    print(f"🎬 Lower third: '{text} {value}'")
    D = 5

    # Transparent bg bar with opacity
    bg_bar = ColorClip(size=(750, 100), color=PURPLE, duration=D)
    bg_bar = bg_bar.with_opacity(0.85)

    # Slide in from left
    def slide_x(t, start_x=-800, end_x=40):
        if t < 0.3: return start_x
        if t < 0.8: return start_x + (end_x - start_x) * ((t-0.3)/0.5)
        return end_x

    bg_bar = bg_bar.with_position(lambda t: (slide_x(t), H-200))
    
    # Gold accent strip
    accent = ColorClip(size=(10, 100), color=(255,215,0), duration=D)
    accent = accent.with_position(lambda t: (slide_x(t), H-200))

    # Label
    label = TextClip(font=FONT, text=text, font_size=28, color=(255,215,0), duration=D)
    label = label.with_position(lambda t: (slide_x(t)+30, H-190))

    # Value
    val = TextClip(font=FONT, text=value, font_size=44, color=WHITE, duration=D)
    val = val.with_position(lambda t: (slide_x(t)+30, H-155))

    video = CompositeVideoClip([bg_bar, accent, label, val], size=(W, H))
    video.write_videofile(output, fps=FPS, codec='libx264', audio=False, logger=None)
    print(f"  ✅ {output}")
    return output


# ═══════════════════════════════════════════
# PACKAGE PROMO (6s)
# ═══════════════════════════════════════════
def create_package_card(title="6 Hour Gaming", price="25,000 Ks",
                        features=None, output="psvibe_package.mp4"):
    if features is None:
        features = ["🎮 PS5 Console", "🥤 Free Drinks", "🍿 Snacks", "📶 WiFi"]
    print(f"🎬 Package: '{title}'")
    D = 6

    bg = ColorClip(size=(W, H), color=(26, 10, 46), duration=D)

    # Title with zoom
    title_clip = TextClip(font=FONT, text=title, font_size=90, color=WHITE,
                          stroke_color=GOLD, stroke_width=2, duration=D)
    title_clip = title_clip.with_position(('center', 300))

    # Price with bounce
    price_clip = TextClip(font=FONT, text=price, font_size=120, color=GOLD,
                          stroke_color='#000', stroke_width=2, duration=D)
    def price_pos(t):
        bounce = 5 * np.sin(t * 3) if t > 1 else 0
        return ('center', 500 + bounce)
    price_clip = price_clip.with_position(price_pos)

    # Features - slide in from left with stagger
    feat_clips = []
    for i, feat in enumerate(features):
        fc = TextClip(font=FONT_BOLD, text=f"▸ {feat}", font_size=38, color=WHITE, duration=D)
        def fpos(t, idx=i):
            delay = 1.5 + idx * 0.3
            if t < delay: return (-400, 730 + idx * 80)
            if t < delay + 0.4: return (-400 + 780 * ((t-delay)/0.4), 730 + idx * 80)
            return (380, 730 + idx * 80)
        feat_clips.append(fc.with_position(fpos))

    # Tagline
    tag = TextClip(font=FONT, text="Play The Game. Share The VIBE!", 
                   font_size=28, color=(255,215,0), duration=D)
    tag = tag.with_position(('center', 1300))

    video = CompositeVideoClip([bg] + feat_clips + [title_clip, price_clip, tag], size=(W, H))
    video = video.with_effects([vfx.FadeIn(0.5)])
    video.write_videofile(output, fps=FPS, codec='libx264', audio=False, logger=None)
    print(f"  ✅ {output}")
    return output


# ═══════════════════════════════════════════
# GAME SHOWCASE (8s)
# ═══════════════════════════════════════════
def create_game_showcase(game="God of War Ragnarök", console="PS5",
                          rating="⭐⭐⭐⭐⭐", output="psvibe_game.mp4"):
    print(f"🎬 Game showcase: '{game}'")
    D = 8

    bg = ColorClip(size=(W, H), color=(18, 0, 33), duration=D)

    # Game title - zoom in
    title = TextClip(font=FONT, text=game, font_size=90, color=WHITE,
                     stroke_color=GOLD, stroke_width=2, duration=D)
    def title_pos(t):
        if t < 0.5: return (-300, 400)
        if t < 1.2: return (-300 + 380 * ((t-0.5)/0.7), 400)
        return (80, 400)
    title = title.with_position(title_pos)

    # Console badge
    badge_bg = ColorClip(size=(200, 50), color=(0, 100, 200), duration=D)
    badge_bg = badge_bg.with_position((W//2 - 100, 600))
    badge_bg = badge_bg.with_opacity(0.8)
    
    badge_txt = TextClip(font=FONT, text=f"🎮 {console}", font_size=28, color=WHITE, duration=D)
    badge_txt = badge_txt.with_position(('center', 605))

    # Rating
    rating_clip = TextClip(font=FONT, text=rating, font_size=50, color=(255,215,0), duration=D)
    rating_clip = rating_clip.with_position(('center', 750))

    # Available at
    avail = TextClip(font=FONT, text="Available now at PS VIBE", font_size=36,
                     color='#8888FF', duration=D)
    avail = avail.with_position(('center', 900))

    # PS VIBE logo
    logo = TextClip(font=FONT, text="PS VIBE", font_size=50, color=WHITE, duration=D)
    logo = logo.with_position(lambda t: ('center', 1400 + 10 * np.sin(t*2)))

    # Decorative lines
    line1 = ColorClip(size=(W-200, 2), color=PURPLE, duration=D).with_position((100, 380))
    line2 = ColorClip(size=(W-200, 2), color=PURPLE, duration=D).with_position((100, 1000))

    video = CompositeVideoClip([bg, line1, line2, title, badge_bg, badge_txt,
                                rating_clip, avail, logo], size=(W, H))
    video = video.with_effects([vfx.FadeIn(0.5)])
    video.write_videofile(output, fps=FPS, codec='libx264', audio=False, logger=None)
    print(f"  ✅ {output}")
    return output


# ═══════════════════════════════════════════
# PROMO AD (10s) - Full promotional video
# ═══════════════════════════════════════════
def create_promo_ad(output="psvibe_promo.mp4"):
    """Generate full promotional ad for PS VIBE."""
    print("🎬 Promo ad...")
    D = 10
    
    clips = []
    
    # Scene 1: Logo reveal
    bg1 = ColorClip(size=(W, H), color=PURPLE, duration=3)
    txt1 = TextClip(font=FONT, text="PS VIBE", font_size=160, color=WHITE,
                    stroke_color=GOLD, stroke_width=3, duration=3)
    txt1 = txt1.with_position(('center', 600))
    sub1 = TextClip(font=FONT, text="PS5 Gaming Lounge", font_size=40, color=(255,215,0), duration=3)
    sub1 = sub1.with_position(('center', 800))
    scene1 = CompositeVideoClip([bg1, txt1, sub1], size=(W, H))
    scene1 = scene1.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
    clips.append(scene1)
    
    # Scene 2: Tagline
    bg2 = ColorClip(size=(W, H), color=(18, 0, 33), duration=3)
    txt2 = TextClip(font=FONT, text="Play The Game.", font_size=100, color=WHITE, duration=3)
    txt2 = txt2.with_position(('center', 700))
    sub2 = TextClip(font=FONT, text="Share The VIBE!", font_size=80, color=(255,215,0), duration=3)
    sub2 = sub2.with_position(('center', 850))
    scene2 = CompositeVideoClip([bg2, txt2, sub2], size=(W, H))
    scene2 = scene2.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
    clips.append(scene2)
    
    # Scene 3: CTA
    bg3 = ColorClip(size=(W, H), color=PURPLE, duration=4)
    txt3 = TextClip(font=FONT, text="Come and Play!", font_size=100, color=WHITE, duration=4)
    txt3 = txt3.with_position(('center', 500))
    sub3 = TextClip(font=FONT_MYANMAR if os.path.exists(FONT_MYANMAR) else FONT, 
                   text="လာရောက်ကစားလို့ရပါပြီ။", font_size=50, color=(255,215,0), duration=4)
    sub3 = sub3.with_position(('center', 700))
    tag3 = TextClip(font=FONT, text="📍 Yangon", font_size=35, color='#AAAAAA', duration=4)
    tag3 = tag3.with_position(('center', 900))
    scene3 = CompositeVideoClip([bg3, txt3, sub3, tag3], size=(W, H))
    scene3 = scene3.with_effects([vfx.FadeIn(0.5)])
    clips.append(scene3)
    
    # Concatenate scenes
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output, fps=FPS, codec='libx264', audio=False, logger=None)
    print(f"  ✅ {output}")
    return output


# ═══════════════════════════════════════════
# CLI 
# ═══════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PS VIBE Motion Graphics")
    sub = parser.add_subparsers(dest="command", required=True)
    
    pi = sub.add_parser("create-intro")
    pi.add_argument("-t", "--text", default="PS VIBE")
    pi.add_argument("-s", "--subtitle", default="Play The Game. Share The VIBE!")
    pi.add_argument("-o", "--output", default="/home/node/.local/share/psvibe_intro_animated.mp4")
    
    pl = sub.add_parser("create-lower-third")
    pl.add_argument("-t", "--text", default="Now Playing:")
    pl.add_argument("-v", "--value", default="God of War Ragnarök")
    pl.add_argument("-o", "--output", default="/home/node/.local/share/psvibe_lower_third.mp4")
    
    pp = sub.add_parser("create-package")
    pp.add_argument("-t", "--text", default="6 Hour Gaming")
    pp.add_argument("-p", "--price", default="25,000 Ks")
    pp.add_argument("-f", "--features", nargs="*")
    pp.add_argument("-o", "--output", default="/home/node/.local/share/psvibe_package.mp4")
    
    pg = sub.add_parser("create-game-showcase")
    pg.add_argument("-g", "--game", default="God of War Ragnarök")
    pg.add_argument("-c", "--console", default="PS5")
    pg.add_argument("-r", "--rating", default="⭐⭐⭐⭐⭐")
    pg.add_argument("-o", "--output", default="/home/node/.local/share/psvibe_game_showcase.mp4")
    
    p_promo = sub.add_parser("create-promo")
    p_promo.add_argument("-o", "--output", default="/home/node/.local/share/psvibe_promo.mp4")
    
    args = parser.parse_args()
    
    if args.command == "create-intro":
        create_intro(args.text, args.subtitle, args.output)
    elif args.command == "create-lower-third":
        create_lower_third(args.text, args.value, args.output)
    elif args.command == "create-package":
        create_package_card(args.text, args.price, args.features, args.output)
    elif args.command == "create-game-showcase":
        create_game_showcase(args.game, args.console, args.rating, args.output)
    elif args.command == "create-promo":
        create_promo_ad(args.output)
