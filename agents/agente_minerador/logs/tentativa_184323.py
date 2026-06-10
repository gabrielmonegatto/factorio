from bs4 import BeautifulSoup
import requests

# URL da página
url = 'https://www.stempublishing.com/authors'

# Headers para simular um navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Opções da requisição
options = {
    'headers': headers,
    'timeout': 10,  # Timeout de 10 segundos
    'allow_redirects': True  # Permitir redirecionamentos
}

# Realiza a requisição HTTP
try:
    response = requests.get(url, **options)
    # Verifica se a requisição foi bem sucedida
    if response.status_code == 200:
        # Parseia o conteúdo HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Encontra todos os elementos que contêm os autores
        autores = soup.find_all('a', href=True)

        # Filtra apenas os links que são autores
        autores_links = [a['href'] for a in autores if '/authors/' in a['href']]

        # Remove duplicados
        autores_links = list(set(autores_links))

        # Exibe os links dos autores
        for link in autores_links:
            print(link)
    else:
        print('Erro ao acessar a página:', response.status_code)
except requests.exceptions.RequestException as e:
    print('Erro na requisição:', e)