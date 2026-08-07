"""Generate Spanish VO segments with ElevenLabs with-timestamps.

Each segment has a start time (aligned to the original video sections) and a
max_end. If the generated audio is longer than the window, we compute an
atempo factor (capped at 1.18) and scale the word timestamps accordingly.

Outputs:
  tts/seg_NN.mp3           raw TTS audio
  tts/seg_NN_fit.wav       tempo-adjusted 44.1k stereo wav (only if needed)
  tts/plan.json            [{idx, start, max_end, text, dur_raw, atempo,
                             dur_final, words: [{w, t0, t1}] (absolute video time)}]
"""
import base64
import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).parent
OUT = ROOT / "tts"
OUT.mkdir(exist_ok=True)

KEY = None
for line in (Path("/Volumes/KINGSTON/claude/tools/video-use/.env")).read_text().splitlines():
    if line.startswith("ELEVENLABS_API_KEY="):
        KEY = line.split("=", 1)[1].strip().strip('"')
assert KEY

VOICE = "sKgg4MPUDBy69X7iv3fA"  # Alejandro Duran - Warm, Deep and Hoarse
MODEL = "eleven_multilingual_v2"

SEGMENTS = [
    # (start, max_end, text)
    (8.85, 12.95, "Esto fue un intento de capturar tu atención, y logró 2,9 millones de vistas."),
    (13.35, 16.25, "No fue solo el mensaje: fue la forma de entregarlo."),
    (16.70, 21.95, "En vez de explicar la idea con palabras, el creador la convierte en una demostración visual en tiempo real."),
    (22.45, 27.15, "La gente se queda hasta el final, porque solo así entiende la comparación."),
    (27.75, 30.10, "El algoritmo no impulsa contenido al azar."),
    (30.35, 36.60, "Impulsa contenido que no solo entrega un mensaje: lo revela con un proceso visual que te engancha hasta el final."),
    (36.95, 41.05, "Comenta \"Formatos\" y te enviamos nuestro pack de 50 ganchos virales para cualquier nicho."),
]


def dur_of(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def words_from_alignment(text, alignment):
    chars = alignment["characters"]
    starts = alignment["character_start_times_seconds"]
    ends = alignment["character_end_times_seconds"]
    words, cur, t0, t1 = [], "", None, None
    for c, s, e in zip(chars, starts, ends):
        if c.isspace():
            if cur:
                words.append({"w": cur, "t0": t0, "t1": t1})
                cur, t0 = "", None
        else:
            if not cur:
                t0 = s
            cur += c
            t1 = e
    if cur:
        words.append({"w": cur, "t0": t0, "t1": t1})
    return words


plan = []
prev_text = None
for i, (start, max_end, text) in enumerate(SEGMENTS):
    raw = OUT / f"seg_{i:02d}.mp3"
    aln_path = OUT / f"seg_{i:02d}_alignment.json"
    if not raw.exists() or not aln_path.exists():
        body = {
            "text": text,
            "model_id": MODEL,
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8,
                               "style": 0.25, "use_speaker_boost": True},
        }
        if prev_text:
            body["previous_text"] = prev_text
        if i + 1 < len(SEGMENTS):
            body["next_text"] = SEGMENTS[i + 1][2]
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": KEY, "Content-Type": "application/json"},
            json=body, timeout=120)
        r.raise_for_status()
        d = r.json()
        raw.write_bytes(base64.b64decode(d["audio_base64"]))
        aln_path.write_text(json.dumps(d["alignment"]))
    prev_text = text

    alignment = json.loads(aln_path.read_text())
    words = words_from_alignment(text, alignment)
    dur_raw = dur_of(raw)
    window = max_end - start
    atempo = 1.0
    fit = raw
    if dur_raw > window:
        atempo = min(dur_raw / window, 1.18)
        fit = OUT / f"seg_{i:02d}_fit.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(raw),
             "-filter:a", f"atempo={atempo:.4f}",
             "-ar", "44100", "-ac", "2", str(fit)], check=True)
    dur_final = dur_of(fit)
    abs_words = [{"w": w["w"],
                  "t0": start + w["t0"] / atempo,
                  "t1": start + w["t1"] / atempo} for w in words]
    plan.append({"idx": i, "start": start, "max_end": max_end, "text": text,
                 "file": str(fit), "dur_raw": round(dur_raw, 2),
                 "atempo": round(atempo, 4), "dur_final": round(dur_final, 2),
                 "overflow": round(start + dur_final - max_end, 2),
                 "words": abs_words})
    print(f"S{i}: raw={dur_raw:.2f}s window={window:.2f}s atempo={atempo:.3f} "
          f"final={dur_final:.2f}s overflow={start + dur_final - max_end:+.2f}s")

(OUT / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
print("wrote", OUT / "plan.json")
