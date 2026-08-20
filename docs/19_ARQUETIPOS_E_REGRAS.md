# 🧬 ARQUÉTIPOS, CADÊNCIA, VOZES E FUNIL — as regras da rede

> Decisões do Gabriel em 19/08/2026, formalizadas. Este doc é o que um canal novo
> consulta pra saber "que tipo eu sou e quais regras eu herdo".
> Complementa `18_REDE_TREASURES.md` (a lista de pregadores).

---

## 1. Tabela de arquétipos

Arquétipo é o **produto**, não a relação com outro canal. Spurgeon e Moody são
duas instâncias de TREASURES, não "canal-mãe e réplica".

| Arquétipo | Produto | Duração | Matéria-prima | Meta de instâncias |
|---|---|---|---|---|
| **TREASURES** | sermão histórico narrado na íntegra | 20-40min | sermões/capítulos de um pregador em DP | **10 canais** |
| **WISDOM** | o mesmo sermão condensado no miolo | ≤15min | reaproveita o corpus dos Treasures | 1 por família |
| **AGREGADOR** | compilação temática ou longa por tradição | 1-8h | cruza vários Treasures | 1 por tradição |
| **BÍBLIA** | texto bíblico narrado por blocos | ~60min | KJV/WEB (DP) | 1 por tradução |
| **MÚSICA** | instrumental de hino em DP | 1-3h | hinos pré-1930 + arranjo próprio | 1 a 2 |
| **HISTÓRIAS** | narrativa bíblica contada | a definir | a definir | futuro |

**Regra de ouro entre arquétipos:** derivação é **transformação**, nunca reupload.
O mesmo arquivo de áudio em dois canais é reupload aos olhos do YouTube e derruba
a monetização, mesmo sendo nosso. Cada arquétipo tem que mudar corte, copy, voz
ou formato.

---

## 2. Regras de cadência (a matéria-prima manda)

O erro de fixar "1 por dia" pra todo canal: **o tipo de fonte determina quanto
trabalho de transformação existe, e o volume determina quanto tempo o canal vive.**

### 2.1 Por tipo de matéria-prima

| Tipo de fonte | Transformação necessária | Serve pra | Exemplo |
|---|---|---|---|
| **Sermão pronto** | corte direto, zero reescrita | Treasures | Spurgeon |
| **Livro temático por capítulo** | capítulo vira "sermão": precisa de abertura e fecho editoriais | Treasures | Moody, *Weighed and Wanting* (10 mandamentos) |
| **Tratado contínuo** | exige condensação real; não vira sermão de 30min | **Wisdom**, não Treasures | John Owen |
| **Anedota / história curta** | já nasce curta | **Shorts**, nunca longo | *Moody's Anecdotes* |
| **Carta** | curta e pessoal | Shorts ou agregador | Samuel Rutherford |
| **Texto arcaico (séc. XVII)** | + modernização de grafia (thee/thou) | qualquer | puritanos |

### 2.2 A conta da cadência

```
vida do canal (dias) = itens do acervo ÷ posts longos por dia
```

Regra da casa: **mirar em 6+ meses de vida** antes de o acervo secar.

| Tamanho do acervo | Cadência de longo recomendada |
|---|---|
| até 60 itens | 1 a cada 3 dias |
| 60 a 150 itens | **1 a cada 2 dias** |
| 150 a 300 itens | 1 por dia |
| 300+ | 1 por dia + considerar 2 |

*Aplicado ao Moody (90-120 itens): 1 a cada 2 dias = 6 a 8 meses de vida.*

**⚠️ CORREÇÃO 20/08 (Gabriel):** o Spurgeon tem **~3.500+ sermões** no acervo
histórico (63 volumes do Metropolitan Tabernacle Pulpit). Os 113 são só o que
foi MINERADO até hoje: a extração dos ~51 volumes restantes está parada.
Logo a cadência 1/dia está CERTA pro Spurgeon; o gargalo é a MINERAÇÃO, não o
acervo. A conta de vida usa o acervo REAL da fonte, não o já minerado — e a
fila de mineração precisa correr na frente da fila de publicação.

### 2.3 Equilíbrio com shorts

Shorts saem das anedotas, cartas e trechos aforísticos, que NÃO dão vídeo longo.

- Proporção de partida: **2 a 3 shorts por vídeo longo**
- ⚠️ Short diário com longo a cada 2 dias faz o algoritmo ler o canal como
  "canal de shorts com longos ocasionais". Não é errado, é posicionamento.
  Se o short é porta de entrada pro longo, funciona; se vira o produto, o
  canal muda de identidade sem ninguém decidir isso.
- Isto é hipótese, não lei. Medir e ajustar depois de 30 dias.

---

## 3. Catálogo de vozes (54 gratuitas, licença Apache 2.0)

O Kokoro tem **54 vozes**, não as 8 que a gente tinha em cache. Só de masculinas
em inglês são **13** (9 americanas + 4 britânicas), o que cobre 13 canais com
timbre distinto sem gastar um centavo.

| Idioma | Masculinas | Femininas |
|---|---|---|
| 🇺🇸 EN-US | am_adam, am_echo, am_eric, am_fenrir, am_liam, am_michael, am_onyx, am_puck, am_santa | 11 vozes (af_*) |
| 🇬🇧 EN-GB | bm_daniel, bm_fable, bm_george, bm_lewis | 4 vozes (bf_*) |
| 🇧🇷 PT | pm_alex, pm_santa | pf_dora |
| 🇪🇸 ES | em_alex, em_santa | ef_dora |
| outros | FR, IT, HI, JP, ZH | |

### Alocação (regra: uma voz nunca se repete entre canais)

| Canal | Voz | Estado |
|---|---|---|
| Charles Spurgeon Treasures | `bm_george` | 🔒 travada |
| Bíblia KJV | `am_michael` | 🔒 travada (0.80 + pausa 0,75s) |
| D.L. Moody | a decidir entre `am_onyx` / `am_fenrir` / `am_eric` | ⬜ A/B |
| J.C. Ryle (britânico) | `bm_lewis` ou `bm_daniel` | ⬜ reservar |
| próximos Treasures | am_adam, am_echo, am_liam, am_puck, bm_fable | livre |

### 🚫 Sobre "laboratório no ElevenLabs e clona no motor livre"

Não dá, e o motivo não é técnico. Os termos do ElevenLabs proíbem usar o áudio
gerado pra alimentar outro motor de voz, e as vozes do catálogo são licenciadas
de dubladores reais: clonar pra fora tira a voz da pessoa do contrato dela.
Num canal monetizado, é passivo que dorme por anos e acorda de uma vez.

E o argumento perdeu a razão de existir: **com 13 vozes masculinas em inglês de
graça, a escassez que justificaria o risco não existe mais.**

Se um dia a gente quiser uma voz que seja NOSSA de verdade e não de catálogo:
locutor contratado, com cláusula de uso sintético perpétuo por escrito, uma vez.
Aí clonar é legítimo porque o direito é nosso.

---

## 4. Funil: uma URL por canal (correção de 19/08)

**O erro atual:** `mananciall.org/go?s=yt&v=NNNN` foi desenhado quando existia um
canal só. Com uma rede de 10+, não dá pra saber de qual canal veio o scan.

**O desenho novo:**

```
mananciall.org/go/<canal>?v=NNNN
   ex.: /go/spurgeon?v=0042
        /go/moody?v=0007
```

✅ **NO AR desde 20/08/2026.** Rota no próprio site Astro
(`mananciall-site/src/pages/go/[...canal].ts`), servido 100% pela
**Cloudflare** (worker `manancial-new`; nada de Vercel — atualizado 20/08).
Resolve `<canal>` → destino + UTMs (`utm_source=youtube`, `utm_medium`,
`utm_campaign=<canal>`, `utm_content=<v>`) e loga cada scan na tabela
`go_scans` do D1 `mananciall-db` (canal, v, legacy, país). Antes disso o
`/go` respondia **404**: os QRs dos 15 vídeos no ar apontavam pro nada.

**Legado do Spurgeon:** os vídeos no ar apontam pro formato velho
(`/go?s=yt&v=`). Não dá pra re-renderizar. O `/go` sem canal é tratado como
`spurgeon` (flag `legacy=1` no log), que é historicamente verdade. Nenhum QR
impresso quebra, e daqui pra frente todo canal nasce com URL própria.
Destino atual do spurgeon: `/collections/spurgeon-library` (existe e responde).

### A LP: biolink por pregador (decisão do Gabriel)

Máximo **3 ofertas**: um combo, um clássico e um devocional. Decide rápido,
não paralisa, e é o mesmo template repetido por canal.

⚠️ **Gargalo real:** hoje o `/go` cai num placeholder e não existe coletânea
"The Best of D.L. Moody" na livraria. Canal novo com oferta genérica desperdiça
o tráfego mais quente que ele vai ter na vida. **Criar a coletânea antes de
lançar o canal.**

---

## 5. Assets: ambientar cada canal (Cloudflare Workers AI)

Mesma linguagem visual da família (retrato do pregador + fundo de época), mas
cada canal precisa de ambiente próprio — "igrejas diferentes", como o Gabriel
descreveu.

| Asset | Como | Diferenciação por canal |
|---|---|---|
| Fundo | Workers AI (geração de imagem, cota gratuita) | ambiente e paleta: catedral fria vs salão de avivamento quente |
| Retrato | foto histórica em DP (pré-1930) | o próprio pregador |
| Paleta | derivada do fundo | Spurgeon frio/azulado · Moody âmbar/quente |
| Trilha | ⚠️ ver `13_CANAL_MUSICA.md` | só com procedência provada |

**Ordem correta:** ambiente primeiro, paleta depois. A cor sai da imagem, não
o contrário, senão os dois brigam.
