import os
import sys
import argparse
import soundfile as sf
import numpy as np
from kokoro import KPipeline

def main():
    parser = argparse.ArgumentParser(description="Mecanismo de TTS Kokoro Agnóstico")
    parser.add_argument("--input", required=True, help="Caminho do arquivo de texto de entrada")
    parser.add_argument("--output", required=True, help="Caminho do arquivo de áudio de saída (.wav)")
    parser.add_argument("--voice", default="bm_george", help="Voz do Kokoro (ex: bm_george, af_bella)")
    parser.add_argument("--speed", type=float, default=0.9, help="Velocidade da narração")
    parser.add_argument("--silence", type=float, default=1.0, help="Silêncio em segundos entre parágrafos")
    parser.add_argument("--lang", default="a", help="Código de linguagem (ex: 'a' para inglês, 'b' para português se suportado)")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Arquivo de entrada não encontrado: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("❌ O texto de entrada está vazio.")
        sys.exit(1)

    # Garante que o diretório de saída existe
    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"🎙️ Iniciando síntese Kokoro:")
    print(f"   - Entrada: {args.input}")
    print(f"   - Saída  : {output_path}")
    print(f"   - Voz    : {args.voice}")
    print(f"   - Speed  : {args.speed}x")
    print(f"   - Pausa  : {args.silence}s")

    try:
        pipeline = KPipeline(lang_code=args.lang)
        
        # Injeção de silêncio para cadência (taxa de amostragem de 24kHz)
        sample_rate = 24000
        silence_samples = np.zeros(int(sample_rate * args.silence), dtype=np.float32)
        
        # Divide o texto por parágrafos para aplicar a cadência
        generator = pipeline(text, voice=args.voice, speed=args.speed, split_pattern=r'\n\n+')
        
        all_audio = []
        for gs, ps, audio in generator:
            all_audio.append(audio)
            if args.silence > 0:
                all_audio.append(silence_samples)
        
        if not all_audio:
            raise Exception("Nenhum segmento de áudio foi gerado pelo pipeline do Kokoro.")

        # Concatena todos os segmentos de áudio
        final_audio = np.concatenate(all_audio)
        
        # Salva o arquivo .wav final
        sf.write(output_path, final_audio, sample_rate)
        print(f"✅ Áudio gerado e salvo com sucesso em: {output_path}")
        
    except Exception as e:
        print(f"❌ Erro durante a síntese de voz: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
