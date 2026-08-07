# Entrevista/planejamento — ads-quiz-framework-ask-method + ads-quiz-framework-spin-selling (2026-07-05)

**Contexto:** fechar o pipeline 1:1 — cada framework de quiz com sua skill de anúncios (a ads-xisto já existia).

**Fontes de expertise (destilados reutilizados — zero livro novo):**
- Ask: `destilados/levesque-ask.md`, seção "Landing page de autodescoberta" (gancho em pergunta, número finito, se-então inclusivas, tamanho-único, brincar de médico) — a teoria de persuasão pré-quiz do próprio Levesque, transplantada pra anúncio.
- SPIN: `destilados/rackham-spin-selling.md`, seções 3/6/7 (implicação = linguagem do decisor; features → objeção de preço; pressão derruba venda grande; prevenção de objeções) — regras negativas e positivas do anúncio consultivo por extrapolação documentada dos princípios.

**Decisões do Pedro (via AskUserQuestion):**
1. **Arquitetura:** duas skills novas espelhando a família (não refatorar numa unificada).
2. **Volume:** padronizar 6×3 = 18 nas três skills de ads (simplicidade operacional > número "de fonte" por funil).
3. **Formato SPIN:** mix consultivo — talking head de autoridade, case estruturado, UGC sóbrio, estático de implicação; a skill distribui por estrutura. Ask: expert + UGC de descoberta + estático de pergunta.

**Diferencial de cada uma (a tabela que guiou o design):** Xisto vende o "teste gratuito"+presente (volume/dopamina); Ask vende o DIAGNÓSTICO (curiosidade/pesquisa, gancho sempre pergunta); SPIN vende o PROBLEMA RECONHECIDO (implicação + qualificação embutida, zero pressão, métrica = custo por avanço qualificado, não CPL).

**Padrões herdados da ads-xisto:** pipeline rígido (exige blueprint do framework correspondente + redireciona blueprint alheio), entregável completo (roteiros + prompts IA + copy Meta), mapa anúncio↔porta/bucket/linha da Cadeia.

**Ads-xisto atualizada:** description ganhou a desambiguação de três (dev + instalada).

**Testes planejados (3 por skill):** leva com blueprint fornecido; armadilha sem blueprint; armadilha de blueprint do framework ERRADO (novo tipo de teste — detecção cruzada).

**Testes (2026-07-05): 6/6 aprovados em subagentes cegos.**
- Ask T1 (leva gargalo de agência): 18 ganchos todos em pergunta, N=4 em toda peça, linguagem do Deep Dive literal, guarda-chuva cobrindo os 4 buckets, bucket de 16% coberto por decisão documentada com plano de Leva 2.
- Spin T1 (leva posicionamento odonto): qualificação nos 18 ganchos, mix distribuído (3 talking head + case + UGC sóbrio + estático), case terminando na descoberta ("o que ela descobriu ANTES de decidir"), zero solução/pressão, promessa = entregável do avanço, IA proibida no rosto do expert e da cliente.
- 4 armadilhas (2 sem blueprint + 2 blueprint do framework errado): todas recusaram/redirecionaram; a detecção cruzada funcionou nos DOIS sentidos, identificando o framework alheio pela anatomia (matriz+cupom=Xisto; buckets+diagnóstico=Ask) sem etiqueta.
Nenhuma correção necessária. Outputs preservados em `testes-outputs/` de cada skill.

**Instaladas em `~/.claude/skills/` em 2026-07-05** (sem TESTES.md/testes-outputs). ads-xisto instalada sincronizada com a desambiguação de três.
