#!/bin/zsh
# reel2 recreation: 10 frame-capped sections, purple design, ES VO + music bed.
set -e
cd "$(dirname "$0")"

SEGS=(
  "tts/seg_00_fit.wav" 8850
  "tts/seg_01_fit.wav" 13350
  "tts/seg_02_fit.wav" 16700
  "tts/seg_03.mp3"     22450
  "tts/seg_04_fit.wav" 27750
  "tts/seg_05_fit.wav" 30350
  "tts/seg_06_fit.wav" 36950
)

cat > filter_r2.txt <<'EOF'
[0:v]trim=0:8.767,setpts=PTS-STARTPTS,fps=30,format=yuv420p,trim=end_frame=263,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s1];
[7:v]fps=30,trim=0:4.44,setpts=PTS-STARTPTS[b2];
[1:v]trim=0:4.6,setpts=PTS-STARTPTS,scale=310:551[a2];
[b2][a2]overlay=205:520,fps=30,format=yuv420p,trim=end_frame=133,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s2];
[8:v]fps=30,trim=0:2.28,setpts=PTS-STARTPTS[b3];
[2:v]trim=0:2.4,setpts=PTS-STARTPTS,crop=720:1126:0:77,scale=600:938[c3];
[b3][c3]overlay=60:118,fps=30,format=yuv420p,trim=end_frame=68,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s3];
[23:v]trim=0:1.17,setpts=PTS-STARTPTS,fps=30,format=yuv420p,trim=end_frame=35,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s4];
[9:v]fps=30,trim=0:5.87,setpts=PTS-STARTPTS[b5a];
[3:v]trim=3.43:8.73,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.7[c5a];
[b5a][c5a]overlay=60:118,fps=30,format=yuv420p,trim=end_frame=176,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s5a];
[10:v]fps=30,trim=0:5.2,setpts=PTS-STARTPTS[b5b];
[4:v]trim=0:4.68,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.6[l5];
[5:v]trim=0:4.68,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.6[r5];
[b5b][l5]overlay=46:324[p5];
[p5][r5]overlay=374:324,fps=30,format=yuv420p,trim=end_frame=156,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s5b];
[24:v]trim=0:1.30,setpts=PTS-STARTPTS,fps=30,format=yuv420p,trim=end_frame=39,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s6a];
[25:v]trim=0:1.24,setpts=PTS-STARTPTS,fps=30,format=yuv420p,trim=end_frame=37,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s6b];
[11:v]fps=30,trim=0:6.67,setpts=PTS-STARTPTS[b7];
[6:v]trim=0:6.58,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.2[c7];
[b7][c7]overlay=68:278,fps=30,format=yuv420p,trim=end_frame=200,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s7];
[12:v]fps=30,crop=720:1280:0:'(ih-1280)*min(t/4.3,1)',trim=0:4.4,setpts=PTS-STARTPTS,format=yuv420p,trim=end_frame=132,setpts=PTS-STARTPTS,settb=1/30,setpts=N[s8];
[s1][s2][s3][s4][s5a][s5b][s6a][s6b][s7][s8]concat=n=10:v=1:a=0[vcat];
[vcat][13:v]overlay=0:0[vout];
[14:a]anull[unused];[unused]anullsink;
[15:a]atrim=0:41.42[bed];
EOF

i=16
n=0
vo_labels=""
idx=1
while (( idx < ${#SEGS[@]} )); do
  f=${SEGS[$idx]}; ms=${SEGS[$((idx+1))]}
  echo "[${i}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=${ms}|${ms}[vo${n}];" >> filter_r2.txt
  vo_labels="${vo_labels}[vo${n}]"
  i=$((i+1)); n=$((n+1)); idx=$((idx+2))
done
echo "[bed]${vo_labels}amix=inputs=$((n+1)):duration=first:normalize=0,alimiter=limit=0.97[aout]" >> filter_r2.txt

INPUTS=(
  -i clipA2.mp4 -i clipA2.mp4
  -i clipA2.mp4 -i clipCard.mp4
  -i clipL.mp4 -i clipR.mp4 -i clipT.mp4
  -loop 1 -t 4.60 -i bg.png
  -loop 1 -t 2.40 -i bg.png
  -loop 1 -t 6.00 -i bg.png
  -loop 1 -t 5.40 -i bg.png
  -loop 1 -t 6.90 -i bg.png
  -loop 1 -t 4.60 -i cta_tall.png
  -framerate 30 -i "overlay/%05d.png"
  -i source_audio.mp3 -i bed_r2.wav
)
idx=1
while (( idx < ${#SEGS[@]} )); do
  INPUTS+=(-i "${SEGS[$idx]}")
  idx=$((idx+2))
done
INPUTS+=(-f lavfi -t 1.5 -i "color=black:s=720x1280:r=30")
INPUTS+=(-f lavfi -t 1.5 -i "color=black:s=720x1280:r=30")
INPUTS+=(-f lavfi -t 1.5 -i "color=black:s=720x1280:r=30")

ffmpeg -y -hide_banner -loglevel warning "${INPUTS[@]}" \
  -filter_complex_script filter_r2.txt \
  -map "[vout]" -map "[aout]" \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -r 30 \
  -c:a aac -b:a 192k -t 41.30 \
  out_r2.mp4
echo "done: out_r2.mp4"
