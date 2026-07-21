# Atribuição Meta → Criativos

Liga cada anúncio do Meta ao PNG do nosso acervo, para responder **"quanto
cada arte gastou e quanto trouxe"**.

## Por que hash perceptual

Não dá para ligar ad → criativo por UTM (a UTM só carrega `utm_campaign`,
resolve no nível de campanha) nem por `image_hash` do Meta (é um hash
próprio deles, não bate com o nosso MD5, porque o Meta reprocessa o PNG em
JPG ao subir para o CDN).

A ponte é o **dHash**: uma miniatura 9×8 em cinza, comparando cada pixel com
o vizinho da direita → 64 bits. Sobrevive a recompressão e resize. Casamos
por distância de Hamming.

## Ordem de execução

```bash
python apply_schema.py                      # 1x — cria meta_ads, meta_insights, creatives.dhash
python creatives_dhash.py                   # 1x — dHash dos 2505 PNGs do acervo
python meta_pull_insights.py --since 2026-01-01 --chunk-days 10
python meta_pull_ads.py --from-insights     # só os ads que rodaram de fato
python meta_match.py --dry-run              # confere antes
python meta_match.py                        # grava os matches inequívocos
```

Depois, o que sobrar ambíguo se resolve na mão em `/admin/meta-match/`.

Rotina diária (candidata a cron no trigger.dev):

```bash
python meta_pull_insights.py --days 7       # reprocessa a última semana
python meta_pull_ads.py --from-insights     # pega ads novos
python meta_match.py
```

Reprocessar os últimos 7 dias todo dia é proposital: o Meta reatribui
conversões por até ~72h, então os números de ontem ainda mudam.

## ⚠️ O pixel manda a compra como evento custom ofuscado

Descoberto em 21/07/2026 e é a coisa mais importante deste diretório.

O evento `Purchase` padrão **parou de disparar em 30/04/2026**. De maio em
diante a compra chega como conversão custom com nome ofuscado:

| Evento custom | O que é |
|---|---|
| `offsite_conversion.fb_pixel_custom.p` | **Purchase** — é o único com valor monetário |
| `offsite_conversion.fb_pixel_custom.i_c` | InitiateCheckout |
| `offsite_conversion.fb_pixel_custom.a_t_c` | AddToCart |
| `offsite_conversion.fb_pixel_custom.quiz_etapa01` | primeira etapa do quiz |

Consequências práticas:

- Ler `offsite_conversion.fb_pixel_purchase` sozinho dá **receita zero** de
  maio em diante. `meta_pull_insights.py` lê os dois e fica com o maior — as
  janelas não se sobrepõem, então não duplica.
- **Nunca** usar `offsite_conversion.fb_pixel_custom` agregado como receita:
  ele soma todos os custom (66 mil eventos em 90 dias contra ~450 compras) e
  infla o ROAS em várias vezes. É preciso o sufixo `.p`, que só aparece nos
  campos `conversions` / `conversion_values` — não em `actions`.
- A conta **Tonaface** ainda usa o `Purchase` padrão; as da Bluue usam o
  custom. Por isso a lógica lê as duas fontes.

## Contas

| account_id | nome | marca |
|---|---|---|
| `act_1363438474022368` | LF 1 - Bluue | bluue |
| `act_3462187117241841` | LF 8 - BLUUE New | bluue |
| `act_1276336571351856` | CA1 - Bluue $ | bluue |
| `act_2794654284238893` | CA2 - Bluue $ | bluue |
| `act_1261729839382630` | Tonaface | tonaface |

Há ~23 mil ads somando as contas, mas só uma fração teve entrega — daí o
`--from-insights`, que evita baixar dezenas de milhares de imagens à toa.

## Gotchas

- `_factorio/.env` é CRLF: `_common.env()` já limpa o `\r`.
- Janela longa com `time_increment=1` no nível de ad faz o Meta responder
  erro 500/código 1 ("reduza o volume"). Daí o `--chunk-days`.
- O D1 é acessado pela REST API direto, **não** pelo wrangler: o wrangler
  local está logado na conta ZOAC, não na Br4nds.
- `.cache/` guarda as imagens baixadas do Meta — reexecução não rebaixa nada.
  Pode apagar à vontade.
- ROAS aqui é **atribuição do pixel do Meta**, não receita real da Flow /
  Hotmart. Para receita real só dá para resolver por campanha (via UTM em
  `data_tracker`), não por criativo. Serve para comparar criativos entre si;
  não é fonte de verdade de faturamento.
