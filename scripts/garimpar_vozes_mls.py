#!/usr/bin/env python3
"""
garimpar_vozes_mls.py — garimpo de vozes candidatas no MLS (Multilingual LibriSpeech).

O MLS é o LibriVox já cortado em trechos de 10 a 20s, com id de falante e
licença CC-BY 4.0 (gravação dedicada ao domínio público pelos leitores). Serve
como fonte de REFERÊNCIA pra clonagem zero-shot (5 a 10s bastam) e, pros leitores
com horas, pra fine-tune. Pedido do Gabriel (06/09): "baixa numa pasta que eu vou
abrindo e te falando quais prestam".

Pra cada idioma: percorre o split de treino em streaming (sem baixar o dataset
inteiro, que passa de 30GB por língua) e guarda N trechos de cada um dos
primeiros K falantes distintos, com duração entre MIN_S e MAX_S. Saída:

    <out>/<idioma>/<speaker_id>/<speaker_id>_<n>.mp3
    <out>/<idioma>/INDICE.md   (falante, nº de trechos, duração, transcrição)

O speaker_id é a chave do catálogo: quem o Gabriel aprovar entra em
_globalassets/vozes/<id>/ com origem "mls:<idioma>:<speaker_id>" e licença
CC-BY 4.0 anotadas no meta.json.

Uso (dentro do container python com datasets+soundfile+ffmpeg):
  python3 garimpar_vozes_mls.py --idiomas portuguese,spanish,english \
      --falantes 40 --por-falante 2 --out /data/vozes_candidatas
"""
import argparse
import io
import os
import subprocess

import soundfile as sf

MIN_S, MAX_S = 8.0, 20.0


def garimpar(idioma, falantes, por_falante, out):
    from datasets import load_dataset
    pasta = os.path.join(out, idioma)
    os.makedirs(pasta, exist_ok=True)
    from datasets import Audio
    # MINA: o MLS do Hugging Face NÃO tem inglês (só dutch/french/german/italian/
    # polish/portuguese/spanish). Inglês vem do LibriTTS-R (mesma origem LibriVox,
    # CC BY 4.0, restaurado), com o mesmo grão por falante.
    if idioma == "english":
        ds = load_dataset("mythicinfinity/libritts_r", "clean", split="train.clean.100",
                          streaming=True)
        ds = ds.rename_column("text_normalized", "transcript")
    else:
        ds = load_dataset("facebook/multilingual_librispeech", idioma, split="train",
                          streaming=True)
    # decode=False: o decodificador padrão do `datasets` puxa torch/torchcodec
    # (falhou na 1ª rodada: "No module named torch"). Os bytes lidos direto pelo
    # soundfile dispensam torch inteiro.
    ds = ds.cast_column("audio", Audio(decode=False))
    visto = {}
    linhas = []
    for ex in ds:
        spk = str(ex["speaker_id"])
        if len(visto) >= falantes and spk not in visto:
            if all(len(v) >= por_falante for v in visto.values()):
                break
            continue
        if len(visto.get(spk, [])) >= por_falante:
            continue
        try:
            arr, sr = sf.read(io.BytesIO(ex["audio"]["bytes"]))
        except Exception as e:
            print(f"  (pulei um trecho ilegível: {e})", flush=True)
            continue
        a = {"array": arr, "sampling_rate": sr}
        dur = len(arr) / sr
        if not (MIN_S <= dur <= MAX_S):
            continue
        n = len(visto.get(spk, [])) + 1
        d = os.path.join(pasta, spk)
        os.makedirs(d, exist_ok=True)
        wav = os.path.join(d, f"{spk}_{n}.wav")
        sf.write(wav, a["array"], a["sampling_rate"])
        mp3 = wav[:-4] + ".mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1",
                        "-b:a", "96k", mp3], check=True)
        os.remove(wav)
        visto.setdefault(spk, []).append(mp3)
        linhas.append(f"| {spk} | {n} | {dur:.0f}s | {ex['transcript'][:90]} |")
        print(f"  {idioma} · falante {spk} · trecho {n} · {dur:.0f}s  ({len(visto)}/{falantes} falantes)", flush=True)
    with open(os.path.join(pasta, "INDICE.md"), "w", encoding="utf-8") as f:
        f.write(f"# Candidatos MLS · {idioma} · {len(visto)} falantes\n\n"
                "Marque aqui os que prestam. Chave = speaker_id.\n\n"
                "| speaker_id | trecho | dur | começo do texto |\n|---|---|---|---|\n")
        f.write("\n".join(linhas) + "\n")
    print(f"✅ {idioma}: {len(visto)} falantes em {pasta}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idiomas", default="portuguese,spanish,english")
    ap.add_argument("--falantes", type=int, default=40)
    ap.add_argument("--por-falante", dest="por_falante", type=int, default=2)
    ap.add_argument("--out", default="/data/vozes_candidatas")
    a = ap.parse_args()
    for idioma in a.idiomas.split(","):
        garimpar(idioma.strip(), a.falantes, a.por_falante, a.out)


if __name__ == "__main__":
    main()
