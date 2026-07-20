#!/usr/bin/env python3
"""
subtitle_ass.py — Gera legenda .ass IDÊNTICA à do SubtitleLayer do Remotion.

Replica FIELMENTE:
  - a lógica de segmentação (buildCues): máx 2 linhas, ~42 chars, glue words, quebra em pontuação
  - o estilo visual: Georgia bold 48px, branco, MAIÚSCULAS, centralizado a 6% do rodapé, sombra escura
  - o timing: cada cue aparece do seu start até end+500ms (ou até o próximo cue começar)

Assim o corpo do sermão renderizado no ffmpeg fica visualmente igual ao Remotion.

Uso: python subtitle_ass.py --transcript public/storage/sermons/0001/transcript.json --out sermon_0001.ass
"""
import json
import argparse
import re

MAX_CHARS_PER_LINE = 42
MAX_LINES = 2
GLUE_WORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for",
    "by", "with", "from", "and", "but", "or", "nor", "as",
    "is", "it", "its", "my", "his", "her", "our", "your",
    "their", "this", "that", "no", "not", "so", "if", "be",
}


def ends_with_punctuation(t):
    return bool(re.search(r"[.,;:!?…—\-]$", t))


def ends_with_sentence_end(t):
    return bool(re.search(r"[.!?…]$", t))


def build_cues(words):
    """Porta fiel do buildCues() do SubtitleLayer.tsx."""
    cues = []
    current_line = ""
    lines = []
    cue_words = []

    def flush_cue():
        nonlocal current_line, lines, cue_words
        if lines or current_line:
            if current_line:
                lines.append(current_line.strip())
            if cue_words:
                cues.append({
                    "text": "\n".join(lines),
                    "start": cue_words[0]["start"],
                    "end": cue_words[-1]["end"],
                })
            lines = []
            current_line = ""
            cue_words = []

    def flush_line():
        nonlocal current_line, lines
        if current_line:
            lines.append(current_line.strip())
            current_line = ""

    for word in words:
        wt = word["text"]
        test_line = wt if not current_line else current_line + " " + wt

        if len(test_line) > MAX_CHARS_PER_LINE and current_line:
            last_space = current_line.rfind(" ")
            handled = False
            if last_space > 0:
                last_word = re.sub(r"[.,;:!?]", "", current_line[last_space + 1:].lower())
                if last_word in GLUE_WORDS:
                    before_glue = current_line[:last_space]
                    glue_word = current_line[last_space + 1:]
                    current_line = before_glue
                    flush_line()
                    current_line = glue_word + " " + wt
                    cue_words.append(word)
                    if len(lines) >= MAX_LINES:
                        flush_cue()
                    handled = True
            if not handled:
                flush_line()
                if len(lines) >= MAX_LINES:
                    flush_cue()
                current_line = wt
                cue_words.append(word)
        else:
            current_line = test_line
            cue_words.append(word)

        if ends_with_sentence_end(wt):
            flush_cue()
        elif ends_with_punctuation(wt) and len(lines) >= 1:
            flush_cue()

    flush_cue()
    return cues


def ms_to_ass(ms):
    """ms -> H:MM:SS.cc (centésimos), formato do .ass."""
    cs = int(round(ms / 10.0))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# Estilo replicando o CSS do SubtitleLayer (PlayRes 1920x1080).
# ASS cor = &HAABBGGRR. Georgia bold 48, branco, MAIÚSCULAS, alinhamento 2 (base-centro),
# MarginV ~= 6% de 1080 ~= 65. Outline+Shadow escuros p/ imitar o textShadow.
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sermon, Georgia, 48, &H00FFFFFF, &H00FFFFFF, &HE6000000, &HCC000000, -1, 0, 0, 0, 100, 100, 1, 0, 1, 2, 3, 2, 200, 200, 65, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = json.load(open(args.transcript, encoding="utf-8"))
    words = data.get("words", [])
    cues = build_cues(words)

    lines_out = [ASS_HEADER]
    for i, cue in enumerate(cues):
        start = cue["start"]
        # aparece até end+500ms, mas nunca depois do próximo cue começar
        end = cue["end"] + 500
        if i + 1 < len(cues):
            end = min(end, cues[i + 1]["start"])
        if end <= start:
            end = start + 200
        # limpa pontuação/espaço órfão no início de cada linha (bug ",THEREFORE")
        clean_lines = [re.sub(r"^[\s.,;:!?…—\-]+", "", ln) for ln in cue["text"].split("\n")]
        text = "\n".join(clean_lines).upper().replace("\n", "\\N")
        lines_out.append(f"Dialogue: 0,{ms_to_ass(start)},{ms_to_ass(end)},Sermon,,0,0,0,,{text}")

    open(args.out, "w", encoding="utf-8").write("\n".join(lines_out) + "\n")
    print(f"✅ {len(cues)} legendas -> {args.out}")


if __name__ == "__main__":
    main()
