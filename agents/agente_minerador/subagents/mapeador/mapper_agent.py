import os
import sys
import subprocess
from pathlib import Path

# Adiciona a raiz do squad ao path para importar as tools
SQUAD_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(SQUAD_DIR))

from agents import Agent, function_tool

def escrever_e_executar_script(nome_arquivo: str, codigo_python: str) -> str:
    """
    Salva um script Python temporário na pasta scratch/ e o executa no ambiente.
    Use para testar conexões, scrapers, ou debugar erros de requisição (como 403).
    Se precisar instalar pacotes extras (ex: cloudscraper, bs4), execute subprocess.run(['pip', 'install', ...]) no início do script.
    A saída do terminal (stdout e stderr) é retornada.
    """
    scratch_dir = SQUAD_DIR / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    file_path = scratch_dir / nome_arquivo
    
    # Salva o arquivo
    file_path.write_text(codigo_python, encoding="utf-8")
    print(f"\n[Sandbox] 📝 Script salvo em: {file_path}")
    
    # Executa usando o interpretador do ambiente atual
    try:
        resultado = subprocess.run(
            [sys.executable, str(file_path)],
            capture_output=True,
            text=True,
            timeout=45,
            encoding="utf-8"
        )
        output = f"--- STDOUT ---\n{resultado.stdout}\n--- STDERR ---\n{resultado.stderr}"
        print(f"[Sandbox] ⚙️ Executado {nome_arquivo} (Status: {resultado.returncode})")
        return output
    except subprocess.TimeoutExpired:
        print(f"[Sandbox] ❌ Tempo limite esgotado executando {nome_arquivo}")
        return "Erro: Execução excedeu o limite de 45 segundos."
    except Exception as e:
        print(f"[Sandbox] ❌ Falha na execução: {e}")
        return f"Erro ao executar: {str(e)}"



# Instância do Agente Mapeador
mapeador_agent = Agent(
    name="Subagente_Mapeador",
    instructions=(
        "Você é o Mapeador especialista da fábrica, atuando como um Scraper Autônomo e Auto-Corretivo (Self-Healing Scraper).\n\n"
        "Sua missão é mapear todos os links/obras/conteúdos de uma determinada URL fonte e cadastrá-los na tabela content_index do Baserow.\n\n"
        "COMO OPERAR:\n"
        "1. Escreva um script Python focado em raspar a URL desejada.\n"
        "2. O script deve extrair itens (Título, Autor e URL da página do item) e imprimi-los em formato JSON no terminal (stdout), no seguinte formato:\n"
        "   [\n"
        "     {\"title\": \"Título da Obra\", \"author\": \"Autor\", \"url\": \"URL da página\"}\n"
        "   ]\n"
        "4. IMPORTANTE REGRAS DE FALHA (FALLBACK): Se a página retornar erro (403, Cloudflare, etc), você DEVE tentar os seguintes 5 métodos em ordem até conseguir:\n"
        "   - Método 1: requests normal com Headers forjados (User-Agent, Accept, etc).\n"
        "   - Método 2: Instalar e usar 'cloudscraper' (`pip install cloudscraper`).\n"
        "   - Método 3: Instalar e usar 'curl_cffi' (`pip install curl_cffi`).\n"
        "   - Método 4: Instalar e usar headless browser ('playwright' ou 'selenium').\n"
        "   - Método 5: Tentar ler sitemaps (`/sitemap.xml`) ou APIs JSON ocultas.\n"
        "   Se um método falhar, invoque a ferramenta `escrever_e_executar_script` NOVAMENTE usando o próximo método.\n"
        "5. Continue tentando até exaurir os 5 métodos. Se TODOS falharem, retorne um JSON vazio [] e um aviso de erro.\n"
        "6. Se tiver sucesso em algum método, analise os dados extraídos e retorne A LISTA JSON COMPLETA como resultado.\n"
    ),
    model="deepseek/deepseek-v4-flash",
    tools=[
        function_tool(escrever_e_executar_script)
    ]
)
