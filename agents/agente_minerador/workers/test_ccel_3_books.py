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
        print(f"Erro na autenticação: {e}")
        return False

def clean_element_to_markdown(element):
    import copy
    el = copy.copy(element)
    
    for sref in el.find_all('scripRef'):
        sref.replace_with(sref.get_text())
        
    for note in el.find_all('note'):
        note.replace_with(f" [Nota: {note.get_text().strip()}]")
        
    for i in el.find_all(['i', 'em']):
        i.replace_with(f"*{i.get_text().strip()}*")
    for b in el.find_all(['b', 'strong']):
        b.replace_with(f"**{b.get_text().strip()}**")
        
    for br in el.find_all('br'):
        br.replace_with("\n")
        
    for h in el.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        try:
            level = int(h.name[1])
        except:
            level = 2
        h.replace_with(f"\n\n{'#' * level} {h.get_text().strip()}\n\n")
        
    for p in el.find_all('p'):
        p.replace_with(f"\n\n{p.get_text().strip()}\n\n")
        
    for l in el.find_all('l'):
        l.replace_with(f"\n> {l.get_text().strip()}")
        
    text = el.get_text()
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def get_specific_books(book_ids):
    books = []
    for bid in book_ids:
        url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_CONTENT_INDEX}/{bid}/?user_field_names=true"
        try:
            res = session.get(url, timeout=10)
            if res.status_code == 200:
                books.append(res.json())
            else:
                print(f"❌ Livro ID {bid} não encontrado: {res.text}")
        except Exception as e:
            print(f"❌ Erro ao buscar livro {bid}: {e}")
    return books

def parse_ccel_xml(source_url):
    try:
        parts = source_url.rstrip('/').split('/')
        author_slug = parts[-2]
        book_slug = parts[-1]
    except Exception as e:
        print(f"❌ Erro ao extrair slugs: {e}")
        return None, None, []

    xml_url = f"https://ccel.org/ccel/{author_slug}/{book_slug}.xml"
    print(f"⏳ Baixando XML: {xml_url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(xml_url, headers=headers, timeout=20)
        if res.status_code != 200:
            xml_url = f"https://ccel.org/ccel/{author_slug}/{book_slug}/cache/{book_slug}.xml"
            print(f"⚠️ Tentando cache: {xml_url}")
            res = requests.get(xml_url, headers=headers, timeout=20)
            
        if res.status_code != 200:
            print(f"❌ Erro HTTP {res.status_code}")
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
                    chapters.append({
                        "title": f"{title1} - {title2}",
                        "element": d2
                    })
            else:
                chapters.append({
                    "title": title1,
                    "element": d1
                })
                
        return author_slug, book_slug, chapters
    except Exception as e:
        print(f"❌ Erro no parse: {e}")
        return None, None, []

def delete_existing_chapters(book_id):
    # Opcional: Limpa capítulos antigos deste livro antes do teste
    print(f"🧹 Limpando capítulos antigos do livro [{book_id}] se houver...")
    # Buscamos as linhas que têm index_id correspondente
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_MINERATION_CONTENT}/?user_field_names=true&filter__field_12612__equal={book_id}"
    try:
        res = session.get(url, timeout=10)
        if res.status_code == 200:
            rows = res.json().get("results", [])
            for r in rows:
                session.delete(f"{BASEROW_URL}/api/database/rows/table/{TABLE_MINERATION_CONTENT}/{r['id']}/")
            if rows:
                print(f"✅ {len(rows)} capítulos antigos deletados.")
        else:
            print(f"⚠️ Erro ao listar capítulos antigos: {res.text}")
    except Exception as e:
        print(f"⚠️ Erro de rede ao limpar: {e}")

def insert_chapters_to_baserow(book_id, book_title, book_author, chapters):
    if not chapters:
        return True
        
    print(f"⏳ Inserindo {len(chapters)} capítulos de '{book_title}'...")
    payloads = []
    
    for idx, ch in enumerate(chapters, 1):
        md_content = clean_element_to_markdown(ch["element"])
        word_count = len(md_content.split())
        display_name = f"{book_title} - Cap. {idx:02d}: {ch['title'][:50]}"
        
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
            "raw_content": str(ch["element"])[:20000]
        })
        
    batch_url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_MINERATION_CONTENT}/batch/?user_field_names=true"
    chunk_size = 100
    
    for i in range(0, len(payloads), chunk_size):
        chunk = payloads[i:i + chunk_size]
        try:
            res = session.post(batch_url, json={"items": chunk}, timeout=20)
            if res.status_code != 200:
                print(f"❌ Erro na inserção: {res.text}")
                return False
        except Exception as e:
            print(f"❌ Erro de rede: {e}")
            return False
            
    print(f"✅ Inseridos {len(chapters)} capítulos!")
    return True

def update_book_status(book_id, status="scraped"):
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_CONTENT_INDEX}/{book_id}/?user_field_names=true"
    payload = {
        "status": status,
        "scraped_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    try:
        session.patch(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ Erro status PATCH: {e}")

def main():
    if not baserow_auth():
        return
        
    # As 3 obras de teste:
    # 178 = Pilgrim's Progress (John Bunyan)
    # 1227 = Imitation of Christ (Thomas a Kempis)
    # 48 = Confessions of Saint Augustine (Saint Augustine)
    target_ids = [178, 1227, 48]
    
    books = get_specific_books(target_ids)
    
    for book in books:
        book_id = book.get("id")
        book_title = book.get("Name") or book.get("title") or "Sem Título"
        book_author = book.get("author") or "Desconhecido"
        source_url = book.get("source_url")
        
        print(f"\n🚀 TESTE ETL para [{book_id}] '{book_title}'...")
        
        if not source_url:
            print(f"⚠️ URL indisponível")
            continue
            
        delete_existing_chapters(book_id)
        author_slug, book_slug, chapters = parse_ccel_xml(source_url)
        
        if not chapters:
            print(f"❌ Sem capítulos para processar.")
            continue
            
        success = insert_chapters_to_baserow(book_id, book_title, book_author, chapters)
        if success:
            update_book_status(book_id, "scraped")
            print(f"🎉 Sucesso total para '{book_title}'!")
        else:
            print(f"❌ Falha ao inserir capítulos.")
            
        time.sleep(2)

if __name__ == "__main__":
    main()
