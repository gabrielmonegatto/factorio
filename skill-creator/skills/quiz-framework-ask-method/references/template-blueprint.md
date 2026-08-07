# Template: Blueprint do Quiz Ask Method

Estrutura exata do entregável. Preencha todas as seções; onde não houver dado, escreva a hipótese e marque `[HIPÓTESE]`.

---

```markdown
# Quiz Ask Method — [Mercado/Marca]

## 1. Contexto
- **Mercado/nicho:**
- **Público:**
- **Promessa do diagnóstico** (o que a landing/anúncio promete que o quiz revela):
- **Fonte dos buckets:** dados de pesquisa aberta [descrever] OU hipóteses a validar pelo "Outro"
- **Depois do quiz** (pra onde o lead vai): oferta / lista / conteúdo

## 2. Buckets

| # | Nome do bucket | Problema central (na linguagem do mercado) | % estimado | O que muda na prescrição |
|---|---|---|---|---|
| 1 | | | | |

> Regras: 3–5 buckets, soma ≥ ~80% do mercado, cada linha com prescrição distinta.

## 3. Arquitetura das telas

| Tela | Tipo | Pergunta (resumo) | Variável coletada | Onde a variável é usada |
|---|---|---|---|---|
| 1 | Engraxar as Rodas | | | |
| 2–N | Personalização | | | |
| N+1 | Segmentação | | (bucket) | Página de resultado |
| N+2 | Captura | nome + e-mail | | Follow-up |
| N+3 | Resultado | — | — | — |

> Regras: 6–8 telas no total. Nenhuma célula de "onde é usada" pode ficar vazia.

## 4. Telas (copy completa)

### Tela 1 — Engraxar as Rodas
**Pergunta:**
**Opções:** ( ) A ( ) B
**Nota de design:** binária, sem sobreposição, resposta instantânea.

### Tela 2..N — Personalização
**Pergunta:** (com [colchetes] ecoando resposta anterior, se aplicável)
**Opções:** (consolidadas 80/20; randomizar ordem)
**Lógica condicional:** (se a tela muda conforme resposta anterior, descrever)

### Tela N+1 — Segmentação
**Pergunta:** (recapitulando as respostas anteriores em fraseado natural)
**Opções:** (uma por bucket, 1–2 linhas cada, na linguagem do mercado)
( ) Nenhuma das opções acima ← sempre por último

### Tela N+2 — Captura
**Headline:** (entrega do diagnóstico prometido: "Seu resultado está pronto...")
**Campos:** nome + e-mail
**Microcopy:** (por que pedir o contato, em troca de quê)

## 5. Páginas de resultado (uma por bucket)

### Bucket 1 — [Nome]
- **Rótulo do diagnóstico:** (nome próprio, curioso: "Maldição do Tráfego Frio")
- **Abertura:** agradecer + reconhecer a decisão de responder
- **Diagnóstico:** o que o rótulo significa; sintomas descritos na linguagem do bucket (alvo: "é como se você lesse meu diário")
- **Ponte:** transição para o próximo passo definido no Contexto

(repetir para cada bucket — nenhuma página copiada de outra)

## 6. Checklist de validação
- [ ] Zero venda, preço ou prova social dentro das perguntas
- [ ] 3–5 buckets, todos com prescrição distinta, ~80% de cobertura
- [ ] Tela 1 é binária e trivial; dificuldade cresce tela a tela
- [ ] Toda variável coletada tem uso declarado
- [ ] Segmentação recapitula respostas + tem "Nenhuma das opções acima"
- [ ] Contato só após a última pergunta
- [ ] 6–8 telas
- [ ] N buckets = N páginas de resultado, cada uma com rótulo próprio
- [ ] Pós-lançamento: monitorar % do "Outro" (>10% = repensar buckets)
```
