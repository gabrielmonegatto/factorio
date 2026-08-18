# ⛏️ Esteira de Mineração Mananciall

> Sistema que transforma o plano de catálogo (202 obras no Notion) em texto bruto no nosso banco.
> Criado em 18/08/2026. Código: `scripts/mining/`. Companheiro dos docs 13 (estratégia) e 14 (mapa de obras).
> **A vitória desta fase**: ter o conteúdo no nosso banco. Limpeza e edição são fase seguinte (e já existem: ver "Onde isto entrega").

---

## O comando

```bash
node scripts/mining/run.mjs --limite 15
```

Roda a esteira inteira: fila → resolve → minera → painel. Toda etapa é idempotente: repetir é seguro, não duplica.

Etapas avulsas, quando precisar de controle fino:

```bash
node scripts/mining/queue.mjs                    # Notion -> fila no D1
node scripts/mining/resolve.mjs --limite 200     # descobre a URL de cada obra
node scripts/mining/mine.mjs --limite 20         # busca, extrai e grava
node scripts/mining/mine.mjs --obra 42           # uma obra específica
node scripts/mining/mine.mjs --fonte ccel        # só de uma fonte
node scripts/mining/status.mjs --falhas --fracas # o que precisa de decisão humana
```

## Onde cada coisa mora

| Camada | Casa | Por quê |
|---|---|---|
| **Plano** (o que minerar, prioridade) | Notion `Biblioteca Mananciall` | painel humano; o Gabriel manda aqui |
| **Fila e estado** | D1 `mananciall-mining`, tabela `works` | a máquina precisa de estado consultável |
| **Texto bruto minerado** | D1 `mananciall-mining`, tabela `chapters` | separado da produção de propósito |
| **Diário de execução** | D1 `mananciall-mining`, tabela `runs` | saber o que aconteceu sem adivinhar |
| **Produto à venda** | D1 `mananciall-db` (outro banco) | mineração não encosta em produção |

Banco de mineração: `mananciall-mining` (`b08c9fae-3692-409a-aebd-e9630ca66f1d`), conta Eternall.
Escolhido separado da produção porque texto bruto é lixo industrial: pesa, muda, e não pode
disputar espaço nem risco com os 54 MB do banco que serve o site.

Acesso por API HTTP do D1 (não pelo wrangler): permite **parâmetro vinculado**, então texto de
livro entra sem escapar aspas na mão. Escapar SQL com texto de 700 KB é bug garantido.

## O ciclo de vida de uma obra

    queued ──resolve──► resolved ──mine──► mined
       │                   │                 │
       └── sem URL ────────┘                 └─ Notion vira "Limpando"
                    │
                    ├── failed  (fonte fora do ar, 0 capítulos, sem adapter)
                    └── blocked (domínio público não confirmado)

O Notion reflete o resultado: obra minerada vira **Estado = Limpando** no painel. Se o painel
não acompanha a esteira, ele mente pro Gabriel, e painel que mente é pior que painel nenhum.

## As fontes (e o que cada uma entrega)

| Fonte | Formato | Corte de capítulo | Qualidade |
|---|---|---|---|
| **CCEL** | ThML (XML) em `<url>.xml` | `<divN title="...">`, explícito | ⭐⭐⭐ o melhor: capítulo vem marcado com título |
| **Project Gutenberg** | texto puro | convenção tipográfica (`CHAPTER I`) | ⭐⭐ bom; resolve sozinho pela API gutendex |
| **New Advent** | HTML | não tem | ⭐ documento único; o corte fica pra fase de limpeza |

### CCEL: escolher o nível de divisão certo

O `div1` do ThML é capítulo em obra simples, mas é **livro** em obra com partes. A Imitação de
Cristo saiu com 5 peças de 64 KB antes do ajuste. Hoje a esteira desce de nível enquanto a
mediana das peças passar de 25 KB: a mesma obra agora sai com 116 capítulos de ~2,5 KB.

## As três travas (aprendidas apanhando, nesta ordem)

### 1. Similaridade normalizada pelo MAIOR conjunto

A primeira versão normalizava pelo menor. Resultado: `On Prayer` (1 palavra útil) casava **1.00**
com `With Christ in the School of Prayer`, e a esteira minerou um documento dos Padres da Igreja
achando que era Andrew Murray. Texto errado no banco é pior que banco vazio, porque parece certo.

### 2. Casamento exige autor concordando

Título parecido não basta: `aceitavel()` só deixa passar se o autor bater (≥0,3) **ou** o título
for quase idêntico (≥0,9). Sem isso, obra de século errado entra sem ninguém perceber.

Casamento com nota abaixo de 0,7 **não avança sozinho**: fica marcado `FRACO: confirmar na mão`
e aparece em `status.mjs --fracas`.

### 3. Trava de direito autoral no minerador

Antes de gravar qualquer coisa, o minerador procura marca de tradução moderna
(`newly translated`, `translated and edited by`, `copyright 19xx/20xx`). Achou, a obra vira
`blocked` e **não** é gravada.

Isso pegou um caso real: **as Confissões de Agostinho no CCEL são a tradução Outler de 1955**,
protegida por direito autoral. O mapa (doc 14) manda usar Pusey 1838. Sem essa trava, a esteira
teria minerado obra alheia com a maior naturalidade.

**A trava não vale pro Gutenberg**: todo arquivo de lá carrega o aviso de licença da própria PG
("Copyright (C) 2002" da edição eletrônica) e o acervo deles é domínio público nos EUA por
definição. Checar o texto cru ali barrava obra legítima (aconteceu com Brother Lawrence).

## Educação com as fontes

`fetchPolido()` identifica quem somos (User-Agent com o domínio), espera intervalo mínimo por
host, e faz retry com espera crescente em 429/5xx. As três fontes são acervos sem fins
lucrativos que nos dão o insumo do negócio de graça: martelar em paralelo é o jeito rápido de
tomar bloqueio e perder a única via de acesso.

## Onde isto entrega

A mineração para no texto bruto, de propósito. A limpeza já existe e vive no repo do site
(`apps/eternall/mananciall-site`): `scripts/editar.mjs`, com `source_md` (extração crua, nunca
reescrita) e `content_md` (saída da esteira de edição), portão que compara letra por letra.

**A ponte ainda não está construída**: falta o passo que promove obra `mined` do banco de
mineração pra `books` + `chapters.source_md` na produção. É a próxima peça.

## Primeira corrida real (18/08/2026)

| | |
|---|---|
| Obras na fila | 175 (as 202 do plano menos as 27 já publicadas) |
| **Mineradas** | **24 obras · 231 capítulos · 14,0 M caracteres** |
| Falhas visíveis | 1 |
| Bloqueadas por direito autoral | 1 |
| Sem URL (não resolveram) | 149 |

Volumes que entraram: A Cidade de Deus (22 caps, 2,4 M), Charnock (8 partes, 3,8 M),
Contra Celso (1,3 M), História Eclesiástica de Eusébio (817 K), A Imitação de Cristo
(114 caps), Catecheses de Cirilo (24 caps, 599 K), Homilias de Crisóstomo em Gálatas,
Sobre o Sacerdócio, A Regra Pastoral de Gregório Magno.

**O gargalo não é minerar, é resolver.** 149 das 175 obras não acharam URL. Não é falha
de código: é que o `content_index` só cobre 545 obras (CCEL e New Advent) e o Gutenberg
não tem tudo. Aumentar a colheita = alimentar o `content_index` com mais fontes, não
mexer no minerador.

## Limites conhecidos (o que esta fase NÃO resolve)

- **Título de volume não é obra de fonte.** O mapa tem entradas editoriais como
  `On Prayer + On Patience + On Repentance` (três obras num volume). Isso não casa com nenhuma
  fonte, e não deveria: é decisão de empacotamento nossa. Essas obras precisam ser mineradas
  peça por peça e montadas depois.
- **New Advent entrega documento único.** Os Padres saem como um bloco por obra; o corte em
  capítulo fica pra fase de limpeza.
- **Snapshot cru ainda não vai pro R2.** A coluna `raw_key` existe e está vazia. Guardar o cru
  evita re-raspar a fonte e serve de prova de proveniência do domínio público.
- **Obra sem candidato fica parada.** Não inventamos URL: é melhor uma fila honesta com buraco
  do que texto errado no acervo.
- **Extração fina demais passa pelo piso.** O piso de 3.000 chars pega índice óbvio, mas não
  pega o caso intermediário: "On the Trinity" entrou com 6 K quando a obra tem 15 livros.
  Conferir com `status.mjs` quem tem `chars_n` incompatível com o tamanho esperado da obra.
- **Sem adapter pro Archive.org** (21 obras na fila dependem dele).
