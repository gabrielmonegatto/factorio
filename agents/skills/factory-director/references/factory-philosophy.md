# Filosofia da Fábrica

Extraído de `factorio_philosophy.md` — principios fundamentais.

## Princípio Central
Um agente ou humano deve entender o estado de qualquer projeto em no máximo 2 consultas ao banco.

## As 3 Camadas
1. **CONTENT** — Matéria-prima e outputs. Dado granular. Cada campo JSONB presente = feito.
2. **INDEX** — Painel de controle por projeto. Estado agregado em JSONB.
3. **TASKS** — Dashboard da fábrica. 1 row = 1 operação de alto nível.

## Runners vs Agentes
- **Runners** — Scripts bobos. Não tomam decisão. Processam próximo chunk, atualizam contadores.
- **Agentes** — LLMs. Decidem "qual livro traduzir?", "o que está travado?", "qual área priorizar?".
- Runner não cria task na TASKS. Agente não executa processamento pesado.

## Mapa das Áreas
```
mineracao/    → importacao, estruturacao, classificacao
inteligencia/ → indexacao, vetorizacao
i18n/         → es/{traducao, revisao}, pt/{traducao, revisao}
produto/      → narracao_{es,pt}, transcricao_{es,pt}, capa, publicacao
channels/     → render_video, upload_youtube, publicacao_social
```