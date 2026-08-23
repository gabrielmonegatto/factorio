"""
asr_whisper.py — transcrição palavra a palavra na CPU da fábrica (container factorio-asr).

## Por que local e não API

A esteira narra o texto com o Kokoro e depois precisa saber QUANDO cada palavra
foi dita, porque a legenda destaca palavra por palavra. Medido em 22/08 sobre o
mesmo sermão de 33min, comparando sempre contra o TEXTO FONTE que mandamos
narrar (a única verdade disponível):

  motor                  custo        tempo    fidelidade   tempo fora de ordem
  AssemblyAI             US$ 0,15/h   minutos     99,2%            0
  Groq whisper-turbo     US$ 0,04/h        3s     98,9%           64
  small.en aqui          grátis          284s     98,8%            0
  tiny.en aqui           grátis           84s     98,1%            0

`small.en` empata com a API paga e ainda devolve o timing em ordem, coisa que o
Whisper da Groq não faz (~1% das palavras começam antes da anterior). Sendo
grátis, não há motivo pra mandar 53 horas de áudio pra fora.

## O teto que ainda dá pra furar

Fidelidade 98,8% significa que ~1% das palavras da legenda não são as que foram
faladas. Isso é bobagem da ASR ADIVINHANDO um texto que nós já temos. O caminho
de 100% é ALINHAMENTO FORÇADO (torchaudio.forced_align), que recebe o texto
certo e só procura os tempos. Fica anotado como melhoria; não é bloqueio.

Uso (dentro do container):
  python3 asr_whisper.py --audio /data/s.mp3 --out /data/words.json [--modelo small.en]
"""
import argparse
import json
import os
import time

from faster_whisper import WhisperModel


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audio", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--modelo", default=os.environ.get("ASR_MODELO", "small.en"))
    p.add_argument("--idioma", default="en")
    p.add_argument("--threads", type=int, default=os.cpu_count() or 8)
    args = p.parse_args()

    m = WhisperModel(args.modelo, device="cpu", compute_type="int8",
                     cpu_threads=args.threads, download_root="/cache")

    t0 = time.time()
    # beam_size=1 de propósito: o áudio é TTS limpo, sem ruído nem sotaque, e
    # busca em feixe só custa tempo aqui. vad_filter desligado porque as pausas
    # entre frases são NOSSAS, colocadas de propósito; o VAD cortaria elas e
    # desalinharia tudo.
    segs, info = m.transcribe(args.audio, language=args.idioma, word_timestamps=True,
                              vad_filter=False, beam_size=1)

    palavras = []
    texto = []
    for s in segs:
        texto.append(s.text)
        for w in (s.words or []):
            t = w.word.strip()
            if not t:
                continue
            palavras.append({"text": t,
                             "start": int(round(w.start * 1000)),
                             "end": int(round(w.end * 1000)),
                             "confidence": round(float(w.probability), 4),
                             "speaker": None})
    if not palavras:
        raise SystemExit("❌ nenhuma palavra reconhecida")

    # Cinto de segurança: o Whisper às vezes devolve palavra começando antes da
    # anterior. Aqui não aconteceu em 5592 palavras, mas custa 3 linhas garantir.
    ant = 0
    for w in palavras:
        if w["start"] < ant:
            w["start"] = ant
        if w["end"] <= w["start"]:
            w["end"] = w["start"] + 30
        ant = w["start"]

    gasto = time.time() - t0
    saida = {"text": " ".join(texto).strip(),
             "words": palavras,
             "audio_duration": round(info.duration, 2),
             "confidence": round(sum(w["confidence"] for w in palavras) / len(palavras), 4),
             "language_code": args.idioma,
             "motor": f"faster-whisper/{args.modelo} (cpu int8)"}
    json.dump(saida, open(args.out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"✅ {len(palavras)} palavras · {info.duration/60:.1f}min de áudio · "
          f"{gasto:.0f}s (RTF {gasto/info.duration:.3f})", flush=True)


if __name__ == "__main__":
    main()
