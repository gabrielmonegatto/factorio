"""
tts_kokoro.py — motor de narração da fábrica (roda dentro do container factorio-tts).

## A mina da pausa (medida em 20/08, resolvida aqui em 22/08)

O Kokoro NÃO devolve o áudio justo: ele cola ~1,1s de silêncio no fim de cada
pedaço que gera. Somando com o silêncio que este script injetava, o intervalo
real entre frases dava ~2,1s, e a narração soava arrastada. Antes isso era
consertado depois, com `ffmpeg silenceremove` sobre o wav pronto, o que só
funciona quando você sabe onde ficaram as emendas.

Aqui é o lugar certo: o pedaço ainda está em memória e as fronteiras são
conhecidas. Com `--trim`, cada pedaço é aparado nas duas pontas e o intervalo
passa a ser EXATAMENTE o `--silence` pedido.

  - `--silence 0.75 --trim` é a receita aprovada pelo Gabriel na narração bíblica
  - sem `--trim` o comportamento é o antigo, byte a byte (não quebra quem chama)

## Corte por frase

`--split sentence` corta em ponto final, não em parágrafo. Num sermão de 45min
o parágrafo pode ter 2 minutos, e um pedaço longo demais some com o controle
de respiração. Ponto final é a unidade natural da fala.
"""
import argparse
import os
import re
import sys
import time

import numpy as np
import soundfile as sf
from kokoro import KPipeline

SR = 24000


def aparar(audio, limiar=0.005, folga_ms=40):
    """Corta silêncio das duas pontas, deixando uma folga curta.

    Limiar por amplitude absoluta, não por dB: o silêncio do Kokoro é silêncio
    digital de verdade (zeros), não ruído de fundo, então não precisa de nada
    mais fino. A folga evita cortar o ataque da consoante inicial.
    """
    forte = np.abs(audio) > limiar
    if not forte.any():
        return audio[:0]
    folga = int(SR * folga_ms / 1000)
    ini = max(0, int(np.argmax(forte)) - folga)
    fim = min(len(audio), len(audio) - int(np.argmax(forte[::-1])) + folga)
    return audio[ini:fim]


def main():
    p = argparse.ArgumentParser(description="Mecanismo de TTS Kokoro agnóstico")
    p.add_argument("--input", required=True, help="arquivo de texto de entrada")
    p.add_argument("--output", required=True, help="arquivo .wav de saída")
    p.add_argument("--voice", default="bm_george", help="voz do Kokoro (bm_george, am_adam, am_onyx...)")
    p.add_argument("--speed", type=float, default=0.9)
    p.add_argument("--silence", type=float, default=1.0, help="intervalo entre pedaços, em segundos")
    p.add_argument("--lang", default="a", help="'a' inglês americano, 'b' britânico")
    p.add_argument("--split", choices=["paragraph", "sentence"], default="paragraph")
    p.add_argument("--trim", action="store_true",
                   help="apara as pontas de cada pedaço (ver a mina da pausa no topo)")
    p.add_argument("--progresso", type=int, default=0,
                   help="a cada N pedaços, imprime andamento (0 = calado)")
    args = p.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"❌ entrada não encontrada: {args.input}")
    texto = open(args.input, encoding="utf-8").read().strip()
    if not texto:
        sys.exit("❌ o texto de entrada está vazio.")

    saida = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(saida), exist_ok=True)

    # O Kokoro aceita o padrão de corte; frase é regex com lookbehind de pontuação.
    padrao = r"\n\n+" if args.split == "paragraph" else r"(?<=[.!?])\s+"

    print(f"🎙️  {os.path.basename(args.input)} → {os.path.basename(saida)}", flush=True)
    print(f"    voz={args.voice} speed={args.speed} corte={args.split} "
          f"pausa={args.silence}s trim={'sim' if args.trim else 'não'}", flush=True)

    pipeline = KPipeline(lang_code=args.lang)
    quieto = np.zeros(int(SR * args.silence), dtype=np.float32)

    pedacos = []
    t0 = time.time()
    n = 0
    for _gs, _ps, audio in pipeline(texto, voice=args.voice, speed=args.speed,
                                    split_pattern=padrao):
        a = np.asarray(audio, dtype=np.float32)
        if args.trim:
            a = aparar(a)
        if not len(a):
            continue
        pedacos.append(a)
        if args.silence > 0:
            pedacos.append(quieto)
        n += 1
        if args.progresso and n % args.progresso == 0:
            feito = sum(len(x) for x in pedacos) / SR
            print(f"    [{n}] {feito/60:.1f}min de áudio em {time.time()-t0:.0f}s", flush=True)

    if not pedacos:
        sys.exit("❌ o Kokoro não gerou nenhum segmento de áudio.")
    if args.silence > 0:
        pedacos.pop()          # nada de silêncio pendurado no fim do arquivo

    final = np.concatenate(pedacos)
    sf.write(saida, final, SR)
    dur = len(final) / SR
    gasto = time.time() - t0
    print(f"✅ {dur/60:.1f}min de áudio · {n} pedaços · {gasto:.0f}s "
          f"(RTF {gasto/dur:.2f}) · {os.path.getsize(saida)/1e6:.1f}MB", flush=True)


if __name__ == "__main__":
    main()
