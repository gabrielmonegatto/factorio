import os
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv("C:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://factorio.io")
BASEROW_EMAIL = "gabriel.monegatto@gmail.com"
BASEROW_PASS = "123mudar"

TABLE_CONTENT_INDEX = 1479  # content_index
TABLE_MINERATION_CONTENT = 1475  # mineration_content

session = requests.Session()

def baserow_auth():
    url = f"{BASEROW_URL}/api/user/token-auth/"
    try:
        response = session.post(url, json={"username": BASEROW_EMAIL, "password": BASEROW_PASS})
        if response.status_code == 200:
            token = response.json()["token"]
            session.headers.update({
                "Authorization": f"JWT {token}",
                "Content-Type": "application/json"
            })
            print("✅ Autenticado no Baserow!")
            return True
        return False
    except Exception as e:
        print(f"Erro na autenticação do Baserow: {e}")
        return False

def clean_element_to_markdown(element):
    import copy
    el = copy.copy(element)
    
    # 1. Converte referências bíblicas
    for sref in el.find_all('scripRef'):
        sref.replace_with(sref.get_text())
        
    # 2. Converte notas de rodapé
    for note in el.find_all('note'):
        note.replace_with(f" [Nota: {note.get_text().strip()}]")
        
    # 3. Converte itálicos e negritos
    for i in el.find_all(['i', 'em']):
        i.replace_with(f"*{i.get_text().strip()}*")
    for b in el.find_all(['b', 'strong']):
        b.replace_with(f"**{b.get_text().strip()}**")
        
    # 4. Converte quebras de linha
    for br in el.find_all('br'):
        br.replace_with("\n")
        
    # 5. Converte cabeçalhos
    for h in el.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        try:
            level = int(h.name[1])
        except:
            level = 2
        h.replace_with(f"\n\n{'#' * level} {h.get_text().strip()}\n\n")
        
    # 6. Converte parágrafos
    for p in el.find_all('p'):
        p.replace_with(f"\n\n{p.get_text().strip()}\n\n")
        
    # 7. Converte versos/poesia
    for l in el.find_all('l'):
        l.replace_with(f"\n> {l.get_text().strip()}")
        
    text = el.get_text()
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def get_active_pending_books():
    print("⏳ Buscando livros ativos e pendentes no Baserow...")
    books = []
    # Usamos paginação de 200 em 200
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_CONTENT_INDEX}/?user_field_names=true&size=200"
    
    while url:
        try:
            res = session.get(url, timeout=15)
            res.raise_for_status()
            data = res.json()
            results = data.get("results", [])
            
            # Filtrar apenas ativos que não foram raspados
            for b in results:
                # Active é True e scraped_at é nulo ou status não é scraped
                is_active = b.get("Active") == True
                is_pending = not b.get("scraped_at") and b.get("status") != "scraped"
                if is_active and is_pending:
                    books.append(b)
                    
            url = data.get("next")
        except Exception as e:
            print(f"❌ Erro ao buscar livros: {e}")
            break
            
    print(f"📖 Encontrados {len(books)} livros ativos e pendentes para mineração.")
    return books

def parse_ccel_xml(source_url):
    # Extrai author_slug e book_slug do source_url
    # Ex: https://ccel.org/ccel/bunyan/pilgrim
    try:
        parts = source_url.rstrip('/').split('/')
        author_slug = parts[-2]
        book_slug = parts[-1]
    except Exception as e:
        print(f"❌ Erro ao extrair slugs do URL {source_url}: {e}")
        return None, None, []

    xml_url = f"https://ccel.org/ccel/{author_slug}/{book_slug}.xml"
    print(f"⏳ Baixando XML do CCEL: {xml_url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(xml_url, headers=headers, timeout=20)
        if res.status_code != 200:
            # Tentar URL alternativa de cache
            xml_url = f"https://ccel.org/ccel/{author_slug}/{book_slug}/cache/{book_slug}.xml"
            print(f"⚠️ URL principal falhou. Tentando alternativa: {xml_url}")
            res = requests.get(xml_url, headers=headers, timeout=20)
            
        if res.status_code != 200:
            print(f"❌ Falha ao baixar XML ({res.status_code}) para {source_url}")
            return author_slug, book_slug, []
            
        soup = BeautifulSoup(res.text, 'xml')
        
        chapters = []
        div1s = soup.find_all('div1')
        
        for d1 in div1s:
            if d1.parent.name == 'ThML.head':
                continue
                
            title1 = d1.get('title') or "Untitled"
            div2s = [d2 for d2 in d1.find_all('div2') if d2.parent == d1]
            
            if div2s:
                for d2 in div2s:
                    title2 = d2.get('title') or "Untitled"
                    full_title = f"{title1} - {title2}"
                    chapters.append({
                        "title": full_title,
                        "element": d2
                    })
            else:
                chapters.append({
                    "title": title1,
                    "element": d1
                })
                
        return author_slug, book_slug, chapters
    except Exception as e:
        print(f"❌ Erro crítico no download/parsing do XML para {source_url}: {e}")
        return None, None, []

def insert_chapters_to_baserow(book_id, book_title, book_author, chapters):
    if not chapters:
        return True
        
    print(f"⏳ Inserindo {len(chapters)} capítulos de '{book_title}' no Baserow...")
    payloads = []
    
    for idx, ch in enumerate(chapters, 1):
        md_content = clean_element_to_markdown(ch["element"])
        word_count = len(md_content.split())
        
        # Nome da linha para visualização limpa
        display_name = f"{book_title} - Cap. {idx}: {ch['title'][:50]}"
        
        metadata = {
            "chapter_index": idx,
            "total_chapters": len(chapters),
            "chapter_title": ch['title']
        }
        
        payloads.append({
            "Field 1": display_name,
            "index_id": str(book_id),
            "title": ch['title'],
            "author": book_author,
            "status": "scraped",
            "content": md_content,
            "word_count": word_count,
            "metadata": re.sub(r'\s+', ' ', str(metadata)),
            "raw_content": str(ch["element"])[:20000] # Limite para não estourar coluna longa do Baserow se for gigante
        })
        
    # Enviar em lotes menores (10) para não estourar a API do Baserow com timeout
    batch_url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_MINERATION_CONTENT}/batch/?user_field_names=true"
    chunk_size = 10
    
    for i in range(0, len(payloads), chunk_size):
        chunk = payloads[i:i + chunk_size]
        try:
            res = session.post(batch_url, json={"items": chunk}, timeout=20)
            if res.status_code != 200:
                print(f"❌ Erro ao inserir lote de capítulos: {res.text}")
                return False
        except Exception as e:
            print(f"❌ Erro de rede ao inserir capítulos: {e}")
            return False
            
    print(f"✅ Todos os {len(chapters)} capítulos inseridos com sucesso!")
    return True

def update_book_status(book_id, status="scraped"):
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_CONTENT_INDEX}/{book_id}/?user_field_names=true"
    payload = {
        "status": status,
        "scraped_at": datetime.utcnow().strftime("%Y-%m-%d")
    }
    try:
        res = session.patch(url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"✅ Livro [{book_id}] atualizado como '{status}' no content_index.")
        else:
            print(f"❌ Falha ao atualizar livro [{book_id}] no content_index: {res.text}")
    except Exception as e:
        print(f"❌ Erro ao enviar PATCH para livro [{book_id}]: {e}")

def main():
    if not baserow_auth():
        return
        
    books = get_active_pending_books()
    if not books:
        print("✨ Sem pendências de mineração no CCEL.")
        return
        
    last_auth_time = time.time()
    for book in books:
        # Renova o token a cada 15 minutos (900 segundos) para não expirar
        if time.time() - last_auth_time > 900:
            print("🔄 Renovando token do Baserow por segurança...")
            baserow_auth()
            last_auth_time = time.time()
            
        book_id = book.get("id")
        book_title = book.get("Name") or book.get("title") or "Livro sem título"
        book_author = book.get("author") or "Autor desconhecido"
        source_url = book.get("source_url")
        
        print(f"\n🚀 Iniciando Processo ETL para [{book_id}] '{book_title}'...")
        
        if not source_url:
            print(f"⚠️ Livro [{book_id}] não possui source_url. Ignorando.")
            update_book_status(book_id, status="error")
            continue
            
        author_slug, book_slug, chapters = parse_ccel_xml(source_url)
        
        if not chapters:
            print(f"❌ Falha ao processar ou sem capítulos válidos para o livro [{book_id}]")
            update_book_status(book_id, status="error")
            # Pequeno delay para evitar estressar o servidor
            time.sleep(2)
            continue
            
        success = insert_chapters_to_baserow(book_id, book_title, book_author, chapters)
        if success:
            update_book_status(book_id, status="scraped")
        else:
            update_book_status(book_id, status="error")
            
        # Delay de cortesia entre livros
        time.sleep(3)

if __name__ == "__main__":
    main()
