# Entrevista — criar-skill (2026-07-10)

Skill meta: porta o método da fábrica para qualquer sessão. A entrevista foi curta porque a matéria-prima é a própria fábrica (CLAUDE.md + references/), já validada por 9 skills instaladas com testes cegos 100% aprovados.

## Origem
Pedro pediu comparação entre o método da fábrica e a skill-creator oficial da Anthropic (repo `anthropics/skills`, 485 linhas). Veredito:
- **Fábrica vence no método** (o que faz a skill nascer boa): entrevista de 8 blocos vs 4 perguntas genéricas; fórmula de description com frases literais + trigger negativo vs "seja pushy"; pares certo/errado por modo de falha; pipeline de livros → destilado (a oficial não tem nada equivalente); ≤150 linhas vs ≤500; loop de manutenção (erro em produção vira exemplo errado).
- **Oficial vence na medição**: baseline com/sem skill (prova que a skill agrega) e eval de gatilho com near-misses realistas. O resto da infra dela (viewer HTML, benchmark quantitativo, grader, otimizador automático de description) é overkill para o volume do Pedro.

## Decisões (com porquê)
1. **Escopo = método da fábrica + 2 ideias roubadas da oficial** (baseline e near-misses) — custo de ~30% mais tempo por skill, benefício permanente: prova de valor agregado e proteção contra colisão de gatilho nas 40+ skills instaladas.
2. **Detecção automática da fábrica** — se `/Volumes/KINGSTON/claude/tools/skill-creator/` (ou `Kingston`) existir, desenvolve lá (entrevista e destilado arquivados no acervo); senão, modo standalone (rascunho em pasta temporária → instala em `~/.claude/skills/` com TESTES.md junto). Sem pergunta extra por sessão.
3. **A skill vira a fonte única do método** — o CLAUDE.md da fábrica encolhe para ~15 linhas (acervo + ponteiro para a skill). Motivo: método duplicado em 2 lugares diverge inevitavelmente; contraria a regra de ouro da própria fábrica.

## Gatilhos (bloco 2)
- "cria uma skill", "quero uma skill que...", "transforma isso numa skill", "vira skill"
- "melhora a skill X", "conserta a skill X", "a skill X errou"
- NÃO disparar para: configuração do harness/hooks/permissões (update-config), criação de subagentes (.claude/agents/), skills de projetos BMAD (copy-master etc., anatomia diferente).

## Barra de qualidade (bloco 3)
A mesma da fábrica: skill só está pronta quando passa nos testes cegos, no baseline e no teste de gatilho. Erro inaceitável: skill que dispara errado (colisão silenciosa com skill vizinha) ou que incha contexto sem agregar sobre o Claude puro.
