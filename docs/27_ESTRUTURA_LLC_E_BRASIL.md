# 27 · Estrutura societária: LLC nos EUA (Stripe, mundo) + CPF/ME no Brasil (Mercado Pago)

Pesquisa de 10/09/2026, duas frentes (EUA e Brasil), fontes oficiais onde havia.
Decisão do Gabriel: Mercado Pago no Brasil, Stripe pelo resto do mundo via LLC;
no Brasil vende como CPF até certo volume e depois abre empresa. Este doc é a
orientação; nada aqui substitui o contador, e o item 0 é obrigatório antes de
gastar um dólar.

## 0. O fato que muda a conta: 15% no Brasil todo ano

A Receita publicou a **Solução de Consulta Cosit 56/2026** (abril/2026): LLC
americana tratada como transparente e com sócio não residente nos EUA é
"regime fiscal privilegiado". Pela Lei 14.754/2023, o lucro da LLC apurado em
31/12 é tributado na sua pessoa física a **15%, sacado ou não**. Vender produto
(renda ativa) não escapa mais: a regra dos 60% de renda passiva deixou de
importar pra LLC.

Consequências:
- A LLC é veículo **operacional** (Stripe, dólar, cliente global), não veículo
  de adiar imposto.
- Todo ano: balanço da LLC em BR GAAP assinado por contador brasileiro, ficha
  de "entidade controlada" na DIRPF, DARF de 15% até maio.
- Depois de pagos os 15%, trazer o dinheiro é isento (só câmbio + IOF 0,38%).
- Opção de "transparência" (art. 8º) é irrevogável e tende a ser pior pra LLC
  operacional: não escolher sem simular com contador.

Fontes: Conjur, Mariz Advogados, Chambarelli, Bastilho Coelho, PDF da SC 56.

## 1. Lado americano

**Estado: Wyoming.** US$ 100 pra abrir, US$ 60/ano, dono não aparece em
registro público, é o estado que banco, Stripe e contador conhecem pra não
residente. Delaware só se o caminho for Stripe Atlas (US$ 300/ano). Florida
expõe o dono. New Mexico economiza US$ 60 e perde familiaridade.

**Abertura:** dois caminhos.

| | Globalfy plano Remote (brasileira, Orlando) | Enxuto: Northwest + contador avulso |
|---|---|---|
| Ano 1 | US$ 998 + US$ 100 estado | US$ 39 + US$ 100 + EIN US$ 200 + 5472 ~US$ 450 |
| Inclui | LLC, EIN, agente, endereço, Form 5472/1120, renovação, ajuda com Mercury, suporte em português | LLC, agente, endereço com scan; 5472 por form5472.online em abril |
| Ano 2+ | ~US$ 1.060 | ~US$ 760 |

Recomendação: Globalfy Remote. Um fornecedor só, em português, e a multa de
esquecer o Form 5472 é US$ 25.000. A economia do caminho enxuto (~US$ 300/ano)
não paga o risco.

**EIN sem SSN:** SS-4 por fax pro IRS (internacional 304-707-9471), "N/A" na
linha 7b, passaporte anexo; devolve por fax em ~4 dias úteis quando você
informa fax de retorno. Realista: 1 a 6 semanas.

**Banco:** Mercury como conta principal (Brasil é elegível; precisa LLC + EIN
+ passaporte; não aceita endereço de registered agent como operacional).
Wise Business só como conversor pra BRL. Relay e Brex não atendem (exigem SSN
ou presença física).

**Stripe:** abrir no dashboard com a LLC, EIN, CPF como tax ID do representante
(há campo pra "não sou contribuinte US"), telefone +1, conta Mercury, site
mananciall.org. **Ponto mais incerto do plano:** a política escrita da Stripe
pede endereço físico e não aceita virtual/registered agent; na prática muita
LLC de não residente é aprovada, mas há relatos de fechamento em 2026.
Mitigação: site com histórico (já temos), reembolso claro, volume crescendo
devagar. Plano B: Stripe Atlas (US$ 500, Delaware, fluxo integrado, não
garante aprovação). Plano C: Stripe Brasil PJ (aceita cartão internacional,
liquida em BRL).

**Impostos e obrigações nos EUA:**
- Single-member LLC de não residente = disregarded. Sem funcionário ou agente
  nos EUA fechando contrato, o lucro não paga IR federal. Cliente americano e
  servidor na Cloudflare não criam presença.
- Form 5472 + 1120 pro-forma até 15/04 todo ano, por fax ou correio, mesmo com
  zero imposto. Multa US$ 25.000. Aporte e retirada são "transação reportável".
- BOI do FinCEN: LLC formada nos EUA está isenta em definitivo (regra final de
  14/08/2026). Nada a entregar.
- Sales tax: só ao cruzar nexus (US$ 100k ou 200 transações na maioria dos
  estados). Ano 1: nenhum.
- Stripe Tax (0,5%/transação) ligado desde o dia 1. VAT na UE desde a primeira
  venda B2C: registro Non-Union OSS (Irlanda), trimestral; UK separado (20%).
  Stripe calcula, quem declara é você ou parceiro (Taxually, Marosa). Registrar
  só quando as vendas UE/UK pagarem o parceiro.
- ITIN (Form W-7): não é obrigatório, mas sem ele o "Register for me" do Stripe
  Tax e a Relay ficam fechados. Tirar no ano 1 se for escalar.

## 2. Lado brasileiro

**Vender como CPF é legal.** Não existe "limite de 3 mil": é folclore. O que
existe é a obrigação de lançar no Carnê-Leão Web todo mês (DARF 0190 até o
último dia útil do mês seguinte) e a tabela progressiva com o redutor da Lei
15.270/2025: renda tributável total até **R$ 5.000/mês paga zero**.

| Receita/mês | IR (só essa renda) |
|---|---|
| até R$ 5.000 | R$ 0 |
| R$ 6.000 | ~R$ 560 |
| R$ 7.350 | ~R$ 1.110 |
| R$ 10.000 | ~R$ 1.840 |

Mercado Pago aceita CPF pra tudo, inclusive Assinaturas (4,99% na hora, 3,99%
em 30 dias). Risco de vender como PF é só patrimonial (responde com o pessoal)
e de não emitir nota.

**Ponto de virada: ~R$ 7.500/mês por três meses.** Aí abre **ME no Simples**
(não MEI: MEI não pode ser sócio de outra empresa, e a leitura majoritária
inclui empresa no exterior; abrir a LLC derruba o MEI). CNAE 5811-5/00 edição
de livros + 4761-0/01 comércio de livros; e-book no Anexo I com ICMS imune
segregado dá ~2,3% a 2,75% efetivo. Assinatura de leitura a Receita tende a
tratar como serviço (Anexo III, 6% com fator R): separar as receitas. Custo:
contador online R$ 249 a 349/mês + INSS de pró-labore ~R$ 178.

**Livros:** imunidade de impostos alcança e-book (STF, Súmula Vinculante 57);
PIS/COFINS alíquota zero pra livro (Lei 10.865) com extensão a e-book só em
decisões do TRF3. Não muda a conta da PF nem do MEI; no Simples reduz o ICMS.

**Declarar a LLC:** DIRPF, Bens e Direitos grupo 03 código 02, pelo custo em
reais de cada aporte, com os campos de entidade controlada. CBE do Banco
Central só acima de US$ 1 milhão.

**Trazer o dinheiro:** distribuição de lucro (isenta depois dos 15%), com
resolução da LLC de suporte, natureza "distribuição de lucros" no câmbio.
Wise ~1% a 2% + IOF 0,38%; Nomad ou Remessa Online parecidos. Redução legítima
dos 15%: contrato real de serviço da LLC pra você PF até R$ 5.000/mês (IR zero
pelo redutor, despesa na LLC), o resto como lucro.

**Sem royalties entre Brasil e LLC.** Marca e conteúdo em nome do Gabriel PF
(INPI e direito autoral), licenciados por escrito e sem cobrança pra cada
operação; cada empresa atende só o seu mercado. Royalties do Brasil pro
exterior sofrem IRRF 15% + IOF 3,5% e inflam o lucro da LLC: custo duplo.

**Contador:** pacote anual "balanço BR GAAP da LLC + DIRPF com controlada +
DARF", mercado cota US$ 1.500 a 3.000/ano. Escritórios que fazem isso: Shield
International Tax (SP/Miami), La Rocque (RJ), Confirp (SP), DLG Consult,
Master Consultores (SP), PEC Contabilidade (também abre a ME), Brasil Tax.
Contador de bairro não sabe preencher a ficha de controlada.

## 3. Custo do ano 1 (estimado)

| Item | US$ |
|---|---|
| Estado (WY) | 100 |
| Globalfy Remote | 998 |
| Wise Business (USD details) | 31 |
| Telefone +1 e extras | ~150 |
| Contador BR (balanço + DIRPF) | 1.500 a 3.000 |
| **Total** | **~2.800 a 4.300** |

Mais 15% de IR sobre o lucro da LLC e as taxas do Stripe (2,9% + US$ 0,30,
Stripe Tax 0,5%). Ano 2+: ~US$ 1.060 (EUA) + contador BR.

## 4. PLANO OFICIAL (decidido 10/09/2026): abrir com ~R$ 800 e pagar o resto com venda

O Gabriel não tem caixa pra Globalfy ou doola agora. O caminho enxuto é o
oficial: abre barato, começa a vender, e as obrigações que vencem em 2027 são
pagas com a receita. O único erro caro é esquecer o Form 5472 em abril.

**Hoje (custo total ~US$ 139, ~R$ 800):**

| Passo | Onde | Custo | Prazo |
|---|---|---|---|
| 1. Abrir a LLC em Wyoming (nome neutro) | northwestregisteredagent.com | US$ 39 + US$ 100 do estado | 1 a 3 dias úteis |
| 2. EIN sem SSN | SS-4 por fax pro IRS (internacional 304-707-9471), "N/A" na linha 7b, passaporte anexo, informar fax de retorno | grátis | ~4 dias úteis (pode ir a semanas) |
| 3. Conta Mercury | mercury.com com LLC + EIN (carta CP-575) + passaporte | grátis | 1 a 5 dias úteis |
| 4. Contrato de licença dos conteúdos (Gabriel PF → LLC, sem cobrança) | assinar antes da 1ª venda | grátis | 1 dia |
| 5. Stripe pelo dashboard | LLC, EIN, CPF como tax ID do representante, telefone +1, Mercury, mananciall.org; Stripe Tax ligado | grátis, cobra por venda | 1 a 7 dias (revisão) |

**Apto a vender: 2 a 4 semanas** no cenário normal (EIN em ~4 dias + Mercury +
Stripe). Se o IRS demorar, até 8 semanas. Dá pra abrir o Stripe antes do
EIN? Não pelo dashboard comum; só o Atlas permite, e custa US$ 500.

**Depois, pago com venda:**

| Quando | O quê | Quanto |
|---|---|---|
| até 15/04/2027 | Form 5472 + 1120 pro-forma (ex.: form5472.online) | ~US$ 450 |
| abril a maio/2027 | balanço BR GAAP 31/12/2026 + DIRPF com controlada + DARF 15% do lucro | contador BR, US$ 1,5k a 3k (negociar já, pra LLC pequena) |
| setembro/2027 | annual report Wyoming + renovação do agente Northwest | US$ 60 + US$ 125 |

Fazer agora, grátis: conversar com um contador do §2 e fechar preço pra 2027.

## 4b. Ordem de execução (versão completa)

1. Fechar contador brasileiro (§2) e confirmar com ele: Cosit 56/2026, não
   optar por transparência, e a régua de virar ME.
2. Abrir a LLC em Wyoming pela Globalfy Remote; nome neutro. EIN.
3. Mercury com EIN + CP-575 + passaporte. Wise Business depois.
4. Contrato de licença dos conteúdos (PF → LLC), assinado antes da 1ª venda.
5. Stripe pelo dashboard; Stripe Tax ligado; volume gradual. Plano B Atlas.
6. Brasil: seguir como CPF no Mercado Pago com Carnê-Leão mensal; ME quando
   passar de ~R$ 7.500/mês por três meses.
7. Calendário anual: Form 5472 até 15/04 (EUA); balanço 31/12 + DIRPF + DARF
   15% até maio (Brasil); WY annual report no mês de aniversário.
8. Guardar por 5 anos: extratos, DARFs, balanço, resoluções, contratos.

## 5. O que ainda está incerto (checar na semana da abertura)

- Política de endereço da Stripe e da Mercury (mudou duas vezes em 12 meses).
- Se a Globalfy inclui o balanço BR GAAP no Remote (provavelmente não).
- INSS de contribuinte individual sobre serviço prestado a PJ estrangeira.
- Tratamento de assinatura de leitura (serviço x livro) na Receita.
- A Cosit 56 pode ser questionada na Justiça; hoje não há jurisprudência.
  Planejar com os 15%.

Gates humanos: abrir a LLC, contratar contador e mover dinheiro são do Gabriel.
