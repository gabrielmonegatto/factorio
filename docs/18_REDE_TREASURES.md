# 🕸️ REDE TREASURES — arquétipo "pregações históricas" multiplicado

> Visão do Gabriel (19/08/2026): um arquétipo de canal (pregações extraídas de
> sermões e livros em domínio público), uma matéria-prima, e uma REDE de canais
> derivados servindo 3 a 7 canais com a mesma mineração.
> Este doc: a lista de pregadores, os critérios, e o desenho da rede.

---

## 1. O desenho da rede (3 camadas por matéria-prima)

> Nomes batidos pelo Gabriel em 26/08: **Treasures / Best Of / Vault**
> (Best Of era "Wisdom" no rascunho; Vault era "agregadores").

| Camada | Formato | Derivação |
|---|---|---|
| **Treasures** (canal-mãe por pregador) | sermão/mensagem NA ÍNTEGRA, 20-45min | narração integral do capítulo minerado |
| **Best Of** (condensado por pregador) | ≤10min, o miolo da pregação | NOVO corte + NOVO copy da mesma matéria-prima |
| **Vault** (agregadores por tradição: Patristic Vault, Reformation Vault, Puritan Vault...) | compilações temáticas, 2-8h, cruzando pregadores | formatos que NÃO cabem no canal-mãe; crédito por trecho |

A mineração de um pregador alimenta as três camadas. O custo marginal de cada
canal derivado é edição e packaging, não matéria-prima nova.

### ⚠️ A regra que salva a rede: derivação é TRANSFORMAÇÃO, nunca reupload

A política de "reused content" do YouTube barra monetização de conteúdo
repostado de outro canal **mesmo sendo teu e mesmo com permissão**, quando não
há transformação significativa. Relançar o MESMO áudio do Spurgeon num
agregador com outra thumbnail é reupload aos olhos do sistema, e derruba a
monetização do agregador (e mancha a rede).

O que cada camada muda pra ser derivação legítima:

- **Wisdom**: corte novo (o miolo do sermão), headline nova, ritmo novo. É outro
  vídeo de verdade. ✅
- **Agregadores**: vivem de formatos que o canal-mãe não faz — compilações
  longas (2 a 8h, "sermons for sleep", que é um formato FORTE no nicho),
  coletâneas temáticas cruzando pregadores ("puritanos sobre ansiedade"),
  narração em OUTRA voz. Nunca o mesmo arquivo re-postado. ✅
- Regra antiga da casa que continua valendo: **voz diferente por canal**. Dois
  canais com a mesma voz são o mesmo canal aos ouvidos de quem assiste os dois.

### Multiplicação pra acervo pequeno (pergunta do Gabriel, 26/08)

A referência que ele trouxe: canais tipo Luciano Subirá / Hernandes Dias Lopes
têm a MESMA pregação 7x com títulos diferentes. Por que funciona lá e o que
transfere pra cá:

**Lá são gravações DIFERENTES da mesma mensagem** (igrejas diferentes, câmera
diferente, duração diferente). O YouTube vê 7 vídeos distintos porque SÃO 7
vídeos distintos. Repostar o nosso mesmo arquivo com outro título não é isso:
é o mesmo hash de conteúdo, e cai na política de reused content (desmonetiza e
mancha o canal).

Mas a nossa esteira tem o equivalente honesto, e quase de graça: **re-renderizar
é a nossa "outra igreja"**. Mesmo texto-fonte, outro vídeo de verdade:

| Degrau | O que muda | Custo | 77 caps do Moody viram |
|---|---|---|---|
| 1. Best Of | corte novo (miolo), copy novo, título novo | só máquina | +150 a 300 cortes |
| 2. Compilação temática | "Moody on Prayer, 3 hours": trechos de N sermões costurados, rotulada como compilação | montador ffmpeg (⬜ construir) | +dezenas de longos |
| 3. Sermão compilado original | mensagem única montada de trechos do PRÓPRIO pregador sobre um tema, apresentada como coletânea ("from the writings of D.L. Moody") | curadoria LLM + montador | +dezenas |
| 4. Remaster | narração em outra voz/velocidade, visual novo, corte novo | só máquina | dobra o catálogo |
| 5. Minerar mais fundo | Gutenberg foi só a 1ª pá: Archive.org tem coletâneas de sermões, transcrições de jornal | esteira de mineração | 77 → 200-400 caps |

A linha que não se cruza: mesmo ARQUIVO, título novo. Todo degrau acima produz
arquivo novo com conteúdo transformado. E na camada Vault vale misturar
pregadores no mesmo vídeo, desde que cada trecho seja creditado a quem falou:
compilação assumida é formato; texto de um na boca de outro é fraude.

---

## 2. Critérios da lista

1. **Licença limpa** (domínio público REAL, incluindo a tradução quando houver)
2. **Popularidade** (público buscador em inglês; o nome puxa busca sozinho?)
3. **Volume de material** minerável e já digitalizado (CCEL, Gutenberg, Monergism)
4. **Modelabilidade** (prosa que vira narração de 30min sem reescrita pesada)
5. **Oferta atrelável** (livraria Mananciall: "The Best of X" por pregador)
6. **Filtro doutrinário do dono** (Gabriel, 26/08): fora o predeterminismo
   decretal. A régua é o PÚLPITO, não o rótulo: calvinista que na prática prega
   oferta livre a qualquer pecador passa (Spurgeon, Ryle, Maclaren); pregação
   decretal não passa. Por essa régua saíram da lista: **Agostinho** (fonte do
   predestinacionismo), **Calvino** (epônimo; e o inglês PD dos sermões é de
   1580), **Edwards** (decretal até no púlpito). Ficam utilizáveis no máximo
   como trecho creditado em Vault temático, nunca como canal-mãe.

---

## 3. A LISTA, em ondas

### 🥇 Onda 1 — Século XIX / vitorianos (busca alta, inglês nativo, risco zero)

| Pregador | Morte | Por que entra | Força |
|---|---|---|---|
| **C.H. Spurgeon** ✅ | 1892 | JÁ NO AR (113 sermões minerados) | canal-mãe da rede |
| **D.L. Moody** | 1899 | evangelista mais famoso dos EUA; prosa SIMPLES, modela fácil | busca alta, americano |
| **J.C. Ryle** | 1900 | anglicano reformado, prosa cristalina, público reformado atual ama | modelagem fácil |
| ~~Jonathan Edwards~~ | 1758 | ❌ REMOVIDO 26/08 pelo filtro doutrinário (critério 6): decretal até no púlpito | |
| **John Wesley** | 1791 | fundador do metodismo; 44 sermões-padrão prontos | denominação inteira busca |
| **George Whitefield** | 1770 | par histórico de Edwards/Wesley, voz do Grande Avivamento | fecha o trio do Awakening |
| **Andrew Murray** | 1917 | devocional de oração/santidade ("Abide in Christ") | nicho de oração é fortíssimo |
| **E.M. Bounds** | 1913 | TUDO dele é sobre oração | nicho "prayer" concentrado |
| **George Müller** | 1898 | histórias de fé e provisão (orfanatos) | storytelling pronto |
| **Oswald Chambers** | 1917 | "My Utmost for His Highest", devocional best-seller há um século (publicado 1927, PD) | busca devocional diária |
| **F.B. Meyer** | 1929 | biografias bíblicas devocionais | matéria-prima pra arquétipo 2 |
| **R.A. Torrey** | 1928 | sucessor de Moody; obras pré-1930 | ⚠️ conferir obra a obra (morte tardia) |
| **Alexander Maclaren** | 1910 | *Expositions of Holy Scripture*: 32 VOLUMES cobrindo a Bíblia inteira | volume monstruoso, expositivo |
| **T. De Witt Talmage** | 1902 | 500+ sermões publicados; o "mais lido do mundo" na época (sindicado em 3.000 jornais) | volume + prosa vívida |
| **Charles Finney** | 1875 | avivamentos; *Lectures on Revivals* | busca "revival" |

### 📊 LISTA FINAL 1.0 do Treasures (batida pelo Gabriel em 26/08)

Critério de corte: 365+ peças distintas em PD inglês (1 ano a 1/dia) OU 180+
(1 ano a 0.5/dia), passando no filtro doutrinário (critério 6). Agostinho,
Calvino e Edwards foram REMOVIDOS pelo filtro; entraram Matthew Henry, F.B.
Meyer (promovido) e Alexander Whyte.

| # | Canal | Volume PD | Cadência | Púlpito na prática | Fonte |
|---|---|---|---|---|---|
| ✅ | **Spurgeon** | 3.541 minerados (63 vols) | 1/dia, NO AR | oferta livre (o modelo) | CCEL |
| ✅ | **Moody** | 77 minerados + escada §1 | 0.5/dia, NO AR | evangelista "whosoever" | Gutenberg |
| 1 | **Alexander Maclaren** | 32 vols ≈ 1.500 sermões | 1/dia | expositor devocional, zero decreto | CCEL/Archive |
| 2 | **Joseph Parker** | *The People's Bible*, 25+ vols ≈ 1.000 | 1/dia | dramático, imaginativo, oferta livre | Archive |
| 3 | **Matthew Henry** | comentário da Bíblia inteira ≈ 1.000+ caps | 1/dia | devocional prático amado por todas as tradições | CCEL (⚠️ inglês de 1706, modernização leve) |
| 4 | **João Crisóstomo** | ~600-800 homilias (NPNF) | 1/dia | sinergista pré-Agostinho, o melhor encaixe do filtro | CCEL (⚠️ notas acadêmicas; excluir Adversus Judaeos) |
| 5 | **T. De Witt Talmage** | 500+ sermões | 1/dia | revivalista vívido, o mais "YouTube" | Archive |
| 6 | **F.B. Meyer** | ~40 livros ≈ 400-600 caps | 0.5/dia | Keswick; biografias bíblicas = episódio pronto | Gutenberg/Archive |
| 7 | **Andrew Murray** | ~400-500 caps | 0.5/dia | oração/entrega, "whosoever" | Gutenberg |
| 8 | **J.C. Ryle** | ~300-500 | 0.5/dia | prático, oferta quentíssima | Gutenberg/Archive |
| 9 | **Alexander Whyte** | *Bible Characters* + Bunyan ≈ 300-400 | 0.5/dia | retratos de alma; o "canal dos personagens" | Archive |
| 10 | **John Wesley** | ~150 sermões + diários | 0.5/dia | o anti-predestinação original | Gutenberg |

Banco de reservas (decisão futura do Gabriel): **G. Campbell Morgan** (~250 do
*Westminster Pulpit* pré-1930, mas morte em 1945 = conferir obra a obra),
**Finney** (anti-calvinista declarado, mas perfeccionismo/governo moral são
flag doutrinária), **Whitefield** (só ~60-80 sermões sobrevivem: vira Vault,
não canal-mãe), **Lutero** (ed. Lenker PD, curadoria pesada de polêmicas).

### 🕰️ Idade Média (o buraco entre patrística e Reforma)

| Nome | Nota |
|---|---|
| **Bernardo de Claraval** | 86 sermões no Cântico (tradução PD); místico, nicho devoto |
| **Tomás de Kempis** | *Imitação de Cristo*: **114 caps JÁ MINERADOS no nosso D1** |

### 🥈 Onda 2 — Puritanos (nicho MUITO fiel; alimenta o agregador "Puritan Faith")

| Pregador | Por que entra |
|---|---|
| **Thomas Watson** | a prosa mais acessível do puritanismo; aforístico (ótimo pra shorts) |
| **John Bunyan** | Pilgrim's Progress = busca gigante; sermões além do livro |
| **Thomas Brooks** | frases de efeito prontas ("Precious Remedies") |
| **Jeremiah Burroughs** | "contentment" é dor moderna com nome antigo |
| **John Owen** | denso demais pra 30min; PERFEITO pro formato Wisdom condensado |
| **Richard Baxter** | pastoral; volume enorme |
| **John Flavel** | providência; devocional |
| **Samuel Rutherford** | as cartas são joias curtas (formato shorts/Wisdom) |

⚠️ Inglês do séc. XVII: precisa modernização leve de grafia na mineração
(thee/thou, spellings). Etapa nova na esteira, barata via LLM-função.

### 🥉 Onda 3 — Reforma

| Pregador | Nota |
|---|---|
| **Martin Luther** | busca enorme; usar traduções EN do séc. XIX (PD). Curadoria: tem textos polêmicos que NÃO entram |
| ~~John Calvin~~ | ❌ REMOVIDO 26/08 pelo filtro doutrinário (critério 6); e o inglês PD dos sermões é de 1580 |
| **John Knox** | fecha a tríade; menor busca, entra por completude do agregador |

### 🏛️ Onda 4 — Patrística (alimenta o agregador "Patristic Faith")

Matéria-prima: as traduções **Ante-Nicene Fathers / Nicene and Post-Nicene
Fathers** (Schaff, 1885-1900) — domínio público, digitalizadas na CCEL. É a
MAIOR mina de patrística em inglês que existe, e é livre.

| Nome | Por que entra |
|---|---|
| **John Chrysostom** | literalmente "boca de ouro": o maior pregador da igreja antiga, centenas de homilias PRONTAS |
| ~~Augustine~~ | ❌ REMOVIDO 26/08 pelo filtro doutrinário (critério 6): fonte do predestinacionismo |
| **Athanasius** | "On the Incarnation" tem público jovem reformado/ortodoxo. ⚠️ o prefácio famoso de C.S. Lewis é PROTEGIDO, nunca usar |
| **Basílio / Gregório Nazianzo** | completam o agregador |
| **Inácio / Policarpo** | cartas curtas = formato curto pronto |

---

## 4. 🚫 A lista dos NOMES-ARMADILHA (parecem óbvios, derrubam canal)

| Nome | Por que NÃO |
|---|---|
| **A.W. Tozer** | obras principais são 1948+ ("The Pursuit of God"), protegidas nos EUA até ~2043 |
| **Martyn Lloyd-Jones** | morreu 1981; MLJ Trust ativo e vigilante |
| **C.S. Lewis** | protegido; espólio litigioso |
| **Watchman Nee** | protegido |
| **Billy Graham / A.W. Pink tardio** | Graham protegido; Pink morreu 1952, obras pós-1930 em zona cinzenta |

Regra: **morte antes de ~1930 = zona verde.** Entre 1930 e 1955, conferir obra a
obra (publicação pré-1930 nos EUA). Depois disso, fora.

---

## 5. Ordem de lançamento

1. ✅ **Moody** (Treasures 2): **NO AR desde 25/08**, 77/77 renderizados,
   warmup 14 dias a 1/dia e depois 1 a cada 2 dias. Validou a replicação:
   a esteira dele se inaugurou pelo próprio cron.
2. **Ryle** (Treasures 3): mesmo perfil, público reformado engajado.
3. **Best Of** (1º derivado): condensados de Spurgeon + Moody. Testa a camada 2
   com matéria-prima já minerada, custo quase zero. Precisa do cortador (⬜).
4. **Edwards ou Wesley** (Treasures 4): nomes maiores, prosa mais difícil.
5. **Puritan Vault** (1º agregador): compilações longas/temáticas quando
   houver 2+ puritanos minerados. Precisa do montador de compilação (⬜).

Patrística fica pra depois: a mineração das homilias (ANF/NPNF tem formatação
acadêmica pesada, notas de rodapé etc.) é a mais cara da lista.

## 6. O que a esteira já suporta e o que falta

| Peça | Estado |
|---|---|
| Multi-canal (`canais.py`, credencial por canal, guardião) | ✅ pronta |
| Mineração → narração → render → publicação, ponta a ponta por canal | ✅ validada 2x (Spurgeon E Moody) |
| Prompt de marketing por canal (`montar_system(C)`) | ✅ generalizado (era hardcoded no Spurgeon) |
| Esteira por canal como unidade systemd/cron (`esteira_canal.sh ligar <slug>`) | ✅ 24-25/08 |
| Semáforo de CPU da máquina inteira (`vaga_cpu.py`) | ✅ 26/08 |
| Etapa de modernização de grafia (puritanos) | ⬜ nova, LLM-função |
| Cortador Best Of (miolo de sermão ≤10min) | ⬜ novo |
| Montador de compilação (Vault, 2-8h temático) | ⬜ novo montador ffmpeg |
| Aumento de cota da YouTube Data API | ⬜ **GATE DO GABRIEL: é o gargalo real da rede** |

## 7. Capacidade medida e o gargalo real (26/08)

Medido, não estimado (deltas dos mp4 no R2 + logs de narração):

- **Render**: 33-37 min por vídeo longo numa vaga de 5 CPUs (18 min com a máquina livre).
- **Narração + transcrição**: ~25 min por sermão de 40min numa vaga.
- **Máquina** (16 vCPU, 3 vagas): ~**45-60 vídeos longos/dia** de ponta a ponta.
  Prova prática: os 71 renders restantes do Moody saíram em ~1 madrugada.

**Compute NÃO é o limite. O limite é a cota da YouTube Data API**: 10.000
unidades/dia por projeto GCP, upload custa 1.600 → **~6 uploads/dia** pra rede
INTEIRA no projeto atual. A VPS produz 50/dia; o YouTube deixa publicar 6.
Multiplicar projetos pra multiplicar cota viola ToS (risco: suspensão de todos).
Caminho certo: **formulário de audit/aumento de cota do projeto** (gate do
Gabriel). Até lá, 6/dia paga confortavelmente 4-5 canais Treasures + margem.

## 8. Verificação por telefone: como fazer e como gerenciar (30/08)

O YouTube limita **~2 canais verificados por número por ano**. Pra 10+ canais,
a solução limpa é chip pré-pago próprio. O que importa saber:

### O insight que simplifica tudo

**Número de verificação ≠ número de segurança da conta.** O YouTube usa o
telefone UMA vez, no ato de verificar o canal. Perder o número depois NÃO
perde o canal: a segurança da conta é do login Google, não desse número.

Por isso a regra de ouro: **NUNCA cadastrar o chip de verificação como
telefone de recuperação/2FA da conta Google.** Recuperação e 2FA ficam no
número principal do Gabriel (ou app autenticador). O chip é consumível.

### Passo a passo

1. Comprar chip pré-pago (Vivo/Claro/TIM, R$ 10-20; eSIM também serve).
   ⚠️ Número VoIP/virtual/alugado o Google REJEITA, e canal montado em
   número alugado é canal em risco. Só linha de operadora de verdade.
2. Ativar o chip num celular qualquer (só precisa receber SMS/ligação).
3. Logado na conta do canal: youtube.com/verify → informar o número →
   receber o código → pronto. Isso libera capa própria, vídeo >15min e live.
4. Anotar no registro abaixo. O mesmo chip serve pro 2º canal do ano.
5. Recarga mínima ocasional se quiser manter o número vivo, mas não é
   obrigatório pro canal (ver insight acima).

### Registro de números (preencher a cada verificação)

| Número (últimos 4) | Canal verificado | Data | Obs |
|---|---|---|---|
| (principal) | Charles Spurgeon Treasures | pré-08/2026 | |
| (principal) | D.L. Moody Treasures | 25/08/2026 | esgotou o principal no ano |
| | Alexander Maclaren Treasures | | chip 1 |
| | Andrew Murray Treasures | | chip 1 (2º uso) |

### Quando mandar o formulário de aumento de cota (a pergunta do Gabriel)

A intuição dele está certa: **com volume pequeno a chance de negarem é
grande.** O formulário de audit avalia legitimidade E necessidade
demonstrada; pedir aumento usando 20% da cota é pedir pra ser negado, e
negativa cria histórico.

Momento certo, na ordem:
1. 4+ canais no ar publicando diariamente (Spurgeon, Moody, Maclaren, Murray);
2. gráfico de uso da cota no GCP batendo no teto (>90%) por 2+ semanas
   seguidas: é ISSO que o avaliador olha como "necessidade";
3. canais limpos, sem strike, com descrição honesta do caso de uso
   ("ferramenta própria de publicação de conteúdo próprio em domínio público").

Estimativa: 3-4 semanas após a estreia do Maclaren e do Murray. Até lá o
funil não trava: upload manual não gasta cota, e a API só "veste" o vídeo
(~150 unidades) — o vestidor de uploads cobre a estreia dos 10 canais.

## 9. A linha de produção no Notion (05/09)

Pedido do Gabriel: "a publicação é só uma etapa; todos os Treasures, ao cair na
linha no Notion, já são construídos de ponta a ponta, e os gates meus eu marco OK".

Desenho: 1 linha do banco `Canais` = 1 canal em 13 estações (00 backlog → 12 no
ar). `scripts/linha_treasures.py` mede o estado real e escreve Etapa/Bloqueio;
o Gabriel só mexe em Estado (backlog→esteira) e em 5 checkboxes (Busto aprovado,
Canal YouTube criado, Verificado por telefone, Coleção na loja, Estrear
autorizado). Estações e critérios de "pronto": docstring do script e página
"🏭 Linha Treasures" no Notion. Automação registrada no doc 18_AUTOMACOES.

Limite honesto da v1: o berçário (estações 01-05) roda do Windows (`--puxar`),
porque o `novo_canal.py` fala com a VPS por ssh e edita o canais.py do repo; na
VPS a linha só mede, espelha e liga produtor/esteira. Fonte `archive` (Parker,
Talmage) ainda não tem adaptador: a linha avisa em vez de tentar.

