"""Assemble the remake: per-scene segments (exact frame caps) -> concat ->
type overlay + global vignette -> original audio.

Needs: storyboard_merged.json, gen/bIDX.mp4 for every broll idx, type/%05d.png,
source.mp4 (audio). Scenes with kind texto/preto render as black.
Clips shorter than the scene loop in ping-pong; longer clips are trimmed.
"""
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
SEG = ROOT / "seg"
SEG.mkdir(exist_ok=True)
FPS = 30
DUR_TOTAL = 275.033

scenes = json.load(open(ROOT / "storyboard_merged.json"))
# broll clips are named gen/bIDX.mp4 where IDX = index of the scene in
# storyboard_merged (same as broll_list/gen_queue 'idx')
for i, m in enumerate(scenes):
    if m["kind"] == "broll":
        m["_b"] = i

# frame-grid boundaries, continuous
bounds = [0]
for s in scenes:
    f = round(float(s["end_s"]) * FPS)
    bounds.append(max(f, bounds[-1] + 1))
bounds[-1] = round(DUR_TOTAL * FPS)  # 8251
ENC = ["-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
       "-pix_fmt", "yuv420p", "-r", "30", "-an"]


def dur_of(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


concat_list = []
for i, s in enumerate(scenes):
    nf = bounds[i + 1] - bounds[i]
    out = SEG / f"{i:03d}.mp4"
    concat_list.append(out)
    if out.exists():
        continue
    need = nf / FPS
    if s["kind"] != "broll":
        bg = "0xEFE8DC" if i in (114,) else "black"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                        "-t", f"{need + 0.2:.3f}",
                        "-i", f"color={bg}:s=720x1280:r=30",
                        "-vf", f"trim=end_frame={nf},setpts=PTS-STARTPTS",
                        *ENC, str(out)], check=True)
        continue
    clip = ROOT / "gen" / f"b{s['_b']:03d}.mp4"
    if not clip.exists():
        raise SystemExit(f"FALTA {clip} (cena {i}, broll idx {s['_b']})")
    cd = dur_of(clip)
    if cd + 0.05 >= need:
        vf = f"fps=30,trim=end_frame={nf},setpts=PTS-STARTPTS,scale=720:1280"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(clip),
                        "-vf", vf, *ENC, str(out)], check=True)
    else:
        # ping-pong loop to cover
        reps = math.ceil(need / cd / 2) + 1
        fc = (f"[0:v]fps=30,scale=720:1280,split=2[a][b];"
              f"[b]reverse[r];[a][r]concat=n=2:v=1[pp];"
              f"[pp]loop=loop={reps}:size={int(cd * 2 * 30)}:start=0,"
              f"trim=end_frame={nf},setpts=PTS-STARTPTS[v]")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(clip),
                        "-filter_complex", fc, "-map", "[v]", *ENC, str(out)],
                       check=True)
    print(f"seg {i:03d} ok ({s['kind']}, {nf}f)")

with open(ROOT / "list.txt", "w") as f:
    for p in concat_list:
        f.write(f"file '{p}'\n")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                "-i", str(ROOT / "list.txt"), "-c", "copy",
                str(ROOT / "base.mp4")], check=True)

# final: type overlay + soft vignette + original audio
subprocess.run([
    "ffmpeg", "-y", "-v", "warning",
    "-i", str(ROOT / "base.mp4"),
    "-framerate", "30", "-i", str(ROOT / "type" / "%05d.png"),
    "-i", str(ROOT / "source.mp4"),
    "-filter_complex",
    "[0:v][1:v]overlay=0:0[vt];[vt]vignette=PI/5:mode=forward[vout]",
    "-map", "[vout]", "-map", "2:a",
    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-t", f"{DUR_TOTAL:.3f}",
    str(ROOT / "out_remake.mp4")], check=True)
print("out_remake.mp4 ok")
