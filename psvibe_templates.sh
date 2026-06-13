#!/bin/bash
# PS VIBE Template Generator - FFmpeg-based (reliable)
FFMPEG=/home/node/.local/bin/ffmpeg
FONT=/home/node/.local/share/fonts/psvibe-font.ttf
FONT_M=/home/node/.local/share/fonts/NotoSansMyanmar_Google-Bold.ttf
OUTDIR=/home/node/.local/share

# Create animated intro
$FFMPEG -y -f lavfi -i "color=c=#6414E6:s=1080x1920:d=4:r=30" \
  -vf "drawtext=text='PS VIBE':fontfile=$FONT:fontsize=140:fontcolor=white:borderw=3:bordercolor=#FFD700:x=(w-text_w)/2:y=400+100*t:enable='between(t,0,1.5)',drawtext=text='Play The Game. Share The VIBE!':fontfile=$FONT:fontsize=40:fontcolor=#FFD700:x=(w-text_w)/2:y=650:enable='gte(t,1)',fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5" \
  -c:v libx264 -preset medium -crf 22 "$OUTDIR/psvibe_intro_animated.mp4" 2>&1 | tail -3

# Create lower third
$FFMPEG -y -f lavfi -i "color=c=#00000000:s=1080x1920:d=5:r=30" \
  -vf "color=c=#6414E6:s=750x100:d=5,format=rgba,drawbox=x=0:y=0:w=10:h=100:c=#FFD700@1" \
  -c:v libx264 -preset medium -crf 22 "$OUTDIR/psvibe_lower_test.mp4" 2>&1 | tail -3

# Create package card (static frame with text)
$FFMPEG -y -f lavfi -i "color=c=#1a0a2e:s=1080x1920:d=5:r=30" \
  -vf "drawtext=text='6 Hour Gaming':fontfile=$FONT:fontsize=90:fontcolor=white:borderw=2:bordercolor=#FFD700:x=(w-text_w)/2:y=300,drawtext=text='25,000 Ks':fontfile=$FONT:fontsize=120:fontcolor=#FFD700:borderw=2:bordercolor=black:x=(w-text_w)/2:y=500,drawtext=text='▸ PS5 Console':fontfile=$FONT:fontsize=38:fontcolor=white:x=380:y=730,drawtext=text='▸ Free Drinks':fontfile=$FONT:fontsize=38:fontcolor=white:x=380:y=810,drawtext=text='▸ Snacks':fontfile=$FONT:fontsize=38:fontcolor=white:x=380:y=890,drawtext=text='Play The Game. Share The VIBE!':fontfile=$FONT:fontsize=28:fontcolor=#FFD700:x=(w-text_w)/2:y=1300,fade=t=in:st=0:d=0.5" \
  -c:v libx264 -preset medium -crf 22 "$OUTDIR/psvibe_package.mp4" 2>&1 | tail -3

echo "✅ Templates generated in $OUTDIR/"
ls -lh "$OUTDIR/"psvibe_*.mp4 2>/dev/null
