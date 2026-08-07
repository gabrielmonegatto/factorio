# CONTEXTO — Skill Creator (a fábrica de skills)
> Atualizado em 2026-07-10. Última sessão: [sessoes/2026-07-10.md](sessoes/2026-07-10.md)

## O que é este projeto
Fábrica de skills do Pedro para Claude Code: toda skill nova nasce aqui pelo processo de 5 fases (entrevista → matéria-prima → rascunho → teste → instalação em ~/.claude/skills/).

## Estado atual
- ✅ **Pronto:** 10 skills instaladas e testadas — família de quiz completa (quiz-framework-xisto/ask-method/spin-selling + as 3 ads-* correspondentes, com desambiguação cruzada), carrossel (auditada/adotada), memoria-projeto, mover-projeto (2026-07-10). Todos os testes cegos aprovados sem exceção.
- 🔄 **Em andamento:** funil da Juliana Guerra — quiz "Raio-X da Contratação PJ" montado no Quiz Maker (**#56, draft**, 28 etapas, motor de diagnóstico configurado) — parou aguardando as validações da Juliana (pendência 1).
- ⛔ **Bloqueado:** publicação do quiz #56 — depende da Juliana: fórmula de exposição (pag×meses×0,7) e faixas do semáforo, depoimentos reais (loader tem PLACEHOLDERS), order bump "Modelo de Contrato PJ" (existe? criar?), pixel Meta.

## Decisões-chave (com o porquê)
- [2026-07-04] Anatomia de quiz Xisto em **5 fases** (Avatar → Dores e Desejos → Consciência → Cálculo → Personalização), pares dor→alívio FECHADOS — reorganização do Pedro; separa o que o lead já sabe do que o quiz revela.
- [2026-07-04] Skills de ads têm **pipeline rígido**: exigem o blueprint do quiz correspondente e redirecionam blueprint alheio — gancho órfão quebra o loop de personalização.
- [2026-07-05] Família de quiz = **3 frameworks com desambiguação tripla** nas descriptions: Xisto (impulso R$17–27), Ask (segmentação/buckets), SPIN (consultivo, 3 modos). Pedido ambíguo → perguntar qual.
- [2026-07-05] Quiz da Juliana no **Xisto com ângulo de diagnóstico de risco** — R$37 é impulso; ancoragem = Índice de Exposição em R$ calculado com os números do lead.
- [2026-07-07] memoria-projeto mora **só no projeto** (não híbrido) — a auto-memory é amarrada ao caminho literal da pasta e os projetos do Pedro migram de caminho.
- [2026-07-10] mover-projeto: escopo amplo (varre launchd/cron/vizinhos) e fluxo mapear→plano→executar — mexer no ~/.claude.json é o risco nº 1; parte mecânica virou script, não prosa. Detalhe em sessoes/2026-07-10.md.

## Pendências & próximos passos
1. Colher as validações da Juliana pro quiz #56 (fórmula, semáforo, depoimentos, order bump, pixel) → publicar
2. Rodar a leva de ads do Raio-X (`ads-quiz-framework-xisto` + `outputs/quiz-blueprint-raio-x-contratacao-pj.md`) após aprovação do quiz
3. Skill `trafego-low-ticket` — seção 10 do destilado Xisto já mapeada (ABO 1-3-1, orçamento=ticket, sexta→segunda)
4. Avaliar hook PreCompact pra memoria-projeto, se o hábito manual não bastar

## Aprendizados & armadilhas
- **Testes cegos em subagente** (só o pedido + a skill, nada do chat) são o padrão de validação — acham melhorias reais que viram correção (ex.: arbitragem híbrido Xisto×SPIN nasceu de um teste).
- **Auto-memory do Claude = 1 cofre por PASTA** (caminho literal): nunca mistura projetos, mas fragmenta quando o projeto muda de lugar.
- **Resumo (Bookey) ≠ livro integral** — diálogos canônicos e números da pesquisa só existem no integral; sempre extrair do integral quando houver.
- A **description decide o disparo**: frases literais do Pedro + "NÃO usar para X → use Y" entre skills vizinhas ("carrossel" e "quiz" são palavras ambíguas no ecossistema dele).
- Skill adotada de fora (ex.: carrossel) ganha cópia dev + TESTES.md aqui — a fábrica é o ambiente de manutenção de todas.

## Mapa de artefatos
- `outputs/quiz-blueprint-raio-x-contratacao-pj.md` — blueprint aprovado do funil da Juliana; alimenta a pendência 2
- `destilados/` — 3 destilados REUTILIZÁVEIS (xisto-quiz-low-ticket, levesque-ask, rackham-spin-selling)
- `entrevistas/` — decisões e resultados de teste de cada skill (o "porquê" de tudo)
- `skills/` — cópias de desenvolvimento (fluxo de manutenção: consertar aqui → testar → reinstalar)
