import os
import sys
import json
import time
import argparse
import requests

def load_env(env_path):
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"\'')
    return env_vars

def read_file_chunks(file_path, chunk_size=5242880):
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data

def main():
    parser = argparse.ArgumentParser(description="Transcreve um arquivo de áudio individual usando a API do AssemblyAI")
    parser.add_argument("--file", required=True, help="Caminho do arquivo de áudio (.wav)")
    args = parser.parse_args()

    audio_path = os.path.abspath(args.file)
    if not os.path.exists(audio_path):
        print(f"❌ Arquivo de áudio não encontrado: {audio_path}", file=sys.stderr)
        sys.exit(1)

    print(f"🎙️ [transcribe_file] Iniciando transcrição para: {audio_path}")

    # 1. Carrega credenciais do .env
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
    env_vars = load_env(env_path)
    api_key = env_vars.get("ASSEMBLYAI_API_KEY")

    if not api_key:
        print("❌ Chave ASSEMBLYAI_API_KEY não encontrada no arquivo .env", file=sys.stderr)
        sys.exit(1)

    # 2. Upload do arquivo
    headers = {
        "authorization": api_key,
        "content-type": "application/octet-stream"
    }
    print("🎙️ [transcribe_file] Fazendo upload do áudio...")
    upload_resp = requests.post(
        "https://api.assemblyai.com/v2/upload",
        headers=headers,
        data=read_file_chunks(audio_path)
    )
    
    if upload_resp.status_code != 200:
        print(f"❌ Falha no upload do áudio: {upload_resp.text}", file=sys.stderr)
        sys.exit(1)
        
    upload_url = upload_resp.json().get("upload_url")
    print(f"🎙️ [transcribe_file] Upload concluído.")

    # 3. Solicita a transcrição
    transcript_url = "https://api.assemblyai.com/v2/transcript"
    payload = {
        "audio_url": upload_url,
        "language_code": "en"
    }
    headers_json = {
        "authorization": api_key,
        "content-type": "application/json"
    }
    
    trans_resp = requests.post(transcript_url, json=payload, headers=headers_json)
    if trans_resp.status_code != 200:
        print(f"❌ Falha ao solicitar transcrição: {trans_resp.text}", file=sys.stderr)
        sys.exit(1)
        
    transcript_id = trans_resp.json().get("id")
    print(f"🎙️ [transcribe_file] Transcrição iniciada com ID: {transcript_id}. Aguardando...")

    # 4. Polling
    polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    
    while True:
        poll_resp = requests.get(polling_url, headers={"authorization": api_key})
        if poll_resp.status_code != 200:
            print(f"❌ Erro ao consultar status da transcrição: {poll_resp.text}", file=sys.stderr)
            sys.exit(1)
            
        poll_data = poll_resp.json()
        status = poll_data.get("status")
        
        if status == "completed":
            transcript_result = poll_data
            break
        elif status == "error":
            print(f"❌ Erro no processamento da transcrição: {poll_data.get('error')}", file=sys.stderr)
            sys.exit(1)
            
        time.sleep(5)

    # 5. Salva o resultado JSON
    output_dir = os.path.dirname(audio_path)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    transcript_output_path = os.path.join(output_dir, f"{base_name}.json")
    
    with open(transcript_output_path, "w", encoding="utf-8") as f:
        json.dump(transcript_result, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Transcrição concluída com sucesso! Salva em: {transcript_output_path}")

if __name__ == "__main__":
    main()
