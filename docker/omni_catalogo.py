#!/usr/bin/env python3
"""
omni_catalogo.py — gera o catálogo de vozes candidatas no modo DESIGN do OmniVoice.

Por que design e não clonagem de referência nativa:
clonagem cross-lingual preserva o timbre mas arrasta a PROSÓDIA da referência.
Clonar um locutor inglês pra falar português entrega vogais certas com melodia
de falante de inglês, que é exatamente o "esquisito" que o ouvido pega. No modo
design o modelo inventa a voz já dentro do idioma alvo, então a prosódia nasce
nativa.

MINA: voz de design NÃO é reprodutível. A mesma instrução gera uma voz diferente
a cada chamada. Por isso este script é one-shot de CURADORIA, não de produção:
o humano escolhe uma candidata, e o .wav vencedor vira o ref_audio fixo daquele
canal. Da escolha em diante tudo é clonagem daquele arquivo, nunca design de novo.

Uso:
  python3 omni_catalogo.py --text-file /data/pt.txt --lang Portuguese --out-dir /data/cat_pt

Env: OMNI_DEVICE=cpu|cuda:0 (default cpu)
"""
import argparse
import json
import os
import time

# MINA: `instruct` NÃO aceita texto livre. É vocabulário fechado de 23 itens,
# separados por vírgula+espaço, e o modelo levanta ValueError em qualquer palavra
# fora da lista. Os únicos eixos disponíveis são objetivos:
#   gênero: male, female
#   idade:  child, teenager, young adult, middle-aged, elderly
#   altura: very low pitch, low pitch, moderate pitch, high pitch, very high pitch
#   sotaque: american/australian/british/canadian/chinese/indian/japanese/korean/
#            portuguese/russian accent
#   outro:  whisper
# NÃO existe controle de emoção, ritmo ou interpretação ("calmo", "solene",
# "autoritário" são todos rejeitados). Interpretação só se consegue fora do modelo,
# via engenharia de pausa e velocidade.
VOZES = [
    ("01_meia_idade_grave",   "male, middle-aged, low pitch"),
    ("02_meia_idade_medio",   "male, middle-aged, moderate pitch"),
    ("03_idoso_grave",        "male, elderly, low pitch"),
    ("04_idoso_medio",        "male, elderly, moderate pitch"),
    ("05_meia_idade_muito_grave", "male, middle-aged, very low pitch"),
    ("06_jovem_medio",        "male, young adult, moderate pitch"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", dest="text_file", required=True)
    ap.add_argument("--lang", required=True, help='"Portuguese" | "Spanish" | "English"')
    ap.add_argument("--out-dir", dest="out_dir", required=True)
    ap.add_argument("--speed", type=float, default=0.95)
    args = ap.parse_args()

    texto = open(args.text_file, encoding="utf-8").read().strip()
    os.makedirs(args.out_dir, exist_ok=True)

    device = os.environ.get("OMNI_DEVICE", "cpu")
    print(f"[cat] carregando modelo em device={device} ...", flush=True)
    t0 = time.time()
    from omnivoice import OmniVoice
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device)
    print(f"[cat] modelo carregado em {time.time()-t0:.1f}s", flush=True)

    import soundfile as sf
    sr = getattr(model, "sampling_rate", 24000)
    manifesto = {"lang": args.lang, "sr": sr, "texto": texto, "vozes": []}

    for slug, instruct in VOZES:
        print(f"[cat] gerando {slug} ...", flush=True)
        t = time.time()
        audios = model.generate(text=texto, language=args.lang,
                                instruct=instruct, speed=args.speed)
        gen = time.time() - t
        arr = audios[0] if isinstance(audios, (list, tuple)) else audios
        out = os.path.join(args.out_dir, f"{slug}.wav")
        sf.write(out, arr, sr)
        dur = len(arr) / float(sr)
        print(f"[cat] {slug}: audio={dur:.1f}s gen={gen:.1f}s RTF={gen/dur:.2f}", flush=True)
        manifesto["vozes"].append({"slug": slug, "instruct": instruct,
                                   "audio_s": round(dur, 1), "gen_s": round(gen, 1)})

    with open(os.path.join(args.out_dir, "manifesto.json"), "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)
    print("[cat] CATALOGO PRONTO", flush=True)


if __name__ == "__main__":
    main()
