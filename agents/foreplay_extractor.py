import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load env variables from _factorio/.env
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

TEABLE_TOKEN = os.getenv("TEABLE_TOKEN", "teable_accTyjWZd49HtTkEi4R_r6fhyEdLypI2Ur9uvLdIj9oTmCSfsQvVa/T+vZFGorQ=")
# Auto-detect if running inside Docker or local host
TEABLE_URL = os.getenv("TEABLE_URL", "http://localhost:3000")

# Teable Table IDs in Operations base
CREATIVES_TABLE_ID = "tblgdfwZD1VIkRB9sZE"
TASKS_TABLE_ID = "tblVzN1Eo8tfk7GX2CJ"
APIS_TABLE_ID = "tblWyciiCjbZaHof2Ey"
TOOLS_TABLE_ID = "tblsLfGpdU5kynWoUUN"
AGENTS_TABLE_ID = "tblo1PEgleR0G17MVIz"

TEABLE_HEADERS = {
    "Authorization": f"Bearer {TEABLE_TOKEN}",
    "Content-Type": "application/json"
}

def get_teable_url(path):
    # If the default local port fails, check if we can reach it
    return f"{TEABLE_URL}{path}"

def log_task(task_id, message, append=True):
    print(f"[TASK LOG] {message}")
    if not task_id:
        return
    # Fetch current logs first
    current_logs = ""
    if append:
        try:
            r = requests.get(get_teable_url(f"/api/table/{TASKS_TABLE_ID}/record/{task_id}"), headers=TEABLE_HEADERS)
            if r.status_code == 200:
                current_logs = r.json().get("fields", {}).get("Logs", "") or ""
        except Exception as e:
            print(f"Error fetching existing logs: {e}")
            
    new_logs = f"{current_logs}\n{message}" if current_logs else message
    try:
        requests.patch(get_teable_url(f"/api/table/{TASKS_TABLE_ID}/record/{task_id}"), headers=TEABLE_HEADERS, json={
            "record": {
                "fields": {
                    "Logs": new_logs
                }
            }
        })
    except Exception as e:
        print(f"Error updating logs in Teable: {e}")

def update_task_status(task_id, status):
    if not task_id:
        return
    try:
        requests.patch(get_teable_url(f"/api/table/{TASKS_TABLE_ID}/record/{task_id}"), headers=TEABLE_HEADERS, json={
            "record": {
                "fields": {
                    "Status": status
                }
            }
        })
    except Exception as e:
        print(f"Error updating status in Teable: {e}")

def fetch_api_credentials(api_name):
    url = get_teable_url(f"/api/table/{APIS_TABLE_ID}/record")
    r = requests.get(url, headers=TEABLE_HEADERS)
    if r.status_code == 200:
        records = r.json().get("records", [])
        for rec in records:
            fields = rec.get("fields", {})
            if fields.get("Name") == api_name:
                return fields.get("API Key"), fields.get("Base URL")
    return None, None

def fetch_tool_code(tool_name):
    url = get_teable_url(f"/api/table/{TOOLS_TABLE_ID}/record")
    r = requests.get(url, headers=TEABLE_HEADERS)
    if r.status_code == 200:
        records = r.json().get("records", [])
        for rec in records:
            fields = rec.get("fields", {})
            if fields.get("Name") == tool_name:
                return fields.get("Code")
    return None

def fetch_agent_config(agent_name):
    url = get_teable_url(f"/api/table/{AGENTS_TABLE_ID}/record")
    r = requests.get(url, headers=TEABLE_HEADERS)
    if r.status_code == 200:
        records = r.json().get("records", [])
        for rec in records:
            fields = rec.get("fields", {})
            if fields.get("Name") == agent_name:
                return fields
    return None

def execute_extractor(task_id, instruction):
    log_task(task_id, f"Iniciando Foreplay Extractor Agent com a instrução: '{instruction}'")
    update_task_status(task_id, "Em Processamento")
    
    # 1. Fetch Foreplay API Key dynamically from Teable
    log_task(task_id, "Buscando credenciais da API do Foreplay no Teable...")
    foreplay_key, foreplay_base_url = fetch_api_credentials("Foreplay")
    if not foreplay_key:
        log_task(task_id, "Erro: Credenciais do Foreplay não localizadas na tabela APIs.")
        update_task_status(task_id, "Erro")
        return
        
    # 2. Fetch and compile dynamic tools from Teable
    log_task(task_id, "Carregando ferramenta 'resolve_redirects' do Teable...")
    tool_code = fetch_tool_code("resolve_redirects")
    resolve_url_fn = None
    if tool_code:
        try:
            # Compile and execute the tool code in a local namespace
            local_vars = {}
            exec(tool_code, globals(), local_vars)
            resolve_url_fn = local_vars.get("resolve_url")
            log_task(task_id, "Ferramenta 'resolve_redirects' compilada com sucesso!")
        except Exception as e:
            log_task(task_id, f"Erro ao compilar ferramenta 'resolve_redirects': {e}")
    else:
        log_task(task_id, "Aviso: Ferramenta 'resolve_redirects' não encontrada. Usando URL bruta do criativo.")

    # 3. Call Gemini to parse parameters if instruction is provided
    import google.generativeai as genai
    
    # Fetch agent configuration for Foreplay Extractor
    agent_config = fetch_agent_config("Foreplay Extractor")
    if agent_config:
        system_prompt = agent_config.get("System Prompt", "")
        model_name = agent_config.get("Model", "gemini-2.5-flash")
    else:
        system_prompt = """Você é o Foreplay Extractor Agent, especialista em interpretar instruções de scraping de criativos.
Sua missão é ler o comando do usuário e extrair os seguintes parâmetros estruturados em formato JSON:
- limit: quantidade de anúncios a extrair (padrão 5, máximo 20).
- brand_name: nome da marca específica se for mencionada no comando.
- niches: nicho ou categoria se mencionada.

Responda APENAS com o JSON contendo os parâmetros encontrados. Exemplo:
{"limit": 5, "brand_name": "IM8 Health", "niches": null}"""
        model_name = "gemini-2.5-flash"
        
    parsed_params = {"limit": 5, "brand_name": None, "niches": None}
    
    if instruction:
        log_task(task_id, f"Interpretando instrução com o modelo {model_name}...")
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            try:
                # We can configure the model
                # Some environments don't support gemini-2.5-flash or have a typo, so we do a fallback try block
                model = None
                for candidate_model in [model_name, "gemini-3-flash-preview", "gemini-1.5-flash"]:
                    try:
                        model = genai.GenerativeModel(
                            model_name=candidate_model,
                            system_instruction=system_prompt
                        )
                        # Test model initialization
                        break
                    except Exception:
                        continue
                
                if model:
                    response = model.generate_content(instruction)
                    response_text = response.text.strip()
                    if response_text.startswith("```"):
                        lines = response_text.splitlines()
                        if lines[0].startswith("```json") or lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines[-1].startswith("```"):
                            lines = lines[:-1]
                        response_text = "\n".join(lines).strip()
                    
                    parsed_params = json.loads(response_text)
                    log_task(task_id, f"Parâmetros extraídos pela IA: {parsed_params}")
                else:
                    log_task(task_id, "Nenhum modelo Gemini compatível pôde ser inicializado.")
            except Exception as e:
                log_task(task_id, f"Erro ao chamar Gemini: {e}. Usando parâmetros padrão.")
        else:
            log_task(task_id, "Aviso: Nenhuma chave API_KEY do Gemini encontrada. Usando parâmetros padrão.")

    limit = int(parsed_params.get("limit") or 5)
    brand_name = parsed_params.get("brand_name")
    
    # 4. Call Foreplay API
    log_task(task_id, "Buscando criativos do Swipefile do Foreplay...")
    headers = {
        "Authorization": f"Bearer {foreplay_key}"
    }
    
    api_limit = 50 if brand_name else limit
    foreplay_url = f"{foreplay_base_url}/swipefile/ads?limit={api_limit}"
    
    try:
        r = requests.get(foreplay_url, headers=headers)
        if r.status_code != 200:
            log_task(task_id, f"Erro na API do Foreplay: {r.status_code} - {r.text}")
            update_task_status(task_id, "Erro")
            return
        all_ads = r.json().get("data", [])
        log_task(task_id, f"Sucesso! Retornados {len(all_ads)} anúncios do Foreplay.")
    except Exception as e:
        log_task(task_id, f"Erro ao chamar API do Foreplay: {e}")
        update_task_status(task_id, "Erro")
        return

    # Filter by brand name if specified
    ads = []
    for ad in all_ads:
        if brand_name:
            ad_brand = (ad.get("brand_name") or ad.get("name") or "").lower()
            if brand_name.lower() not in ad_brand:
                continue
        ads.append(ad)
        if len(ads) >= limit:
            break

    log_task(task_id, f"Processando {len(ads)} anúncios após filtragem.")

    # 5. Insert into Teable
    for ad in ads:
        ad_id = ad.get("id")
        raw_url = ad.get("link_url") or ""
        resolved_url = raw_url
        
        # Apply the compiled redirect resolution tool if available
        if resolve_url_fn and raw_url:
            log_task(task_id, f"Resolvendo redirecionamentos de URL para o criativo {ad_id}: {raw_url}")
            resolved_url = resolve_url_fn(raw_url)
            log_task(task_id, f"URL final resolvida: {resolved_url}")

        display_format = ad.get("display_format")
        if display_format:
            display_format = display_format.lower()
            if display_format not in ["video", "image", "carousel", "dco", "story", "reels"]:
                display_format = None
                
        platforms = ad.get("publisher_platform")
        valid_platforms = []
        if platforms:
            if isinstance(platforms, str):
                platforms = [platforms]
            for p in platforms:
                p_lower = p.lower()
                if p_lower in ["facebook", "instagram", "audience_network", "messenger"]:
                    valid_platforms.append(p_lower)

        log_task(task_id, f"Salvando criativo {ad_id} ({ad.get('name')}) no Teable...")
        fields = {
            "ID": ad_id,
            "Name": ad.get("name") or ad.get("title") or "Unnamed Creative",
            "Brand Name": ad.get("brand_name") or "",
            "Description": ad.get("description") or "",
            "Ad Library URL": ad.get("ad_library_url") or "",
            "Landing Page URL": resolved_url,
            "Display Format": display_format,
            "Publisher Platforms": valid_platforms,
            "Full Transcription": ad.get("full_transcription") or "",
            "Processed Status": "Pendente"
        }
        
        # Check if already exists in Teable to avoid duplicates
        check_url = get_teable_url(f"/api/table/{CREATIVES_TABLE_ID}/record")
        # Quick check using query param
        check_r = requests.get(check_url, headers=TEABLE_HEADERS)
        existing_record_id = None
        if check_r.status_code == 200:
            for rec in check_r.json().get("records", []):
                if rec.get("fields", {}).get("ID") == ad_id:
                    existing_record_id = rec.get("id")
                    break
        
        if existing_record_id:
            log_task(task_id, f"Registro {existing_record_id} para o criativo {ad_id} já existe. Ignorando...")
            continue

        insert_url = get_teable_url(f"/api/table/{CREATIVES_TABLE_ID}/record")
        r_ins = requests.post(insert_url, headers=TEABLE_HEADERS, json={"records": [{"fields": fields}]})
        if r_ins.status_code == 201:
            record_id = r_ins.json().get("records", [{}])[0].get("id")
            log_task(task_id, f"Registro criado com sucesso: {record_id}")
            
            # Upload media file to the record's Media Files attachment column
            media_url = ad.get("video") or ad.get("image") or ad.get("thumbnail")
            if media_url:
                log_task(task_id, f"Fazendo upload de mídia para o anexo do Teable: {media_url}")
                upload_url = get_teable_url(f"/api/table/{CREATIVES_TABLE_ID}/record/{record_id}/fldcinVyqRozsILIAzP/uploadAttachment")
                r_upload = requests.post(upload_url, headers={"Authorization": f"Bearer {TEABLE_TOKEN}"}, files={"fileUrl": (None, media_url)})
                if r_upload.status_code in [200, 201]:
                    log_task(task_id, "Upload de anexo realizado com sucesso!")
                else:
                    log_task(task_id, f"Aviso: Falha ao fazer upload do anexo: {r_upload.status_code} - {r_upload.text}")
        else:
            log_task(task_id, f"Erro ao criar registro: {r_ins.status_code} - {r_ins.text}")
            
    log_task(task_id, "Execução concluída com sucesso!")
    update_task_status(task_id, "Concluído")

if __name__ == "__main__":
    # If running standalone with arguments
    if len(sys.argv) > 2:
        task_id = sys.argv[1]
        instruction = sys.argv[2]
        execute_extractor(task_id, instruction)
    else:
        print("Usage: python foreplay_extractor.py <task_id> <instruction>")
        # Local test fallback
        execute_extractor(None, "Puxe os últimos anúncios")
