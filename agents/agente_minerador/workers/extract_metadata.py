import os
import json
from litellm import completion

def extrair_metadados_pagina(conteudo_limpo: str) -> dict:
    """
    Recebe um texto limpo (com Título, Cabeçalhos e trecho do corpo) 
    e usa a API do Gemini via LiteLLM para extrair Título e Autor em JSON.
    Gasta cirurgicamente 1 token sem overhead de orquestração.
    """
    prompt = f"""
    Você é um assistente cirúrgico de extração de metadados.
    Analise o texto a seguir (raspado da web) e extraia:
    1. O Título principal da obra (title)
    2. O Autor principal (author). Se não houver autor explícito, tente inferir. Se impossível, retorne "Desconhecido".

    Retorne APENAS um JSON válido neste formato exato (sem formatação markdown em volta, apenas o json puro):
    {{"title": "Nome do Livro ou Artigo", "author": "Nome do Autor"}}

    TEXTO A SER ANALISADO:
    {conteudo_limpo}
    """
    
    try:
        # A chave OPENROUTER_API_KEY deve estar configurada no ambiente
        response = completion(
            model="openrouter/deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}]
        )
        conteudo = response.choices[0].message.content.strip()
        
        # Remove blocos de código se o LLM adicionar ```json
        if conteudo.startswith("```"):
            linhas = conteudo.split("\n")
            conteudo = "\n".join(linhas[1:-1])
            
        return json.loads(conteudo)
    except Exception as e:
        print(f"[Extração LLM] Erro: {e}")
        return {"title": "Desconhecido", "author": "Desconhecido", "erro": str(e)}
