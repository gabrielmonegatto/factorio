# Pipeline de Limpeza de Acervos Teológicos (Worker)

## Resumo

Pipeline de limpeza, estruturação literária e curadoria automática de acervos teológicos no Teable/Postgres, alimentando o app de leitura Mananciapp.

**Modelo usado:** Llama 3.1 8B Instruct (via Groq / OpenRouter)
**Resultado:** 5.929 chunks processados, 0 pendências, 100% aproveitamento

## O Problema

Textos brutos (extrações web antigas ou PDFs convertidos por OCR) com:
- Quebras de linha duras (frases cortadas no meio por hifens)
- Lixo residual de OCR/Web (cabeçalhos, botões de navegação como « Prev, Next », caracteres corrompidos)
- Ausência de formatação semântica (textos monolíticos sem subtópicos, citações ou versículos destacados)

## O Pipeline

```
📥 Texto bruto minerado (HTML/PDF/OCR)
   → Chunking em blocos digeríveis
   → Llama 3.1 8B (via Groq/OpenRouter, concorrência 8 threads)
     ├── Cola palavras hifenizadas (quebras de linha de margem)
     ├── Remove lixo (cabeçalhos, botões nav, caracteres corrompidos)
     ├── Estrutura subtópicos e citações
     └── Preserva linguagem original (inglês elisabetano, grafia clássica PT-BR)
   → Chunks reagrupados → Capítulos → Pronto pra publicação
```

## Por Que Llama 3.1 8B

| Critério | Motivo |
|----------|--------|
| **Custo** | Extremamente baixo por milhão de tokens (muitas vezes gratuito via Groq free tier) |
| **Latência** | Inferência veloz → concorrência de 8 threads simultâneas |
| **Qualidade** | Excepcional em "colar" palavras hifenizadas e organizar subtópicos |
| **Preservação** | Mantém a solenidade da escrita e linguagem original sem reescrever ou traduzir |

## Métricas Reais de Produção

| Acervo | Chunks | Resultado |
|--------|--------|-----------|
| "Como Entender a Bíblia" (2.4MB PDF) | 169 chunks → 7 capítulos | Texto limpo, estruturado sob 7 capítulos legítimos |
| Sermões Spurgeon (Vol. 01-63) | 3.398 sermões | Livres de cabeçalhos legados, Markdown perfeito |
| Devocionais Spurgeon (M&E, Faith's Checkbook) | 1.465 leituras | Formatadas e prontas para uso |
| Clássicos Legados (Edwards, Bounds) | 187 capítulos | Estruturação de 6 clássicos que antes estavam zerados |
| **TOTAL** | **5.929 chunks** | **100% processados, 0 pendências** |

## Stack do Pipeline

- **Runner:** Trigger.dev (orquestração)
- **Worker:** Llama 3.1 8B Instruct via Groq/OpenRouter
- **Banco:** Postgres/Teable (base Eternall, tabela content_chunks)
- **Concorrência:** 8 threads paralelas
- **Custo:** Quase zero (free tier Groq)