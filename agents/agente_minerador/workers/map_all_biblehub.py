import os
import requests
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv("C:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://factorio.io")
BASEROW_EMAIL = "gabriel.monegatto@gmail.com"
BASEROW_PASS = "123mudar"
TABLE_ID = 1532

session = requests.Session()

BIBLE_BOOKS = {
    "genesis": 50, "exodus": 40, "leviticus": 27, "numbers": 36, "deuteronomy": 34, 
    "joshua": 24, "judges": 21, "ruth": 4, "1_samuel": 31, "2_samuel": 24, "1_kings": 22, "2_kings": 25, 
    "1_chronicles": 29, "2_chronicles": 36, "ezra": 10, "nehemiah": 13, "esther": 10, "job": 42, 
    "psalms": 150, "proverbs": 31, "ecclesiastes": 12, "songs": 8, "isaiah": 66, "jeremiah": 52, 
    "lamentations": 5, "ezekiel": 48, "daniel": 12, "hosea": 14, "joel": 3, "amos": 9, "obadiah": 1, 
    "jonah": 4, "micah": 7, "nahum": 3, "habakkuk": 3, "zephaniah": 3, "haggai": 2, "zechariah": 14, "malachi": 4, 
    "matthew": 28, "mark": 16, "luke": 24, "john": 21, "acts": 28, "romans": 16, "1_corinthians": 16, 
    "2_corinthians": 13, "galatians": 6, "ephesians": 6, "philippians": 4, "colossians": 4, 
    "1_thessalonians": 5, "2_thessalonians": 3, "1_timothy": 6, "2_timothy": 4, "titus": 3, 
    "philemon": 1, "hebrews": 13, "james": 5, "1_peter": 5, "2_peter": 3, "1_john": 5, "2_john": 1, 
    "3_john": 1, "jude": 1, "revelation": 22
}

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
        print(f"Auth error: {e}")
        return False

def insert_biblehub_index(payloads):
    if not payloads:
        return
    url = f"{BASEROW_URL}/api/database/rows/table/{TABLE_ID}/batch/?user_field_names=true"
    # Baserow allows up to 200 items per batch
    chunk_size = 200
    for i in range(0, len(payloads), chunk_size):
        chunk = payloads[i:i + chunk_size]
        try:
            res = session.post(url, json={"items": chunk}, timeout=15)
            if res.status_code == 200:
                print(f"✅ Inseridos {len(chunk)} registros no Baserow!")
            else:
                print(f"❌ Erro ao inserir lote: {res.text}")
        except Exception as e:
            print(f"Erro de rede ao inserir: {e}")
        time.sleep(0.5)

def map_chapter(book_slug, chapter_number):
    # Pula Genesis 1 porque já inserimos no PoC
    if book_slug == "genesis" and chapter_number == 1:
        return
        
    url = f"https://biblehub.com/{book_slug}/{chapter_number}.htm"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Erro {response.status_code} ao acessar {url}")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        payloads = []
        
        # 1. Capítulo
        payloads.append({
            "url": url, "section": "text", "book": book_slug, "chapter": chapter_number, "status": "pending"
        })
        
        # 2. Seções
        for sec in ['commentaries', 'interlinear', 'sermons', 'lexicon', 'strongs']:
            payloads.append({
                "url": f"https://biblehub.com/{sec}/{book_slug}/{chapter_number}.htm",
                "section": sec, "book": book_slug, "chapter": chapter_number, "status": "pending"
            })
            
        # 3. Versículos
        verses = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if f"/{book_slug}/{chapter_number}-" in href and href.endswith('.htm'):
                try:
                    v_part = href.split(f"/{chapter_number}-")[1].replace('.htm', '')
                    if v_part.isdigit():
                        verses.add(int(v_part))
                except:
                    pass
                    
        for v in sorted(list(verses)):
            payloads.append({
                "url": f"https://biblehub.com/{book_slug}/{chapter_number}-{v}.htm",
                "section": "verse_text", "book": book_slug, "chapter": chapter_number, "verse": v, "status": "pending"
            })
            payloads.append({
                "url": f"https://biblehub.com/commentaries/{book_slug}/{chapter_number}-{v}.htm",
                "section": "verse_commentary", "book": book_slug, "chapter": chapter_number, "verse": v, "status": "pending"
            })
            
        print(f"📖 {book_slug.capitalize()} {chapter_number}: {len(verses)} versículos -> {len(payloads)} URLs")
        insert_biblehub_index(payloads)
        
    except Exception as e:
        print(f"Erro crítico em {book_slug} {chapter_number}: {e}")

def main():
    if not baserow_auth():
        return
        
    # Generate tasks
    tasks = []
    for book, chapters in BIBLE_BOOKS.items():
        for ch in range(1, chapters + 1):
            tasks.append((book, ch))
            
    print(f"🚀 Iniciando mapeamento de {len(tasks)} capítulos...")
    
    # 5 workers to be polite to BibleHub and Baserow
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(map_chapter, b, c) for b, c in tasks]
        for idx, future in enumerate(as_completed(futures), 1):
            if idx % 50 == 0:
                print(f"--- Progresso: {idx}/{len(tasks)} capítulos ---")

if __name__ == "__main__":
    main()
