import os
import sys
import json
import argparse
import re
import subprocess
import glob
from json_to_ass import generate_ass
from PIL import Image, ImageDraw, ImageFont

DB_HELPER = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_db.py"))

def generate_corner_qr_card(assets_dir):
    qr_source_path = os.path.join(assets_dir, "qrcodes", "sample_qr.png")
    output_path = os.path.join(assets_dir, "qrcodes", "corner_qr.png")
    try:
        canvas_w, canvas_h = 160, 180
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        
        card_w, card_h = 136, 136
        card_x = (canvas_w - card_w) // 2
        card_y = 10
        
        try:
            draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                radius=12,
                fill=(255, 255, 255, 255)
            )
        except AttributeError:
            draw.rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h],
                fill=(255, 255, 255, 255)
            )
            
        qr_img = Image.open(qr_source_path).convert("RGBA")
        qr_size = 120
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        qr_x = card_x + (card_w - qr_size) // 2
        qr_y = card_y + (card_h - qr_size) // 2
        canvas.paste(qr_img, (qr_x, qr_y), qr_img)
        
        text = "BOOKS & DEVOTIONALS"
        font_paths = [
            "C:\\Windows\\Fonts\\segoeuib.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]
        
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, 10)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()
            
        try:
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_w = text_bbox[2] - text_bbox[0]
        except AttributeError:
            text_w, _ = draw.textsize(text, font=font)
            
        text_x = (canvas_w - text_w) // 2
        text_y = card_y + card_h + 10
        
        draw.text((text_x + 1, text_y + 1), text, fill=(0, 0, 0, 180), font=font)
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 220), font=font)
        
        canvas.save(output_path, "PNG")
        print(f"🎨 [FFmpeg Render] Card do QR Code do canto gerado em: {output_path}")
    except Exception as e:
        print(f"⚠️ Erro ao gerar corner_qr.png: {e}")


def get_audio_duration(file_path):
    cmd = ["ffprobe", "-i", file_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def get_best_video_encoder():
    try:
        res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, check=True)
        if "h264_nvenc" in res.stdout:
            print("🚀 [FFmpeg] Placa NVIDIA detectada! Utilizando codificação acelerada por GPU (h264_nvenc).")
            return "h264_nvenc", ["-preset", "p1"]
    except Exception:
        pass
    print("🐌 [FFmpeg] Codificador de GPU não disponível. Utilizando codificação por CPU (libx264).")
    return "libx264", ["-preset", "faster", "-crf", "23"]

def main():
    parser = argparse.ArgumentParser(description="Renderizador de vídeo integrado usando FFmpeg")
    parser.add_argument("--record-id", required=True, help="ID da task no Teable")
    args = parser.parse_args()

    record_id = args.record_id
    encoder, preset_args = get_best_video_encoder()

    # 1. Obtém dados estruturados do sermão do banco de dados
    print(f"🎬 [FFmpeg Render] Iniciando esteira para a task: {record_id}")
    
    # Atualiza status para Em Processamento
    subprocess.run([
        sys.executable, DB_HELPER,
        "--record-id", record_id,
        "--update-status", "Em Processamento",
        "--logs", "[FFmpeg RENDER] Iniciando renderizador otimizado com FFmpeg...\n"
    ], check=True)

    try:
        # Pega as informações do sermão
        res_info = subprocess.run([
            sys.executable, DB_HELPER,
            "--record-id", record_id,
            "--get-info"
        ], capture_output=True, text=True, check=True)
        
        info = json.loads(res_info.stdout.strip())
        sermon_dir = info["sermonDir"]
        sermon_title = info["sermonTitle"]
        sermon_number = info["sermonNumber"]
        transcript_path = info["transcriptPath"]
        
        sermon_slug = os.path.basename(sermon_dir)
        print(f"🎬 [FFmpeg Render] Diretório do Sermão: {sermon_dir}")
        print(f"🎬 [FFmpeg Render] Número do Sermão: {sermon_number}")

        assets_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "apps", "channels", "channels_youtube", "treasures_charlesspurgeon", "_assets"))
        global_worship_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "apps", "channels", "channels_youtube", "_globalassets", "worship"))

        # Listar e ordenar fundos
        bgs = sorted(glob.glob(os.path.join(assets_dir, "cathedral", "cathedral_bg_cf_*.png")))
        # Listar e ordenar bustos
        avatars = sorted(glob.glob(os.path.join(assets_dir, "avatars", "spurgeon_bust_cf_*.png")))
        # Listar e ordenar BGMs
        bgms = sorted(glob.glob(os.path.join(global_worship_dir, "worship_*.mp3")))

        if not bgs or not avatars or not bgms:
            raise Exception("Erro: Faltam assets básicos de catedrais, bustos ou BGMs para a rotação.")

        # Fórmula determinística
        N = int(sermon_number)
        selected_bg = bgs[(N - 1) % len(bgs)]
        selected_avatar = avatars[(N - 1) % len(avatars)]
        selected_bgm = bgms[(N - 1) % len(bgms)]

        selected_bg_name = os.path.basename(selected_bg)
        selected_avatar_name = os.path.basename(selected_avatar)
        selected_bgm_name = os.path.basename(selected_bgm)

        print(f"🎨 Assets Selecionados para o Sermão {sermon_number}:")
        print(f"  - Fundo:   {selected_bg_name}")
        print(f"  - Busto:   {selected_avatar_name}")
        print(f"  - Trilha:  {selected_bgm_name}")

        # Atualiza o banco com a escolha dos assets
        subprocess.run([
            sys.executable, DB_HELPER,
            "--record-id", record_id,
            "--update-status", "Em Processamento",
            "--background-image", selected_bg_name,
            "--preacher-image", selected_avatar_name,
            "--bgm-audio", selected_bgm_name,
            "--logs", f"[CONFIG] Assets selecionados: Fundo={selected_bg_name}, Busto={selected_avatar_name}, Trilha={selected_bgm_name}\n"
        ], check=True)

        # 3. Caminhos dos arquivos de áudio e transcrição
        hook_wav = os.path.join(sermon_dir, "hook.wav")
        hook_json = os.path.join(sermon_dir, "hook.json")
        cta_wav = os.path.join(sermon_dir, "cta_narration.wav")
        cta_json = os.path.join(sermon_dir, "cta_narration.json")
        sermon_wav = os.path.join(sermon_dir, f"sermon_{int(sermon_number)}.wav")

        if not os.path.exists(sermon_wav):
            # Fallback para tentar sermon_XX.wav
            sermon_wav = os.path.join(sermon_dir, f"sermon_{re.sub(r'^0+', '', sermon_number)}.wav")
            if not os.path.exists(sermon_wav):
                # Outro fallback listando qualquer wav com "sermon" no nome
                wav_files = glob.glob(os.path.join(sermon_dir, "sermon_*.wav"))
                if wav_files:
                    sermon_wav = wav_files[0]
                else:
                    raise Exception(f"Erro: Áudio do sermão principal não encontrado na pasta {sermon_dir}")

        # 4. Geração das legendas .ass
        print("📝 Convertendo transcrições JSON para legendas ASS...")
        sermon_ass = os.path.join(sermon_dir, "sermon.ass")
        hook_ass = os.path.join(sermon_dir, "hook.ass")
        outro_ass = os.path.join(sermon_dir, "outro.ass")

        generate_ass(transcript_path, sermon_ass, "Default")
        generate_ass(hook_json, hook_ass, "Hook")
        generate_ass(cta_json, outro_ass, "Hook")

        # 5. Calcula as durações exatas
        sermon_duration = get_audio_duration(sermon_wav)
        hook_duration = get_audio_duration(hook_wav)
        outro_duration = get_audio_duration(cta_wav)

        print(f"⏱️ Durações calculadas: Hook={hook_duration:.2f}s, Sermão={sermon_duration:.2f}s, Outro={outro_duration:.2f}s")

        # 6. Criação de pastas temporárias para os segmentos de vídeo
        temp_render_dir = os.path.join(sermon_dir, "_temp_render")
        os.makedirs(temp_render_dir, exist_ok=True)

        hook_segment = os.path.join(temp_render_dir, "1_hook.mp4")
        sermon_segment = os.path.join(temp_render_dir, "3_sermon.mp4")
        outro_segment = os.path.join(temp_render_dir, "4_outro.mp4")

        # Garante a existência do QR code do canto
        generate_corner_qr_card(assets_dir)
        corner_qr_path = os.path.join(assets_dir, "qrcodes", "corner_qr.png")

        # Assets fixos pré-renderizados
        intro_cta_fixed = os.path.join(assets_dir, "pre_rendered", "intro_cta_fixed.mp4")
        outro_cta_fixed = os.path.join(assets_dir, "pre_rendered", "outro_cta_fixed.mp4")
        endscreen_fixed = os.path.join(assets_dir, "pre_rendered", "endscreen_fixed.mp4")
        sparks_loop = os.path.join(assets_dir, "sparks_loop.mp4")
        hook_bgm = os.path.join(global_worship_dir, "frequencial_432hz_01.mp3")

        # Verifica se os fixos existem
        for f in [intro_cta_fixed, outro_cta_fixed, endscreen_fixed, sparks_loop, hook_bgm, corner_qr_path]:
            if not os.path.exists(f):
                raise Exception(f"Erro: Arquivo fixo obrigatório ausente: {f}")


        # 7. Renderiza o segmento: Hook
        print("🎬 Gerando segmento do Hook...")
        # Margem de respiro de 0.5 segundos no final
        hook_seg_dur = hook_duration + 0.5
        
        # Filtro do Hook: catedral em opacidade 15% + blur + queima a legenda
        # Usamos caminhos relativos ou com barras normais para o filtro 'subtitles' do FFmpeg não dar erro no Windows
        hook_ass_rel = os.path.relpath(hook_ass, start=os.getcwd()).replace("\\", "/")
        
        cmd_hook = [
            "ffmpeg", "-y",
            "-loglevel", "warning", "-nostats",
            "-loop", "1", "-i", selected_bg,
            "-i", hook_wav,
            "-i", hook_bgm,
            "-filter_complex",
            f"[0:v]scale=1920:1080,colorchannelmixer=rr=0.15:gg=0.15:bb=0.15,boxblur=2:1,subtitles='{hook_ass_rel}'[v];"
            f"[2:a]volume=0.05[bgm];"
            f"[1:a][bgm]amix=inputs=2:duration=first[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", encoder, "-pix_fmt", "yuv420p", "-r", "30",
        ] + preset_args + [
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", f"{hook_seg_dur:.3f}",
            hook_segment
        ]
        
        subprocess.run(cmd_hook, check=True)
        print("✅ Segmento do Hook gerado com sucesso!")

        # 8. Renderiza o segmento: Sermão
        print("🎬 Gerando segmento do Sermão...")
        # Margem de respiro de 3.0 segundos no final
        sermon_seg_dur = sermon_duration + 3.0
        
        sermon_ass_rel = os.path.relpath(sermon_ass, start=os.getcwd()).replace("\\", "/")
        
        # Filtro do Sermão:
        # 1. Escala o busto para altura 702
        # 2. Cola o busto num canvas preto de 1920x1080 na posição bottom-right (com 38px de margem à direita)
        # 3. Mescla esse canvas com a catedral selecionada usando screen blend mode a 0.9 de opacidade
        # 4. Escala e mescla o loop de faíscas/partículas por cima com screen blend mode a 0.5 de opacidade
        # 5. Mescla o card do QR Code do canto superior esquerdo na posição 40,40
        # 6. Queima a legenda sermon.ass por cima
        # 7. Mixa o áudio do sermão com a música instrumental selecionada (volume a 5%)
        cmd_sermon = [
            "ffmpeg", "-y",
            "-loglevel", "warning", "-nostats",
            "-loop", "1", "-i", selected_bg,
            "-i", selected_avatar,
            "-stream_loop", "-1", "-i", sparks_loop,
            "-loop", "1", "-i", corner_qr_path,
            "-i", sermon_wav,
            "-stream_loop", "-1", "-i", selected_bgm,
            "-filter_complex",
            f"[0:v]scale=1920:1080[bg_scaled];"
            f"[1:v]scale=-1:702[preacher_scaled];"
            f"color=c=black:s=1920x1080[canvas];"
            f"[canvas][preacher_scaled]overlay=1882-overlay_w:1080-overlay_h[preacher_canvas];"
            f"[bg_scaled][preacher_canvas]blend=all_mode=screen:all_opacity=0.9[sermon_static];"
            f"[2:v]scale=1920:1080[sparks_scaled];"
            f"[sermon_static][sparks_scaled]blend=all_mode=screen:all_opacity=0.5[sermon_dynamic];"
            f"[sermon_dynamic][3:v]overlay=40:40[sermon_with_qr];"
            f"[sermon_with_qr]subtitles='{sermon_ass_rel}'[v];"
            f"[5:a]volume=0.05[bgm];"
            f"[4:a][bgm]amix=inputs=2:duration=first[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", encoder, "-pix_fmt", "yuv420p", "-r", "30",
        ] + preset_args + [
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", f"{sermon_seg_dur:.3f}",
            sermon_segment
        ]
        
        subprocess.run(cmd_sermon, check=True)
        print("✅ Segmento do Sermão gerado com sucesso!")

        # 9. Renderiza o segmento: Outro Hook
        print("🎬 Gerando segmento do Outro Hook...")
        outro_seg_dur = outro_duration + 0.5
        
        outro_ass_rel = os.path.relpath(outro_ass, start=os.getcwd()).replace("\\", "/")
        
        cmd_outro = [
            "ffmpeg", "-y",
            "-loglevel", "warning", "-nostats",
            "-loop", "1", "-i", selected_bg,
            "-i", cta_wav,
            "-filter_complex",
            f"[0:v]scale=1920:1080,colorchannelmixer=rr=0.15:gg=0.15:bb=0.15,boxblur=2:1,subtitles='{outro_ass_rel}'[v];"
            f"[1:a]volume=1.0[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", encoder, "-pix_fmt", "yuv420p", "-r", "30",
        ] + preset_args + [
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", f"{outro_seg_dur:.3f}",
            outro_segment
        ]
        
        subprocess.run(cmd_outro, check=True)
        print("✅ Segmento do Outro Hook gerado com sucesso!")

        # 10. Concatenação de todos os pedaços (Sem re-encodar, instantâneo!)
        print("🎬 Concatenando todos os segmentos de vídeo...")
        concat_txt_path = os.path.join(temp_render_dir, "concat.txt")
        
        with open(concat_txt_path, "w", encoding="utf-8") as f:
            h_path = hook_segment.replace('\\', '/')
            i_path = intro_cta_fixed.replace('\\', '/')
            s_path = sermon_segment.replace('\\', '/')
            o_path = outro_segment.replace('\\', '/')
            oc_path = outro_cta_fixed.replace('\\', '/')
            e_path = endscreen_fixed.replace('\\', '/')
            f.write(f"file '{h_path}'\n")
            f.write(f"file '{i_path}'\n")
            f.write(f"file '{s_path}'\n")
            f.write(f"file '{o_path}'\n")
            f.write(f"file '{oc_path}'\n")
            f.write(f"file '{e_path}'\n")

        final_video_path = os.path.join(sermon_dir, "final_spurgeon_sermon.mp4")

        cmd_concat = [
            "ffmpeg", "-y",
            "-loglevel", "warning", "-nostats",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt_path,
            "-c", "copy",
            final_video_path
        ]
        
        subprocess.run(cmd_concat, check=True)
        print(f"🎉 Vídeo final de alta definição compilado com sucesso: {final_video_path}")

        # Limpeza de arquivos temporários
        try:
            for f in [hook_segment, sermon_segment, outro_segment, concat_txt_path]:
                if os.path.exists(f):
                    os.remove(f)
            os.rmdir(temp_render_dir)
            print("🧹 Arquivos temporários de renderização removidos.")
        except Exception as e_clean:
            print(f"⚠️ Aviso ao limpar temporários: {e_clean}")

        # 11. Conclui a task no banco
        subprocess.run([
            sys.executable, DB_HELPER,
            "--record-id", record_id,
            "--update-status", "Concluído",
            "--resultado", final_video_path,
            "--logs", f"[SUCESSO] Render FFmpeg concluído! Vídeo final salvo em: {final_video_path}\n"
        ], check=True)

        print("🎬 [FFmpeg Render] Esteira de renderização finalizada com 100% de sucesso!")

    except Exception as e:
        error_msg = f"\n❌ ERRO NO RENDER FFMPEG: {e}\n"
        print(error_msg, file=sys.stderr)
        
        # Salva o status de Erro no banco
        subprocess.run([
            sys.executable, DB_HELPER,
            "--record-id", record_id,
            "--update-status", "Erro",
            "--logs", error_msg
        ], check=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
