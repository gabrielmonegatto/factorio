import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path so imports work
sys.path.append(str(Path(__file__).parent.parent))

from analisador_agent import analyze_brand_funnel

async def main():
    parser = argparse.ArgumentParser(description="Aciona o Agente Analisador de Funil para classificar anúncios campeões.")
    parser.add_argument("--brand", type=str, required=True, help="Nome do player (Hims, Rugiet, Mars Men)")
    parser.add_argument("--limit", type=int, default=10, help="Limite de anúncios campeões a analisar (padrão: 10)")
    
    args = parser.parse_args()
    
    brand = args.brand
    limit = args.limit
    
    print(f"=====================================================")
    print(f"🚀 Iniciando Execução do Agente Analisador de Funil")
    print(f"🎯 Marca Alvo: {brand} | Limite: {limit}")
    print(f"=====================================================")
    
    results = await analyze_brand_funnel(brand, limit)
    
    print("\n=====================================================")
    print(f"✅ Execução Concluída! {len(results)} anúncios classificados.")
    print("=====================================================")
    
    # Generate a brief summary markdown file in the agent folder
    output_report = Path(__file__).parent / f"relatorio_{brand.lower().replace(' ', '_')}.md"
    
    with open(output_report, "w", encoding="utf-8") as f:
        f.write(f"# Relatório de Classificação de Funil - {brand}\n\n")
        f.write(f"Análise executada pelo **Agente Analisador de Funil** para a marca **{brand}**.\n\n")
        
        f.write("## Anúncios Analisados e Classificados:\n\n")
        for ad in results:
            c = ad['classification']
            f.write(f"### Ad {ad['ID']} ({int(ad['Duracao_Dias'])} dias ativo)\n")
            f.write(f"- **Estágio:** {c.get('stage')}\n")
            f.write(f"- **Tipo de Anúncio:** {c.get('type_number')}. {c.get('type_name')}\n")
            f.write(f"- **Razão de Classificação:** {c.get('reasoning')}\n")
            f.write(f"- **Headline:** *{ad['Headline']}*\n")
            f.write(f"- **Gancho:** {ad['Gancho']}\n")
            f.write(f"- **Copy Principal:**\n")
            f.write("```text\n")
            f.write(ad['Copy_Principal'].strip())
            f.write("\n```\n\n")
            
    print(f"✓ Relatório detalhado salvo em: {output_report}")

if __name__ == "__main__":
    asyncio.run(main())
