---
name: handoff-frente
description: Encerra uma frente de trabalho registrando handoff auditável (doc + task) para outra sessão continuar sem perder contexto. Use ao encerrar sessão com trabalho incompleto ou ao passar trabalho entre frentes.
---

# /handoff-frente

**Gatilho:** sessão encerrando com trabalho incompleto, ou trabalho mudando de frente.
**Inputs:** frente de origem, frente de destino (se houver), estado do trabalho.

## Passo a passo

1. Escreva o handoff com estas seções obrigatórias:
   - **Estado atual** — o que ESTÁ feito e COMO foi verificado (comando/evidência)
   - **Próximos passos** — na ordem, com o primeiro bem detalhado
   - **Minas e gotchas** — o que pode explodir, o que NÃO fazer
   - **Credenciais/paths envolvidos** — referência ao local (ex.: "`.env` → `META_ADS_TOKEN`"), NUNCA o valor
2. Onde registrar:
   - Decisão/estado técnico da fábrica → `docs/handoffs/AAAA-MM-DD_<frente>.md`
   - Narrativa de negócio → Outline. *Enquanto F1.4 pendente: use `docs/handoffs/` com nota `[MIGRAR→OUTLINE]`.*
3. Task no Teable apontando pro doc. *Enquanto F1.5/F1.6 pendentes: registre em `docs/handoffs/_PENDING.md`.*
4. Commit de tudo que ficou no repo.

## Anti-padrão (lei do `02_OPERATING_MODEL.md` §4)

Handoff que só existe na conversa = trabalho perdido. A outra sessão NÃO vê esta conversa.

## Checklist de pronto (DoD)

- [ ] Doc existe e é autossuficiente (outra sessão retoma sem perguntar nada).
- [ ] Nenhum valor de credencial no doc.
- [ ] Commit feito.

**Nível de confiança:** 🟡 Draft — execuções limpas: 0/3
