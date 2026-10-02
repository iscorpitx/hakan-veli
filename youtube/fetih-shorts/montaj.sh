#!/usr/bin/env bash
# Kullanım: ./montaj.sh [ses.mp3]
# 1.jpg..N.jpg resimlerini yakınlaştırma/kaydırma efektiyle 1080x1920 Shorts videosuna çevirir.
# Ses verilirse sahne süreleri sese göre eşit bölünür, verilmezse sahne başı 7 sn.
set -euo pipefail
FPS=30; W=1080; H=1920; FADE=0.6
imgs=( $(ls [0-9]*.jpg | sort -n) ); N=${#imgs[@]}
VOICE=${1:-}
if [[ -n "$VOICE" ]]; then
  TOTAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VOICE")
  D=$(awk -v t="$TOTAL" -v n="$N" -v f="$FADE" 'BEGIN{printf "%.3f",(t+(n-1)*f)/n}')
else D=7; fi
FR=$(awk -v d="$D" -v f="$FPS" 'BEGIN{printf "%d",d*f}')
inputs=(); filt=""
for i in "${!imgs[@]}"; do
  inputs+=(-loop 1 -framerate $FPS -t "$D" -i "${imgs[$i]}")
  case $((i%4)) in
    0) z="min(zoom+0.0008,1.25)"; x="iw/2-(iw/zoom/2)"; y="ih/2-(ih/zoom/2)";;   # içeri yakınlaş
    1) z="if(eq(on,0),1.25,max(zoom-0.0008,1.0))"; x="iw/2-(iw/zoom/2)"; y="ih/2-(ih/zoom/2)";; # dışarı
    2) z="1.2"; x="(iw-iw/zoom)*on/$FR"; y="ih/2-(ih/zoom/2)";;                    # sola kaydır
    3) z="1.2"; x="(iw-iw/zoom)*(1-on/$FR)"; y="ih/2-(ih/zoom/2)";;                # sağa kaydır
  esac
  filt+="[$i:v]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,zoompan=z='$z':x='$x':y='$y':d=1:s=${W}x${H}:fps=$FPS,setsar=1,format=yuv420p[v$i];"
done
prev="v0"; off=0
for ((i=1;i<N;i++)); do
  off=$(awk -v o="$off" -v d="$D" -v f="$FADE" 'BEGIN{printf "%.3f",o+d-f}')
  filt+="[$prev][v$i]xfade=transition=fade:duration=$FADE:offset=$off[x$i];"; prev="x$i"
done
filt+="[$prev]vignette=PI/5[out]"
if [[ -n "$VOICE" ]]; then
  ffmpeg -y -v error "${inputs[@]}" -i "$VOICE" -filter_complex "$filt" -map "[out]" -map "$N:a" -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k -shortest shorts.mp4
else
  ffmpeg -y -v error "${inputs[@]}" -filter_complex "$filt" -map "[out]" -c:v libx264 -preset medium -crf 20 shorts.mp4
fi
echo "Hazır: shorts.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 shorts.mp4) sn)"
