#!/usr/bin/env python3
"""
omni_infer.py — inferência do OmniVoice (k2-fsa), modo clonagem cross-lingual.

Serve à lateralização de idioma do canal: clona a voz do `bm_george` (voz oficial,
inglês) e faz ela falar português/espanhol. Assim os 3 canais têm o MESMO narrador
em vez de 3 vozes soltas do Kokoro.

Modos (a API aceita os três):
  clonagem  → --ref audio.wav --ref-text "transcrição EXATA do audio"
  design    → --instruct "male, low pitch, calm preacher"
  auto      → nenhum dos dois (modelo escolhe)

Uso:
  python3 omni_infer.py --text-file /data/pt.txt --lang Portuguese \
      --ref /data/ref_george.wav --ref-text-file /data/ref_george.txt \
      --out /data/pt_clone.wav

Env: OMNI_DEVICE=cpu|cuda:0 (default cpu)
"""
import argparse
import os
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--text-file", dest="text_file")
    ap.add_argument("--lang", default=None, help='"Portuguese" | "Spanish" | "English"')
    ap.add_argument("--ref")
    ap.add_argument("--ref-text", default="")
    ap.add_argument("--ref-text-file", dest="ref_text_file")
    ap.add_argument("--instruct")
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--out", default="/data/omni.wav")
    args = ap.parse_args()

    texto = open(args.text_file, encoding="utf-8").read().strip() if args.text_file else args.text
    if not texto:
        raise SystemExit("faltou --text ou --text-file")

    ref_text = args.ref_text
    if args.ref_text_file:
        ref_text = open(args.ref_text_file, encoding="utf-8").read().strip()

    device = os.environ.get("OMNI_DEVICE", "cpu")
    print(f"[omni] carregando modelo em device={device} ...", flush=True)
    t0 = time.time()
    from omnivoice import OmniVoice
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=device)
    print(f"[omni] modelo carregado em {time.time()-t0:.1f}s", flush=True)

    kw = {"text": texto}
    if args.lang:
        kw["language"] = args.lang
    if args.ref:
        # clonagem: ref_text tem que ser a transcrição EXATA do ref_audio,
        # senão o modelo desalinha e a voz sai deformada.
        kw["ref_audio"] = args.ref
        kw["ref_text"] = ref_text
        print(f"[omni] clonando de {args.ref} ({len(ref_text)} chars de ref_text)", flush=True)
    elif args.instruct:
        kw["instruct"] = args.instruct
    if args.speed:
        kw["speed"] = args.speed

    print(f"[omni] gerando {len(texto)} chars em lang={args.lang} ...", flush=True)
    t1 = time.time()
    audios = model.generate(**kw)   # devolve LISTA de np.ndarray 1-D
    gen = time.time() - t1

    import soundfile as sf
    arr = audios[0] if isinstance(audios, (list, tuple)) else audios
    sr = getattr(model, "sampling_rate", 24000)
    sf.write(args.out, arr, sr)

    dur = len(arr) / float(sr)
    rtf = gen / dur if dur else float("nan")
    print(f"[omni] RESULTADO: audio={dur:.1f}s | geracao={gen:.1f}s | "
          f"RTF={rtf:.2f} ({1/rtf:.2f}x tempo real) -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
