"""V4 music bed: original audio on the viral-clip windows, a NEW similar
phonk track (music_c) under our narration from 12.05s on.

Timeline (44.1k stereo, 43.14s):
  0.00-6.40   original (clip #1 music + hook)
  6.40-7.65   demucs instrumental bridge (1.25s, under VO)
  7.65-12.05  original (clip #2 music + hook)
  12.05-end   music_c, loudness-matched to the original music, equal-power
              crossfade in (0.4s), fade-out at the tail
"""
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent
SR = 44100
END = 43.14


def load(p):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "2",
         "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def rms(a):
    return float(np.sqrt(np.mean(a ** 2)))


src = load(ROOT / "source_audio.mp3")
inst = load(ROOT / "sep_ft" / "htdemucs_ft" / "source_audio" / "no_vocals.wav")
mc = load(ROOT / "music_c.mp3")

N = int(END * SR)
bed = np.zeros((N, 2), dtype=np.float32)

s640, s765, s1205 = int(6.40 * SR), int(7.65 * SR), int(12.05 * SR)
bed[:s640] = src[:s640]
bed[s640:s765] = inst[s640:s765]
bed[s765:s1205] = src[s765:s1205]
# smooth the two inner seams (30ms linear crossfades)
xf = int(0.03 * SR)
for (edge, a_sig, b_sig) in ((s640, src, inst), (s765, inst, src)):
    w = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
    bed[edge:edge + xf] = a_sig[edge:edge + xf] * (1 - w) + b_sig[edge:edge + xf] * w

# --- new track: pick the steadiest 31.2s window of music_c
need = N - s1205
hop = int(0.5 * SR)
best_off, best_var = 0, 1e9
mono = mc.mean(axis=1)
env_hop = 2048
env = np.array([np.abs(mono[i:i + env_hop]).mean()
                for i in range(0, len(mono) - env_hop, env_hop)])
env_sr = SR / env_hop
for off_s in np.arange(1.0, (len(mc) - need) / SR - 0.1, 0.5):
    e = env[int(off_s * env_sr):int((off_s + need / SR) * env_sr)]
    v = np.std(e) / (np.mean(e) + 1e-9)
    if v < best_var:
        best_var, best_off = v, off_s
seg = mc[int(best_off * SR):int(best_off * SR) + need].copy()

# loudness-match to the original full-quality music, slightly under for VO
target = rms(src[int(8.0 * SR):int(12.0 * SR)]) * 0.85
seg *= target / (rms(seg) + 1e-9)

# equal-power crossfade original -> new track at 12.05 (0.4s)
xf2 = int(0.40 * SR)
w = np.linspace(0, np.pi / 2, xf2, dtype=np.float32)[:, None]
bed[s1205:s1205 + xf2] = (src[s1205:s1205 + xf2] * np.cos(w) ** 2
                          + seg[:xf2] * np.sin(w) ** 2)
bed[s1205 + xf2:] = seg[xf2:]

# tail fade (0.5s)
fo = int(0.5 * SR)
bed[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]

peak = float(np.abs(bed).max())
if peak > 0.99:
    bed *= 0.99 / peak
subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR),
     "-i", "-", str(ROOT / "bed3.wav")],
    input=bed.astype(np.float32).tobytes(), check=True)
print(f"bed3.wav ok — music_c window @{best_off:.1f}s, target rms {target:.3f}, peak {peak:.2f}")
