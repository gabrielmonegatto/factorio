# Templates da memória do projeto

## CONTEXTO.md (sobrescrito a cada salvamento; ≤1 página / ~60 linhas)

```markdown
# CONTEXTO — [Nome do Projeto]
> Atualizado em AAAA-MM-DD. Última sessão: [sessoes/AAAA-MM-DD.md](sessoes/AAAA-MM-DD.md)

## O que é este projeto
[2 linhas: o que é e qual o objetivo. Estável — só muda se o projeto pivotar.]

## Estado atual
- ✅ **Pronto:** [entregas concluídas relevantes — só as que contextualizam o trabalho atual]
- 🔄 **Em andamento:** [o que está no meio + ONDE exatamente parou ("quiz #56 montado, falta validar fórmula")]
- ⛔ **Bloqueado:** [o quê + POR QUÊ + esperando o quê/quem]

## Decisões-chave (com o porquê)
- [AAAA-MM-DD] [Decisão] — porque [motivo]. [Decisões antigas: comprimir em 1 linha; o detalhe está no diário da data.]

## Pendências & próximos passos
1. [a nº 1 é sempre o próximo passo sugerido na retomada]
2. [...]
[Pendência resolvida SAI da lista — não vira "✓ feito" acumulando.]

## Aprendizados & armadilhas
- [O que descobrimos que não está escrito em lugar nenhum — atalhos, pegadinhas, "não tente X porque Y"]

## Mapa de artefatos
- `caminho/arquivo` — [por que importa]
[Só os que a próxima sessão vai precisar. NÃO é árvore de diretórios.]
```

## sessoes/AAAA-MM-DD.md (append-only; nunca editar sessões passadas)

```markdown
# Sessão AAAA-MM-DD

## O que foi feito
- [entregas/mudanças de estado da sessão, em bullets objetivos]

## Decisões (+ porquê)
- [Decisão] — porque [motivo]. [Alternativa descartada, se relevante.]

## Descobertas
- [aprendizados, armadilhas, surpresas]

## Ficou pra próxima
- [o que estava em curso e parou onde; pendências novas]
```

Se houver mais de uma sessão no mesmo dia, adicione `## Sessão 2 (tarde)` no mesmo arquivo.

## CLAUDE.md mínimo (quando o projeto não tem)

```markdown
# [Nome do Projeto]

[1 linha sobre o que é o projeto.]

> **Memória do projeto:** leia CONTEXTO.md antes de começar qualquer trabalho.
> Ao fechar uma sessão de trabalho, atualize-o (skill memoria-projeto).
```

Se o CLAUDE.md JÁ existe: adicione apenas o bloco de citação acima (no topo, após o título), sem tocar no resto.
