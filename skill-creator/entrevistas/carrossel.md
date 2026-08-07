# Auditoria/adoção — carrossel (2026-07-07)

**Origem:** skill criada pelo Pedro FORA da fábrica (2026-07-06), validada por 3 builds reais no Desaign (designs 64 "Prompt IA", 68 "Hermes Agent", 70 "Vaca Roxa"). Auditada contra os padrões da casa a pedido dele e adotada pela fábrica.

**O que já estava excelente (mantido):** scripts determinísticos (`check-image.py` com detectores de xadrez assado e miolos brancos; `punch-counters.py`), armadilhas de guerra documentadas, princípio "pense como designer: mínimo de imagens, máximo nativo", template de build funcional.

**Melhorias aplicadas (plano aprovado em `~/.claude/plans/muito-bom-agora-cheeky-kay.md`):**
1. Description no padrão da casa: TRIGGER com frases literais + desambiguação tripla (Desaign ≠ ZOAC create_carousel ≠ write-carousel/copy) + "pedido ambíguo → pergunte".
2. Seção "Regras duras" (8) promovida pro topo — antes espalhadas pelos passos.
3. `references/armadilhas.md` criado: bestiário em formato ❌/✅ com porquê (9 pares) + válvula de crescimento ("aprendizados novos entram LÁ, não no SKILL.md").
4. Caminhos dos scripts corrigidos de relativo pra absoluto (~/.claude/...).
5. Graus de liberdade explícitos (Fixo vs Livre).
6. Fronteira de escopo: "esta skill NÃO escreve o conteúdo do carrossel".
SKILL.md: 147 → 150 linhas (conteúdo pesado movido, regras promovidas).

**Testes (2026-07-07):** caminho feliz já validado pelos 3 builds reais; testes de borda em subagentes cegos:
- T1 gatilho ambíguo ("faz um carrossel"): ✅ perguntou qual dos 3 caminhos (Desaign/ZOAC/copy), não inventou copy, pediu insumos.
- T2 sem token/workspace: ✅ adiantou a análise do passo 1 (que não depende de credencial), identificou o token como único bloqueio real, pediu o token E confirmou se o roteiro/copy vem pronto (fronteira de escopo funcionando).
- T3 referência com texto rasterizado na imagem: ✅ decompôs tudo em nativo (título, parágrafos, anotação Caveat + shape line), 2 imagens para 4 slides, regras duras citadas uma a uma.

3/3 — nenhuma correção necessária após os testes.

**Pendências:** —
