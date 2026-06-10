from bs4 import BeautifulSoup
import requests

# URL da página
url = 'https://www.stempublishing.com/authors'

# Realiza a requisição HTTP
response = requests.get(url)

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