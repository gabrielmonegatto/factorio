import os
import sys
import json
import argparse
import time
import re
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configurações do Banco
import os; DB_URL = os.environ.get("DATABASE_URL") or "postgresql://teable:teable_secret_password@localhost:42345/teable"
SCHEMA = "bseWeczeNfCSaMlu2EC"
TBL_CONTENT = f'"{SCHEMA}"."tblFyPPXJTiynzBKFH2"'
TBL_INDEX = f'"{SCHEMA}"."tblD7Kxoc7gFTgEWoWo"'

# Caminho do .env do factorio
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"))

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

def pre_clean_text(raw_text):
    """
    Passo 1: Filtro Prévio via Regras em Python.
    Limpa de forma programática lixos fixos de OCR, scrap e navegação de sites.
    """
    if not raw_text:
        return ""
        
    text = raw_text.strip()
    
    # 1. Remove lixos óbvios de tags HTML/XML residuais
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. Remove botões e navegação conhecidos (case-insensitive)
    nav_patterns = [
        r'«\s*Prev',
        r'Next\s*»',
        r'«',
        r'»',
        r'\bPrev\b',
        r'\bNext\b',
        r'Go\s*to\s*Evening\s*Reading',
        r'Go\s*to\s*Morning\s*Reading',
        r'Go\s*To\s*Evening\s*Reading',
        r'Go\s*To\s*Morning\s*Reading',
        r'Go\s*to\s*next\s*chapter',
        r'Go\s*to\s*previous\s*chapter'
    ]
    for pattern in nav_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
    # 3. Remove cabeçalhos de sermões repetitivos típicos (ex: do CCEL)
    sermon_headers = [
        r'Sermon\s+\d+[\.\:]?',
        r'\bNo\.\s+\d+\b',
        r'A\s+SERMON\s+PUBLISHED\s+ON\s+THURSDAY,\s+[A-Z\s\d\,]+[\.\:]?',
        r'DELIVERED\s+BY\s+C\.\s*H\.\s*SPURGEON\,?',
        r'AT\s+THE\s+METROPOLITAN\s+TABERNACLE[\w\s\,]+ON\s+LORD\'S\-DAY[\w\s\,]+[\.\:]?'
    ]
    for pattern in sermon_headers:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
    # 4. Remove espaços múltiplos horizontais
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 5. Remove quebras de linha excessivas (mantendo no máximo duas seguidas para parágrafos)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

def clean_and_structure_with_groq(text, title, api_key):
    """
    Passo 2: Envia para a API do Groq para estruturação inteligente do texto.
    Trata rate-limits 429 e faz fallback automático de modelos.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prompt focado em estruturação teológica clássica, títulos e parágrafos
    prompt = f"""
You are a professional theological editor specialized in structuring classic texts and sermons.
Your task is to take the following draft text and format it into clean, perfectly readable Markdown.
The current text is too monolithic and poorly formatted. Please:
- Add appropriate headers if the text has clear divisions (use ## for main sections, ### for sub-topics).
- Organize the paragraphs in a fluid, natural, and solemn way.
- Remove any remnants of scrap garbage, page numbers, or navigation links that the pre-cleaning script might have missed.
- Fix orphaned line breaks (e.g., words split by a hyphen at the end of the original physical line that cut sentences in the middle).
- CRITICAL: Preserve the original language of the text. Do NOT translate the text. If the input text is in English, the output Markdown MUST be in English.
- Do NOT include the main title of the sermon/chapter as a # or ## header at the very beginning of the output, as the application already renders the title automatically from the database. Start directly with the first subtitle, introductory text, or Bible verses.
- Return strictly the formatted Markdown of the sermon/book. Do NOT add assistant notes, introductory explanations, or closing remarks. The output must contain ONLY the structured text itself.

Title: {title}
Text:
{text}
"""
    
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    last_err = None
    
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  💬 Enviando para Groq ({model}) - Tentativa {attempt+1}/{max_retries}...")
                response = requests.post(url, headers=headers, json=payload, timeout=45)
                
                if response.status_code == 200:
                    res_json = response.json()
                    content_out = res_json['choices'][0]['message']['content'].strip()
                    # Remove bloco de código markdown se o modelo envolver em ```markdown ... ```
                    if content_out.startswith("```markdown"):
                        content_out = content_out[11:].rstrip("`").strip()
                    elif content_out.startswith("```"):
                        content_out = content_out[3:].rstrip("`").strip()
                    return content_out, model
                elif response.status_code == 429:
                    retry_after = 15.0
                    try:
                        res_err = response.json()
                        msg = res_err.get("error", {}).get("message", "")
                        m = re.search(r"try again in ([\d\.]+)s", msg)
                        if m:
                            retry_after = float(m.group(1)) + 2.0
                    except:
                        pass
                    print(f"  ⚠️ Groq 429 Rate Limit. Aguardando {retry_after:.2f}s...", file=sys.stderr)
                    time.sleep(retry_after)
                else:
                    last_err = f"API Error {response.status_code}: {response.text}"
                    print(f"  ⚠️ Erro do Groq na chamada ({response.status_code}): {response.text}", file=sys.stderr)
                    break # Pula para o próximo modelo se for outro erro da API
            except Exception as e:
                last_err = str(e)
                print(f"  ⚠️ Erro de rede na chamada do Groq: {e}. Aguardando 5s...", file=sys.stderr)
                time.sleep(5)
                
    raise Exception(f"Falha na estruturação com Groq (Todos os modelos falharam). Último erro: {last_err}")

def clean_and_structure_with_gemini(text, title, api_key):
    """
    Estruturação de conteúdo usando os modelos de IA do Gemini.
    Possui limite de 1.000.000 TPM gratuitamente, sendo ideal para chunks longos.
    """
    models = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
    last_err = None
    
    prompt = f"""
You are a professional theological editor specialized in structuring classic texts and sermons.
Your task is to take the following draft text and format it into clean, perfectly readable Markdown.
The current text is too monolithic and poorly formatted. Please:
- Add appropriate headers if the text has clear divisions (use ## for main sections, ### for sub-topics).
- Organize the paragraphs in a fluid, natural, and solemn way.
- Remove any remnants of scrap garbage, page numbers, or navigation links that the pre-cleaning script might have missed.
- Fix orphaned line breaks (e.g., words split by a hyphen at the end of the original physical line that cut sentences in the middle).
- CRITICAL: Preserve the original language of the text. Do NOT translate the text. If the input text is in English, the output Markdown MUST be in English.
- Do NOT include the main title of the sermon/chapter as a # or ## header at the very beginning of the output, as the application already renders the title automatically from the database. Start directly with the first subtitle, introductory text, or Bible verses.
- Return strictly the formatted Markdown of the sermon/book. Do NOT add assistant notes, introductory explanations, or closing remarks. The output must contain ONLY the structured text itself.

Title: {title}
Text:
{text}
"""

    for model in models:
        version = "v1beta" if "2.5" in model else "v1"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  💬 Enviando para Gemini ({model} via {version}) - Tentativa {attempt+1}/{max_retries}...")
                url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=25)
                if response.status_code == 200:
                    res_json = response.json()
                    content_out = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    # Remove bloco de código markdown se o modelo envolver em ```markdown ... ```
                    if content_out.startswith("```markdown"):
                        content_out = content_out[11:].rstrip("`").strip()
                    elif content_out.startswith("```"):
                        content_out = content_out[3:].rstrip("`").strip()
                    return content_out, model
                elif response.status_code == 429:
                    print(f"  ⚠️ Gemini 429 Rate Limit. Aguardando 10s...", file=sys.stderr)
                    time.sleep(10)
                else:
                    last_err = f"API Error {response.status_code}: {response.text}"
                    print(f"  ⚠️ Erro do Gemini na chamada ({response.status_code}): {response.text}", file=sys.stderr)
                    break
            except Exception as e:
                last_err = str(e)
                print(f"  ⚠️ Erro de rede na chamada do Gemini: {e}. Aguardando 5s...", file=sys.stderr)
                time.sleep(5)
                
    raise Exception(f"Falha na estruturação com Gemini (Todos os modelos falharam). Último erro: {last_err}")

def clean_and_structure_with_openrouter(text, title, api_key):
    """
    Estruturação e limpeza de conteúdo usando OpenRouter.
    Ideal por suportar qualquer tamanho de texto de forma estável, livre de TPM limits gratuitos.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Factorio Cleaning Runner"
    }
    
    prompt = f"""
You are a professional theological editor specialized in structuring classic texts and sermons.
Your task is to take the following draft text and format it into clean, perfectly readable Markdown.
The current text is too monolithic and poorly formatted. Please:
- Add appropriate headers if the text has clear divisions (use ## for main sections, ### for sub-topics).
- Organize the paragraphs in a fluid, natural, and solemn way.
- Remove any remnants of scrap garbage, page numbers, or navigation links that the pre-cleaning script might have missed.
- Fix orphaned line breaks (e.g., words split by a hyphen at the end of the original physical line that cut sentences in the middle).
- CRITICAL: Preserve the original language of the text. Do NOT translate the text. If the input text is in English, the output Markdown MUST be in English.
- Do NOT include the main title of the sermon/chapter as a # or ## header at the very beginning of the output, as the application already renders the title automatically from the database. Start directly with the first subtitle, introductory text, or Bible verses.
- Return strictly the formatted Markdown of the sermon/book. Do NOT add assistant notes, introductory explanations, or closing remarks. The output must contain ONLY the structured text in si.

Title: {title}
Text:
{text}
"""

    models = ["meta-llama/llama-3.1-8b-instruct"]
    last_err = None
    
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  💬 Enviando para OpenRouter ({model}) - Tentativa {attempt+1}/{max_retries}...")
                response = requests.post(url, headers=headers, json=payload, timeout=40)
                
                if response.status_code == 200:
                    res_json = response.json()
                    content_out = res_json['choices'][0]['message']['content'].strip()
                    if content_out.startswith("```markdown"):
                        content_out = content_out[11:].rstrip("`").strip()
                    elif content_out.startswith("```"):
                        content_out = content_out[3:].rstrip("`").strip()
                    return content_out, model
                else:
                    last_err = f"API Error {response.status_code}: {response.text}"
                    print(f"  ⚠️ Erro do OpenRouter ({response.status_code}): {response.text}", file=sys.stderr)
                    break
            except Exception as e:
                last_err = str(e)
                print(f"  ⚠️ Erro de rede na chamada do OpenRouter: {e}. Aguardando 5s...", file=sys.stderr)
                time.sleep(5)
                
    raise Exception(f"Falha na estruturação com OpenRouter. Último erro: {last_err}")

def clean_and_structure_with_ai(text, title, groq_key, gemini_key, openrouter_key):
    """
    Função de conveniência que roteia de forma inteligente o texto para a IA ideal.
    OpenRouter é a primeira opção por estabilidade e tamanho do limite de TPM.
    """
    if openrouter_key:
        try:
            return clean_and_structure_with_openrouter(text, title, openrouter_key)
        except Exception as e:
            print(f"  ⚠️ OpenRouter falhou: {e}. TENTANDO FALLBACKS...", file=sys.stderr)
            
    if len(text) > 8000:
        print(f"  ℹ️ Texto longo ({len(text)} caracteres). Roteando diretamente para o Gemini (1M TPM limit).")
        return clean_and_structure_with_gemini(text, title, gemini_key)
        
    try:
        return clean_and_structure_with_groq(text, title, groq_key)
    except Exception as e:
        print(f"  ⚠️ Chamada do Groq falhou: {e}. Fazendo fallback automático para o Gemini...")
        return clean_and_structure_with_gemini(text, title, gemini_key)

def update_book_progress_in_index(cur, index_id):
    """
    Atualiza o progresso da etapa de estruturação do livro correspondente na INDEX.
    Conta chunks totais e limpos na CONTENT.
    """
    if not index_id:
        return
        
    try:
        # 1. Conta o total e concluídos do livro na content
        cur.execute(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN content IS NOT NULL AND content != '' THEN 1 END) as cleaned
            FROM {TBL_CONTENT}
            WHERE index_id = %s
        """, (index_id,))
        stats = cur.fetchone()
        if not stats:
            return
            
        total = int(stats['total'] or 0)
        done = int(stats['cleaned'] or 0)
        pct = int(round((done / total) * 100)) if total > 0 else 0
        
        # 2. Busca pipeline_state atual na index
        cur.execute(f'SELECT pipeline_state FROM {TBL_INDEX} WHERE __id = %s', (index_id,))
        row = cur.fetchone()
        pipeline_state = row['pipeline_state'] if row and row['pipeline_state'] else {}
        
        # 3. Atualiza ou cria o nó da estruturação no jsonb
        pipeline_state["estruturacao"] = {
            "pct": pct,
            "done": done,
            "total": total,
            "status": "done" if done == total else "pending",
            "updated_at": datetime.now().isoformat()
        }
        
        # Marca a mineração inteira como scraped se a estruturação bateu 100%
        if done == total:
            if "mineracao" not in pipeline_state:
                pipeline_state["mineracao"] = {}
            pipeline_state["mineracao"]["status"] = "scraped"
            pipeline_state["mineracao"]["updated_at"] = datetime.now().isoformat()
            
        cur.execute(f"""
            UPDATE {TBL_INDEX}
            SET pipeline_state = %s::jsonb, __last_modified_time = NOW()
            WHERE __id = %s
        """, (json.dumps(pipeline_state), index_id))
        
        print(f"📈 [INDEX UPDATE] Livro {index_id} atualizado: {done}/{total} limpos ({pct}%)")
    except Exception as e:
        print(f"❌ Erro ao atualizar progresso na INDEX do livro {index_id}: {e}", file=sys.stderr)

def process_single_chunk(chunk, args, groq_api_key, gemini_api_key, openrouter_api_key, modified_books):
    """
    Processa um único chunk de forma isolada, abrindo e fechando conexões locais do Postgres
    para garantir segurança entre concorrência de múltiplas threads.
    """
    chunk_id = chunk["__id"]
    title = chunk["title"] or "Untitled"
    book_name = chunk["book_name"] or "Unknown Book"
    index_id = chunk["index_id"]
    raw_content = chunk["raw_content"]
    
    print(f"\n🔄 Processando: ID: {chunk_id} | Livro: {book_name} | Título: {title}")
    
    # Passo 1: Pré-limpeza via Regex (Filtro Prévio)
    pre_cleaned = pre_clean_text(raw_content)
    
    try:
        # Passo 2: Estruturação Inteligente via IA
        structured, model_used = clean_and_structure_with_ai(pre_cleaned, title, groq_api_key, gemini_api_key, openrouter_api_key)
        word_count = len(structured.split())
        
        # Prepara pipeline_state do chunk
        current_state = chunk["pipeline_state"] if chunk["pipeline_state"] else {}
        current_state["estruturacao"] = {
            "status": "done",
            "model_used": model_used,
            "updated_at": datetime.now().isoformat()
        }
        
        if args.import_db:
            # Cada thread abre e fecha sua própria conexão Postgres para isolar transações
            thread_conn = psycopg2.connect(DB_URL)
            thread_cur = thread_conn.cursor(cursor_factory=RealDictCursor)
            try:
                # Limpa a numeração inicial do título para as colunas do banco
                clean_title = re.sub(r'^\d+\s*-\s*', '', title).strip()
                # Update na content com content e title limpos
                thread_cur.execute(f"""
                    UPDATE {TBL_CONTENT}
                    SET content = %s, title = %s, word_count = %s, pipeline_state = %s::jsonb, __last_modified_time = NOW()
                    WHERE __id = %s
                """, (structured, clean_title, word_count, json.dumps(current_state), chunk_id))
                
                thread_conn.commit()
                print(f"✅ Chunk {chunk_id} estruturado e limpo no banco (Word Count: {word_count}).")
                
                # Registra o livro como modificado para atualizar no final do lote
                if index_id:
                    modified_books.add(index_id)
            except Exception as db_err:
                thread_conn.rollback()
                print(f"❌ Falha ao gravar no banco para o chunk {chunk_id}: {db_err}", file=sys.stderr)
            finally:
                thread_cur.close()
                thread_conn.close()
        else:
            print(f"🧪 [SIMULADO] Chunk {chunk_id} limpo via IA ({model_used}).")
            
    except Exception as e:
        print(f"❌ Falha ao processar o chunk {chunk_id}: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Runner de estruturação e limpeza inteligente de conteúdo via Groq.")
    parser.add_argument("--dry-run", action="store_true", help="Faz apenas a simulação em dry-run de 1 chunk sem salvar no banco.")
    parser.add_argument("--limit", type=int, default=10, help="Limite de chunks a serem processados nesta rodada.")
    parser.add_argument("--import-db", action="store_true", help="Realiza a alteração e o update real no banco de dados.")
    parser.add_argument("--concurrency", type=int, default=5, help="Número de threads simultâneas para processamento em paralelo.")
    args = parser.parse_args()

    # Carrega credenciais do .env
    env = load_env(ENV_PATH)
    groq_api_key = env.get("GROQ_API_KEY")
    gemini_api_key = env.get("GEMINI_API_KEY")
    openrouter_api_key = env.get("OPENROUTER_API_KEY")
    if not openrouter_api_key and not groq_api_key and not gemini_api_key:
        print("❌ Nenhuma chave de API (OPENROUTER_API_KEY, GROQ_API_KEY, GEMINI_API_KEY) encontrada no arquivo .env!")
        sys.exit(1)

    # Conecta no Postgres para busca inicial
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    modified_books = set()

    try:
        # Busca chunks que têm raw_content mas têm content vazio ou nulo
        cur.execute(f"""
            SELECT __id, title, book_name, index_id, raw_content, pipeline_state
            FROM {TBL_CONTENT}
            WHERE raw_content IS NOT NULL 
              AND raw_content != '' 
              AND (content IS NULL OR content = '')
            ORDER BY __id ASC
            LIMIT %s
        """, (args.limit,))
        
        pending_chunks = cur.fetchall()
        print(f"📥 Encontrados {len(pending_chunks)} chunks pendentes de estruturação/limpeza.")
        
        # Fecha cursor e conexões iniciais antes de disparar as threads para evitar deadlocks de idle
        cur.close()
        conn.close()
        
        if not pending_chunks:
            print("🎉 Nenhum chunk pendente de estruturação. A esteira está limpa!")
            return

        if args.dry_run:
            print("🧪 --- MODO DRY-RUN ---")
            process_single_chunk(pending_chunks[0], args, groq_api_key, gemini_api_key, openrouter_api_key, modified_books)
            return

        # Execução Real Paralelizada via ThreadPoolExecutor
        from concurrent.futures import ThreadPoolExecutor
        concurrency = args.concurrency
        print(f"⚡ Iniciando processamento paralelo com {concurrency} threads...")
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(process_single_chunk, chunk, args, groq_api_key, gemini_api_key, openrouter_api_key, modified_books)
                for chunk in pending_chunks
            ]
            # Aguarda a conclusão de todas as threads
            for fut in futures:
                fut.result()

        # Atualiza a INDEX de forma consolidada ao final de todo o lote
        if args.import_db and modified_books:
            print(f"\n📈 Atualizando progresso na INDEX de {len(modified_books)} livros modificados...")
            update_conn = psycopg2.connect(DB_URL)
            update_cur = update_conn.cursor(cursor_factory=RealDictCursor)
            try:
                for book_id in modified_books:
                    update_book_progress_in_index(update_cur, book_id)
                update_conn.commit()
                print("✅ Progresso dos livros atualizado na INDEX com sucesso!")
            except Exception as index_err:
                update_conn.rollback()
                print(f"❌ Erro ao atualizar progresso consolidado na index: {index_err}", file=sys.stderr)
            finally:
                update_cur.close()
                update_conn.close()

    finally:
        pass

if __name__ == "__main__":
    main()
