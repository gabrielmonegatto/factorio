import os
import time
import re
import psycopg2
import json
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv("C:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

DB_URL = "postgresql://postgres:postgres@localhost:5432/baserow_app"

def get_db_connection():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SET search_path TO mineration, public;")
    cur.close()
    return conn

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
    print("⏳ Buscando livros ativos e pendentes no Postgres...")
    books = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, title, author, source_url 
            FROM content_index 
            WHERE active = true AND (status IS NULL OR status != 'scraped')
            ORDER BY id
        """)
        rows = cur.fetchall()
        for r in rows:
            books.append({
                "id": r[0],
                "name": r[1],
                "title": r[2],
                "author": r[3],
                "source_url": r[4]
            })
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao buscar livros no banco: {e}")
        
    print(f"📖 Encontrados {len(books)} livros ativos e pendentes para mineração.")
    return books

def parse_ccel_xml(source_url):
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
        import requests
        res = requests.get(xml_url, headers=headers, timeout=20)
        if res.status_code != 200:
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

def insert_chapters_to_postgres(book_id, book_title, book_author, chapters):
    if not chapters:
        return True
        
    print(f"⏳ Inserindo {len(chapters)} capítulos de '{book_title}' no Postgres...")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Deletar capítulos anteriores se houver (para garantir idempotência e recomeço limpo)
        cur.execute("DELETE FROM mineration_content WHERE index_id = %s", (str(book_id),))
        
        for idx, ch in enumerate(chapters, 1):
            md_content = clean_element_to_markdown(ch["element"])
            word_count = len(md_content.split())
            display_name = f"{book_title} - Cap. {idx}: {ch['title'][:50]}"
            
            metadata = {
                "chapter_index": idx,
                "total_chapters": len(chapters),
                "chapter_title": ch['title']
            }
            
            cur.execute("""
                INSERT INTO mineration_content (
                    index_id, title, author, status, content, 
                    word_count, metadata, raw_content, field_1
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(book_id), ch['title'], book_author, "scraped", md_content,
                word_count, json.dumps(metadata), str(ch["element"])[:20000], display_name
            ))
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Todos os {len(chapters)} capítulos inseridos com sucesso no banco!")
        return True
    except Exception as e:
        print(f"❌ Erro ao gravar capítulos no banco: {e}")
        return False

def update_book_status(book_id, status="scraped"):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE content_index 
            SET pipeline_state = jsonb_set(
                COALESCE(pipeline_state, '{}'::jsonb), 
                '{mineracao}', 
                COALESCE(pipeline_state->'mineracao', '{}'::jsonb) || jsonb_build_object(
                    'status', %s::text,
                    'updated_at', NOW()::text
                )
            ), scraped_at = %s
            WHERE id = %s
        """, (status, datetime.utcnow().date(), book_id))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Livro [{book_id}] atualizado como '{status}' no banco.")
    except Exception as e:
        print(f"❌ Erro ao atualizar status do livro [{book_id}] no banco: {e}")

def main():
    books = get_active_pending_books()
    if not books:
        print("✨ Sem pendências de mineração no CCEL.")
        return
        
    for book in books:
        book_id = book.get("id")
        book_title = book.get("name") or book.get("title") or "Livro sem título"
        book_author = book.get("author") or "Autor desconhecido"
        source_url = book.get("source_url")
        
        print(f"\n🚀 Iniciando Processo ETL Nativo para [{book_id}] '{book_title}'...")
        
        if not source_url:
            print(f"⚠️ Livro [{book_id}] não possui source_url. Ignorando.")
            update_book_status(book_id, status="error")
            continue
            
        author_slug, book_slug, chapters = parse_ccel_xml(source_url)
        
        if not chapters:
            print(f"❌ Falha ao processar ou sem capítulos válidos para o livro [{book_id}]")
            update_book_status(book_id, status="error")
            time.sleep(1)
            continue
            
        success = insert_chapters_to_postgres(book_id, book_title, book_author, chapters)
        if success:
            update_book_status(book_id, status="scraped")
        else:
            update_book_status(book_id, status="error")
            
        # Pequeno delay de segurança
        time.sleep(1)

if __name__ == "__main__":
    main()
