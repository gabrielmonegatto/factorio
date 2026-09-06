#!/usr/bin/env python3
"""
bakeoff_vozes.py — páreo de motores de TTS pra voz PT-BR (rede Spurgeon BR).

O Kokoro PT foi reprovado de ouvido pelo Gabriel (05/09: "todas horríveis"). Este
script gera o MESMO trecho traduzido em motores open source com licença comercial
limpa, na CPU da VPS (lento, mas custa zero), pra ele escolher de ouvido:

  --motor qwen        Qwen3-TTS 1.7B VoiceDesign (Apache 2.0, jan/2026): voz
                      desenhada por descrição LIVRE em texto. É o que o OmniVoice
                      não tem (lá são 23 atributos fechados). 3 descrições.
  --motor chatterbox  Chatterbox Multilingual (MIT, Resemble): voz padrão em pt.

Saída: <out>/<motor>_<nome>.wav (+ .mp3 se houver ffmpeg). Texto é cortado em
frases e emendado com silêncio, a mesma engenharia de pausa da casa.

MINA (voz desenhada): o resultado NÃO é reprodutível entre chamadas. Se uma
candidata vencer, o .wav dela vira o `ref_audio` FIXO do canal e daí em diante é
clonagem, nunca design de novo (mesma lei do omni_catalogo.py).
"""
import argparse
import os
import re
import subprocess
import time

import numpy as np
import soundfile as sf

DESIGNS_QWEN = [
    ("pregador_idoso", "Voz masculina idosa, grave e pausada, timbre quente e rouco de "
                       "pregador experiente, solene e acolhedora, ritmo lento de púlpito, "
                       "português do Brasil."),
    ("narrador_meia_idade", "Voz masculina de meia-idade, grave, calorosa e firme, dicção "
                            "clara de narrador de audiolivro, tom solene e sereno, "
                            "português do Brasil."),
    ("baritono_jovem", "Voz masculina jovem adulta, barítono encorpado, energia contida, "
                       "articulação nítida, estilo narração de documentário, português "
                       "do Brasil."),
]
PAUSA_S = 0.7


def frases(texto):
    partes = re.split(r"(?<=[.!?])\s+", texto.strip())
    return [p.strip() for p in partes if p.strip()]


def emendar(pedacos, sr):
    sil = np.zeros(int(PAUSA_S * sr), dtype=np.float32)
    out = []
    for i, p in enumerate(pedacos):
        p = np.asarray(p, dtype=np.float32).squeeze()
        out.append(p)
        if i < len(pedacos) - 1:
            out.append(sil)
    return np.concatenate(out)


def salvar(nome, audio, sr, out_dir):
    wav = os.path.join(out_dir, nome + ".wav")
    sf.write(wav, audio, sr)
    mp3 = wav[:-4] + ".mp3"
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1",
                        "-b:a", "96k", mp3], check=True)
    except Exception:
        pass
    print(f"✅ {nome}: {len(audio)/sr:.0f}s de áudio -> {wav}", flush=True)


def motor_qwen(texto, out_dir, lang):
    import torch
    from qwen_tts import Qwen3TTSModel
    t0 = time.time()
    model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
                                          device_map="cpu", dtype=torch.float32)
    print(f"[qwen] modelo carregado em {time.time()-t0:.0f}s", flush=True)
    fs = frases(texto)
    for nome, instruct in DESIGNS_QWEN:
        # 1ª frase define a voz; as demais clonam dela pra manter o MESMO timbre
        # ao longo do trecho (design a cada frase daria um locutor por frase).
        t1 = time.time()
        wavs, sr = model.generate_voice_design(text=fs[0], language=lang, instruct=instruct)
        semente = np.asarray(wavs[0], dtype=np.float32).squeeze()
        pedacos = [semente]
        for f in fs[1:]:
            w, sr = model.generate_voice_clone(text=f, language=lang,
                                               ref_audio=(semente, sr), ref_text=fs[0])
            pedacos.append(w[0])
        audio = emendar(pedacos, sr)
        print(f"[qwen] {nome}: RTF {(time.time()-t1)/(len(audio)/sr):.1f}", flush=True)
        salvar(f"qwen_{nome}", audio, sr, out_dir)


def motor_chatterbox(texto, out_dir, lang_id="pt"):
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    t0 = time.time()
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    print(f"[chatterbox] modelo carregado em {time.time()-t0:.0f}s", flush=True)
    t1 = time.time()
    pedacos = [model.generate(f, language_id=lang_id).squeeze().cpu().numpy() for f in frases(texto)]
    audio = emendar(pedacos, model.sr)
    print(f"[chatterbox] RTF {(time.time()-t1)/(len(audio)/model.sr):.1f}", flush=True)
    salvar("chatterbox_padrao", audio, model.sr, out_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", choices=["qwen", "chatterbox"], required=True)
    ap.add_argument("--text-file", dest="text_file", required=True)
    ap.add_argument("--out-dir", dest="out_dir", default="/data/out")
    ap.add_argument("--lang", default="Portuguese")
    a = ap.parse_args()
    texto = open(a.text_file, encoding="utf-8").read()
    os.makedirs(a.out_dir, exist_ok=True)
    if a.motor == "qwen":
        motor_qwen(texto, a.out_dir, a.lang)
    else:
        motor_chatterbox(texto, a.out_dir)


if __name__ == "__main__":
    main()
