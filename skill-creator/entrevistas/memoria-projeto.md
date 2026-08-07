# Entrevista/planejamento — memoria-projeto (2026-07-07)

**A dor:** o /compact perde muito contexto ("não gosto de ficar compactando as conversas"). Pedro quer fechar uma sessão e abrir outra sem perder o fio — memória DO PROJETO, não da conversa.

**O debate (formato: opções apresentadas + investigação empírica):**
1. Mapeamos 3 arquiteturas: só auto-memory / só no projeto / híbrido. Recomendação inicial: híbrido.
2. Pedro levantou o medo certo: "a auto-memory mistura projetos?" → investigação empírica em ~/.claude/projects/ provou que NÃO (128 cofres separados, 1 por pasta) — MAS revelou o problema real: o cofre é amarrado ao CAMINHO literal, e o histórico do Pedro mostra projetos migrando de pasta (~/Claude-Code/ → ~/claude/ → /Volumes/KINGSTON/), com cofres duplicados órfãos.
3. Isso INVERTEU a recomendação: híbrido perde exatamente no padrão de uso real dele (ponteiro fica órfão quando a pasta muda); arquivo no projeto viaja junto.

**Decisões do Pedro:**
1. **Arquitetura:** só no projeto — CONTEXTO.md + sessoes/ na raiz; ponteiro no CLAUDE.md reconferido/recriado a CADA salvamento (fecha a janela da sessão cega).
2. **Formato:** estado + diário — CONTEXTO.md sobrescrito ≤1 página (o que a sessão nova lê) + sessoes/AAAA-MM-DD.md append-only (história).
3. **Modos:** SALVAR + RETOMAR.
4. **Automação:** só manual por enquanto (hook PreCompact fica como evolução futura se sentir falta).

**O insight central do design:** gravar ESTADO (o quê/porquê/o que falta), nunca resumo de conversa — senão vira um /compact manual. As 8 regras duras derivam disso; o Erro 1 dos exemplos é o modo de falha nº 1.

**Testes (2026-07-07): 4/4 em subagentes cegos com projetos-fixture reais.** T1 bootstrap: CONTEXTO de 27 linhas, decisões com porquê, declarou as inferências que fez (regra 7 madura). T2 atualização: pendências resolvidas SAÍRAM, artefato sem função saiu do mapa com raciocínio certo, ponteiro recriado cirurgicamente em CLAUDE.md existente, 28 linhas. T3 retomada: leu SÓ CONTEXTO + último diário (usou ls pra identificar, auditado), briefing no formato. T4 fato pessoal: recusou gravar no CONTEXTO, roteou pra auto-memory citando o Erro 5, e pegou a nuance auto-memory-por-projeto vs CLAUDE.md global. Nenhuma correção necessária.

**Instalada em `~/.claude/skills/memoria-projeto` em 2026-07-07.** Estreia real: contexto da própria fábrica salvo (CONTEXTO.md + sessoes/ + ponteiro no CLAUDE.md deste projeto).

**Pendências:** avaliar hook PreCompact no futuro, se o hábito manual não bastar.
