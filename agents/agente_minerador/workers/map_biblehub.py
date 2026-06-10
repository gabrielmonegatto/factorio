import os
import requests
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv("C:/Users/Monegatto/Desktop/EternalL/_factorio/.env")

BASEROW_URL = os.getenv("BASEROW_URL", "http://factorio.io")
BASEROW_EMAIL = "gabriel.monegatto@gmail.com"
BASEROW_PASS = "123mudar"

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
        print(f"Auth error: {e}")
        return False

def insert_biblehub_index(payloads):
    url = f"{BASEROW_URL}/api/database/rows/table/1532/batch/?user_field_names=true"
    try:
        res = session.post(url, json={"items": payloads})
        if res.status_code == 200:
            print(f"✅ {len(payloads)} registros inseridos no Baserow!")
        else:
            print(f"❌ Erro ao inserir: {res.text}")
    except Exception as e:
        print(f"Erro na requisição: {e}")

def map_chapter(book_slug, chapter_number):
    """
    Mapeia todos os recursos disponíveis no BibleHub para um determinado capítulo.
    Ex: genesis 1
    """
    url = f"https://biblehub.com/{book_slug}/{chapter_number}.htm"
    print(f"\n🔍 Analisando: {url}")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Erro ao acessar {url}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    payloads = []
    
    # 1. Adicionar o próprio capítulo (texto)
    payloads.append({
        "url": url,
        "section": "text",
        "book": book_slug,
        "chapter": chapter_number,
        "status": "pending"
    })
    
    # 2. Descobrir outras seções disponíveis baseando-se na estrutura do BibleHub
    # O BibleHub possui abas no topo: Interlinear, Commentaries, Sermons, etc.
    # Elas seguem o padrão https://biblehub.com/interlinear/{book}/{chapter}.htm
    sections = ['commentaries', 'interlinear', 'sermons', 'lexicon', 'strongs']
    for sec in sections:
        sec_url = f"https://biblehub.com/{sec}/{book_slug}/{chapter_number}.htm"
        # Nós assumimos que elas existem, mas para ser seguro, checamos se o link está no HTML?
        # A abordagem mais rápida é apenas gerar a URL e deixar pro scraper principal lidar com 404s.
        # Porém, vamos verificar se o link correspondente existe no HTML (ex: href="/commentaries/")
        # Mas como a barra de navegação é universal, podemos adicionar todos como pendentes
        payloads.append({
            "url": sec_url,
            "section": sec,
            "book": book_slug,
            "chapter": chapter_number,
            "status": "pending"
        })
    
    # 3. Encontrar todos os versículos do capítulo
    # Ex: /genesis/1-1.htm
    verses = set()
    links = soup.find_all('a', href=True)
    for a in links:
        href = a['href']
        if f"/{book_slug}/{chapter_number}-" in href and href.endswith('.htm'):
            # extrai versículo
            try:
                verse_part = href.split(f"/{chapter_number}-")[1].replace('.htm', '')
                if verse_part.isdigit():
                    verses.add(int(verse_part))
            except:
                pass
                
    print(f"📖 Encontrados {len(verses)} versículos.")
    
    # Para cada versículo, vamos mapear também os comentários individuais
    for v in sorted(list(verses)):
        # Link do versículo
        payloads.append({
            "url": f"https://biblehub.com/{book_slug}/{chapter_number}-{v}.htm",
            "section": "verse_text",
            "book": book_slug,
            "chapter": chapter_number,
            "verse": v,
            "status": "pending"
        })
        # Link do comentário do versículo
        payloads.append({
            "url": f"https://biblehub.com/commentaries/{book_slug}/{chapter_number}-{v}.htm",
            "section": "verse_commentary",
            "book": book_slug,
            "chapter": chapter_number,
            "verse": v,
            "status": "pending"
        })
        
    print(f"📦 Total de links gerados para {book_slug} {chapter_number}: {len(payloads)}")
    
    # Inserir no Baserow
    insert_biblehub_index(payloads)

if __name__ == "__main__":
    if baserow_auth():
        # POC: Mapeando apenas Genesis 1
        map_chapter("genesis", 1)
