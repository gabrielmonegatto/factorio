---
name: planejamento-keywords-ads
description: Analisa o site de um cliente, entende o que a empresa vende e entrega um planejamento de palavras-chave para Google Ads no Google Sheets — com volume de busca em três níveis geográficos (Brasil, estado e cidade), concorrência e CPC em reais, mais ideias de keywords relacionadas descobertas via API. TRIGGER quando o Pedro mandar a URL de um cliente no contexto de tráfego pago, ou pedir "analisa esse site pra Google Ads", "faz o planejamento de keywords desse site", "quais palavras-chave esse cliente deveria anunciar", "quanto de busca tem essas palavras". NÃO usar para SEO de conteúdo/blog, análise de concorrente ou auditoria de conta de anúncios.
---

# Planejamento de Keywords — Google Ads

Input: uma URL. Output: planilha no Sheets + leitura estratégica.
Ferramenta: CLI em `/Volumes/KINGSTON/claude/tools/planejador-google-ads` (DataForSEO).

```bash
cd /Volumes/KINGSTON/claude/tools/planejador-google-ads && source .venv/bin/activate
```

## Regras duras

1. **Negócio local → três níveis geográficos**, sempre: **Brasil + Estado + Cidade**. O volume
   nacional engana quem só atende uma cidade — a coluna da cidade é a que decide.
2. **Curar por intenção. Nunca despejar as ideias cruas da API** (elas vêm aos milhares e ~90%
   é lixo). Ver `references/curadoria-por-intencao.md`.
3. **CPC e lances em R$**, nunca em dólar (a API devolve USD).
4. **Entregar com leituras**, não só o link. Planilha sem interpretação é trabalho pela metade.
5. **Máx. 20 palavras-semente** por consulta de expansão (limite da API).

## Workflow

1. **Ler o site**: WebFetch na home + páginas internas (menu/rodapé). Extraia: o que vende
   (lista exaustiva de produtos/serviços), cidade que atende, público.
2. **Sementes**: 15-20 termos a partir dos produtos/serviços REAIS do site. Não invente serviço
   que a empresa não oferece.
3. **Expandir** (1 chamada, ~US$ 0,09), rodando na cidade do cliente:
   ```python
   from planejador.dataforseo import gerar_ideias
   ideias, custo = gerar_ideias(sementes, location_code=<cidade>, language_code="pt")
   ```
4. **Curar** (o passo que dá o valor) → `references/curadoria-por-intencao.md`.
5. **Enriquecer** com variações que a API não sugere sozinha e convertem em negócio local:
   `<serviço> <cidade>`, `<serviço> <sigla do estado>`, `<serviço> perto de mim`,
   `<serviço> preço`, `quanto custa <serviço>`.
6. **Volumes nos 3 geos** (3 chamadas, ~US$ 0,27) — a MESMA lista em cada localidade, para os
   números serem comparáveis:
   ```python
   from planejador.dataforseo import volume_por_keyword
   res, custo = volume_por_keyword(keywords, location_code=<geo>, language_code="pt")
   ```
   Descubra os códigos com `curl .../v3/keywords_data/google_ads/locations/br`.
   Brasil = `2076`. Estado do RJ = `20102`. Cidade do Rio = `1001655`.
7. **Converter USD → BRL**: `https://economia.awesomeapi.com.br/last/USD-BRL`.
8. **Entregar**: use a skill **`planilha-google-sheets`** (ela tem o padrão de formatação e o
   destino `Planejamento de Keywords — Google Ads/<Cliente>/`).
9. **Ler os dados para o Pedro**: 3-5 conclusões acionáveis. Ver "O que reportar" abaixo.

## O que reportar (a parte que ele lê)

Não descreva a planilha — diga o que fazer com ela:
- **Por onde começar**: a keyword com melhor relação volume × intenção × CPC.
- **Armadilhas**: CPC alto com volume ridículo (ex.: "tendas rio de janeiro", R$ 12,44 por 20 buscas).
- **O que NÃO fazer**: segmentação que os dados desmentem (ex.: keywords de bairro deram volume zero
  → não anuncie por bairro, use raio na cidade).
- **Oportunidade escondida**: keyword de volume alto e concorrência baixa que o site não explora
  (ex.: NGN — "design de sobrancelha", 1.900/mês, concorrência 20, e o site nem menciona).
- **Sinal de dinheiro**: CPC alto costuma significar que o concorrente está lucrando ali.

## Custo e limites

~US$ 0,36 por relatório (1 expansão + 3 geos, US$ 0,09 cada). Máx. 12 requisições/min (o motor
já tem retry). Confira o saldo antes com `planejar testar` — e avise o Pedro se estiver baixo.
