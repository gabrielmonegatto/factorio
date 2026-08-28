# 23 · Magnific como plataforma audiovisual da fábrica (tese pra decisão)

**Status:** tese pronta, aguardando o Gabriel fechar o Premium+ (mês que vem).
**Escopo:** TODA a geração audiovisual da fábrica, exceto VOZ (TTS segue onde está).
**Data:** 25/08/2026 · Fontes: magnific.com/pricing e docs.magnific.com lidos na data; conversão BRL→USD a 5,15.

---

## 1. A tese em uma frase

Uma assinatura Premium+ (R$ 135/mês no anual, 600 mil créditos/ano) vira o
fornecedor único de **imagem, vídeo, música, SFX e upscale** da fábrica, com
licença comercial e musical escritas no plano — e aposenta RunPod, a rota OpenAI
de imagem e a rota OpenRouter de trilhas, sobrando o TTS como única peça de
áudio fora dela.

## 2. Por que trocar (números medidos, não folheto)

| frente | como era | custo real medido | pela Magnific | delta |
|---|---|---|---|---|
| clipe de âncora 5s | RunPod + Wan 2.2 5B | **US$ 0,22**/clipe (A6000 real = US$ 1,15/h, não os 0,33 da minha tabela errada) | Kling 2.5 720p: 140 cr ≈ **US$ 0,07** | 3x mais barato, qualidade MUITO acima |
| still do catálogo | CF Workers AI (grátis, teto 10k neurons/dia) ou gpt-image-1 pago | grátis porém estoura / US$ ~0,02-0,07 | 50–150 cr via API; **ilimitado no web app** | web app zera o custo da curadoria |
| trilha original | Lyria 3 via OpenRouter (US$ 0,08/faixa, parado por falta de saldo) | nunca rodou | Lyria 3: 160 cr ≈ **US$ 0,08** + **music rights no plano** | mesmo preço, licença escrita |
| SFX | não tínhamos rota | — | 15 cr / 3s | frente nova de graça |
| upscale 704p→1080p/4K | não tínhamos rota | — | Magnific & Topaz inclusos (custo em cr não publicado) | resolve os shorts em 1080p |
| voz (TTS) | esteira atual | — | **fora da tese** | sem mudança |

A comparação de mercado que sustenta o preço do Kling: fal.ai cobra US$ 0,35 o
mesmo clipe; a API oficial chinesa, ~US$ 0,22 em 720p. A Magnific a ~US$ 0,07 só
é possível porque o crédito é subsidiado pela assinatura.

## 3. A regra de ouro da plataforma (decide TODO o desenho)

> **"Unlimited" só vale DENTRO do web app. Chamada de API sempre consome
> crédito, em qualquer plano.** (docs.magnific.com/pricing, texto literal)

Consequência direta, e é assim que a fábrica deve operar:

- **Esteira automatizada (cron, scripts)** → API → gasta crédito → passa por
  orçamento e teto.
- **Curadoria e exploração do Gabriel** (testar estilo, gerar os ensaios
  ilustrados dos pregadores, iterar imagem até gostar) → **web app, nos modelos
  UNLIMITED, custo zero**. Kling 2.5 720p e Hailuo 2.3 Fast (vídeo); Nano Banana
  2/Pro, Seedream 5.0, Flux.2 Pro (imagem).

Ou seja: o trabalho caro de ACHAR a imagem certa migra pro ilimitado; a API só
executa o que já foi decidido.

## 4. Orçamento de créditos no Premium+ (600k/ano)

| uso | conta | créditos/ano |
|---|---|---|
| fechar a biblioteca de âncoras (26 cenas + 27 variantes anti-repetição) | 53 × 140 | 7.420 (única vez) |
| expansão da biblioteca (200 clipes/ano: cenas novas, 2ª marca Moody) | 200 × 140 | 28.000 |
| trilhas originais (20 faixas/ano, 6 climas + renovação) | 20 × 160 | 3.200 |
| stills novos por API (300/ano — a curadoria pesada vai no web app) | 300 × 75 | 22.500 |
| SFX (200 efeitos/ano) | 200 × 15 | 3.000 |
| **subtotal previsível** | | **~64.000 (11%)** |
| reserva pra upscale de vídeo (custo não publicado — ver §6) | | folga de 536.000 |

Mesmo triplicando tudo, não passa de 33% do plano. **Estourar limite não é
risco realista no nosso volume** — o único item capaz de comer crédito em escala
é upscale de vídeo LONGO, e por isso ele fica fora da esteira até termos o preço
(§6).

Premium (240k, R$ 59/mês) também caberia no subtotal previsível; o Premium+ se
justifica por **music rights** (trilha em canal monetizado) + folga pro upscale.
É a diferença de R$ 76/mês comprando a licença musical e o teto alto.

## 5. O que aposenta, o que fica

| peça | veredito | por quê |
|---|---|---|
| **RunPod (animação Wan)** | **APOSENTADO para âncoras** | 3x mais caro por clipe, qualidade inferior, e foi a fonte dos dois estouros de custo (tabela de preço inventada por mim + 10 minas operacionais). `animar.py` fica no repo como arquivo histórico; conta RunPod fica zerada, sem recarga. |
| RunPod (conta em si) | fica dormente | ainda é a saída para compute que a Magnific não vende (treinar LoRA, batch de outra natureza). Não recarregar sem caso de uso novo. |
| rota gpt-image-1 (OpenAI) | APOSENTADA | Magnific cobre com modelos melhores. |
| CF Workers AI (FLUX stills) | fica como **fallback grátis** | custo zero dentro do teto diário; serve pra rascunho em massa. Curadoria fina migra pro web app ilimitado. |
| Lyria via OpenRouter | APOSENTADA antes de nascer | mesmo preço na Magnific, com music rights no papel. OpenRouter segue sendo só LLM (mineração de clipes, DeepSeek). |
| TTS/voz | **fora do escopo** | exceção definida pelo Gabriel. |
| ffmpeg local (graduar, estabilizar, montar) | fica | pós-produção é nossa, determinística e grátis. |

## 6. Pendências que seguram partes da tese (não a tese inteira)

1. **Custo do video upscaler não é publicado.** Até ter número (suporte ou
   teste medido de 1 vídeo), upscale NÃO entra em esteira automatizada.
2. **Página de direitos de uso devolve 403.** O plano diz "Commercial AI
   license"; o detalhamento sobre YouTube monetizado precisa ser lido pelo
   Gabriel no painel logado antes de escalar publicação.
3. **US$ 0,07/clipe é derivação minha** (R$ 1.620/ano ÷ 600k cr), não preço
   publicado. A validação real é o extrato de créditos após os primeiros usos.
4. **Endpoint de saldo:** a doc só expõe consumo por período
   (`/analytics/team-credit-usage`), não saldo restante confirmado. O
   `animar_magnific.py` já loga custo por execução; conferir contra o painel
   nas primeiras semanas.

## 7. Governança (aprendido a ferro nos estouros de 23-25/08)

- **Preço não verificado é preço inexistente.** A tabela da A6000 que eu
  inventei custou US$ 6,58 e três decisões tomadas com número errado.
- Todo script que gasta crédito nasce com: padrão **não gastar** (flag
  `--confirmar`), **teto por execução** (`--limite`, default 1) e **custo
  impresso no fim**. O `animar_magnific.py` já nasce assim.
- Consumo conferido no painel/analytics **semanalmente** no primeiro mês.
- Conta é do Gabriel; chave vive no `.env`, nunca em chat, commit ou pod.

## 8. Sequência de adoção

1. **Agora (conta de teste):** 1–2 gerações medidas → comparar com o Wan →
   validar contrato da API de ponta a ponta (upload, poll, download, graduação).
2. **Ao fechar Premium+:** gerar as 26 cenas restantes + 27 variantes
   (~7.400 cr), montar a esteira de trilhas (6 climas, 960 cr), migrar a
   geração de stills curados pro web app.
3. **Mês 1:** auditoria de consumo real vs. esta tabela; decidir upscale.
4. **Depois:** ensaios ilustrados dos pregadores no web app ilimitado (Nano
   Banana Pro / Seedream), que era a frente travada pelo custo de imagem.
