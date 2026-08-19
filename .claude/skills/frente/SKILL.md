---
name: frente
description: Abre uma sessão de área da fábrica (Organização, Inteligência de Mercado, Inteligência do Negócio, Mineração, Content, Productz, i18n) carregando o blueprint, o território de arquivos e as tarefas dela no Notion. Use ao começar a trabalhar numa área específica.
---

# /frente — abrir uma frente de área

**Gatilho:** início de sessão dedicada a uma das 7 áreas da fábrica.
**Input:** nome da área (se não vier, pergunte; não adivinhe).

## Passo a passo

1. **Carregue o desenho.** Leia `docs/16_BLUEPRINT_AREAS.md`: a seção §6.x da área pedida (missão, o que já existe, ondas W0/W1/W2, indicadores, gates, território) e a §7 (regras das frentes em paralelo).
2. **Confirme o território.** O território da área define o que você PODE editar. Precisou de arquivo fora dele: `/handoff-frente`, nunca "aproveitar e mexer".
   - Se o território for um repo de app (`apps/...`), a sessão abre LÁ, não em `_factorio/`.
   - Productz e i18n dividem o repo do site: `git pull` antes de começar, commits pequenos.
3. **Leia o estado do repo:** `git status --short` e `git log --oneline -5`.
4. **Puxe as tarefas da área no Notion:**
   ```
   node tools/notion/notion-tarefas.mjs "<Área>"
   ```
   Traz as tasks abertas e as entregas do Roadmap por onda, separando o que está travado em gate do Gabriel.
5. **Meça antes de planejar.** Rode `node scripts/org/health_check.mjs --seco --verboso`: número medido vale mais que roadmap escrito (em 19/08/2026 o roadmap dizia "canal parado" e o canal estava publicando 1/dia havia uma semana).
6. **Reporte em ≤10 linhas:** área · o que está no ar de verdade · próxima entrega da onda atual · gates travando · 1 sugestão de próximo passo.
7. **Só então execute**, seguindo o ciclo padrão (`docs/02_OPERATING_MODEL.md` §2).

## Ao encerrar a sessão

- Commit no repo da frente (nunca deixar trabalho fora do git).
- Tasks e Roadmap atualizados no Notion (`tools/notion/`).
- Aprendizado virou arquivo: skill ou doc do território.
- Gate que travou você aparece no report, como cobrança ao Gabriel.

## Checklist de pronto (DoD)

- [ ] O blueprint da área foi lido e o território respeitado (nenhum arquivo fora dele foi editado sem handoff).
- [ ] O estado reportado foi MEDIDO (comando rodado), não copiado do roadmap.
- [ ] Notion reflete o que aconteceu na sessão.
- [ ] `git status` limpo no fim.

**Nível de confiança:** 🟡 Draft — execuções limpas: 0/3
