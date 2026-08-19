# 🎵 CANAL DE MÚSICA INSTRUMENTAL CRISTÃ — pesquisa e viabilidade

> Pergunta do Gabriel (16/08/2026): canal de worship instrumental para
> trabalhar/estudar/relaxar. Qual a dificuldade e as boas práticas?
> Pesquisa: 16/08/2026. Fontes no rodapé.

---

## Veredito curto

**Tecnicamente é o canal MAIS FÁCIL que a gente já desenhou.** Áudio longo +
imagem parada é render trivial: nem Remotion precisa, é ffmpeg puro.

**E é o canal com o MAIOR risco de negócio dos três.** Não por dificuldade de
produção: por licença de música e pela política de conteúdo inautêntico do YouTube,
que em 2026 matou a monetização de boa parte dos canais de música gerada por IA.

O buraco não é fazer. É fazer de um jeito que sobreviva.

---

## 1. A armadilha da licença (a parte que decide tudo)

**Worship moderno é propriedade de alguém.** Hillsong, Bethel, Elevation,
Maverick City: tudo protegido, e são detentores que fiscalizam ativamente.

Uma música tem **DOIS direitos separados**, e essa distinção é onde quase todo
mundo se enrola:

| Direito | O que é | Quem tem |
|---|---|---|
| **Composição** | a obra escrita (melodia + letra) | compositor / editora |
| **Master** | UMA gravação específica daquela obra | quem pagou a gravação |

Consequências práticas:

- **Cover instrumental NÃO te livra.** Tu cria um master novo (teu), mas a
  composição continua sendo de outro. Precisa de licença mecânica, e nos EUA
  a taxa de 2026 é de 13,1 centavos por cópia.
- **Licença mecânica cobre ÁUDIO, não VÍDEO.** Vídeo exige licença de **sincronização**,
  que é negociada caso a caso e não tem tabela. Por isso um cover 100% licenciado
  no áudio **ainda toma Content ID no YouTube**.
- **Content ID não é licença, é radar.** Ele detecta a obra independentemente de
  tu ter permissão. Reclamação de receita cai igual.

### ✅ A saída limpa: HINO EM DOMÍNIO PÚBLICO

Obra com **tune + letra + arranjo publicados até 1930** é domínio público nos EUA
(a partir de 01/01/2026 entrou o ano de 1930). Isso libera todo o cânone clássico
de hinos, que é justamente o repertório que combina com instrumental contemplativo.

**MINA:** um hino tem TRÊS partes com datas de copyright diferentes (melodia,
letra, arranjo). Melodia de 1780 com **arranjo de 1985** = arranjo protegido.
Como a gente vai criar arranjo próprio, só precisa provar que melodia e letra
são pré-1930 — e guardar a prova (edição publicada com a data).

---

## 2. A armadilha da monetização (a que mata canal já pronto)

O YouTube renomeou "conteúdo repetitivo" para **"conteúdo inautêntico"** e
apertou. Números que apareceram na pesquisa:

- Estima-se que **40%+ dos canais de música puramente de IA** perderam ou foram
  reprovados no YPP desde o fim de 2025.
- O sistema pega: cadência alta de upload, **fingerprint de áudio parecido entre
  faixas**, e título formulaico.
- "Despejo de Suno/Udio cru" é explicitamente o padrão que está sendo barrado.

**O que continua monetizando** (e é o desenho que a gente tem que seguir):
IA como INSUMO, não como produto. Faixa + **visual original** + estrutura com
timestamps + curadoria humana. RPM relatado de **$3 a $8** em nichos de sono,
lofi e cinematográfico, que é RPM alto.

### Sobre IA de música: os termos reais

| Item | Situação |
|---|---|
| Suno free | ❌ **não pode monetizar**. Uso pessoal só |
| Suno Pro ($10/mês) / Premier ($30) | ✅ direitos comerciais sobre o que gerar |
| Linguagem de posse | mudou de "User Owned" para "**Granted Commercial Rights**" após o acordo com a Warner |
| Content ID | ❌ áudio 100% IA **não é elegível**. Tu monetiza teu vídeo, mas não consegue reivindicar uso de terceiros |
| Risco 2026 | Suno vai depreciar modelos v5.x e anteriores conforme entram modelos treinados em catálogo licenciado |

Traduzindo o último ponto: **a base de música por IA é chão que se move.**
Modelo pode ser aposentado, termos podem mudar. Isso é risco de fornecedor, e
pesa contra fazer dele o alicerce único do canal.

---

## 3. Os três caminhos possíveis

| Caminho | Custo | Risco de licença | Risco de monetização | Diferenciação |
|---|---|---|---|---|
| **A. Hino PD + arranjo próprio por IA** | $10-30/mês | 🟢 baixo (obra é PD, master é nosso) | 🟡 médio (exige camada original) | 🟢 alta: repertório com significado |
| B. Música IA genérica (sem hino) | $10-30/mês | 🟢 baixo | 🔴 **alto** — é o perfil exato que está sendo demonetizado | 🔴 nenhuma |
| C. Cover de worship moderno | alto | 🔴 **alto** — sync não licenciada | 🔴 Content ID reclama tudo | 🟡 média |

**Recomendação: A.** É o único que junta licença limpa com diferenciação real.
E tem uma vantagem estratégica que o B não tem: o repertório de hinos é
**finito, conhecido e com significado pro público**, então dá pra montar
identidade editorial ("uma hora de [hino] pra estudar") em vez de faixa genérica
número 400.

---

## 4. Se for tocar, o que o canal precisa ter

Para não cair no filtro de conteúdo inautêntico:

- [ ] **Arranjo variado de verdade** entre faixas (fingerprint parecido é o que o
      radar pega). Nada de mesmo preset em 50 faixas.
- [ ] **Visual original**, não banco de imagem repetido. Mesma regra que o canal
      de Bíblia.
- [ ] **Estrutura na descrição**: timestamps por hino, nome de cada obra.
      É curadoria visível, e é o que separa álbum de despejo.
- [ ] **Cadência humana**: 1 a 2 por semana. Upload diário de faixa ambiente é
      sinal de alarme pro algoritmo.
- [ ] **Assinatura Suno Pro** antes de gerar qualquer coisa comercial
      (free não dá direito comercial, e isso não é retroativo).
- [ ] **Prova de domínio público arquivada** por hino (edição + data), junto do
      corpus. Mesma disciplina do Bloco 0 do canal de Bíblia.

## 5. Esforço de construção (reaproveita quase tudo)

| Etapa | Situação |
|---|---|
| Curadoria de hinos PD + prova de licença | ⬜ novo (trabalho de pesquisa, barato) |
| Geração dos arranjos | ⬜ novo (Suno Pro, com prompt por hino) |
| Montagem do vídeo longo | ✅ **ffmpeg puro** — mais simples que a esteira atual |
| Thumbnail / visual | ✅ mesma máquina do Spurgeon |
| Upload + agendamento | ✅ **já resolvido**: `canais.py` + `--canal musica_worship` |
| Fila e cron | ✅ já existe |

**Ou seja: a esteira multi-canal de 15/08 já cobre a parte chata.** O trabalho
novo é curadoria e geração de áudio, não engenharia.

---

## 6. O que eu recomendo de verdade

Canal é promissor **e** é o mais arriscado do ponto de vista de política de
plataforma. Os dois são verdade ao mesmo tempo.

Sugestão de sequência, pra não repetir o padrão de construir antes de validar:
1. Fechar o canal de Bíblia primeiro (decisões já travadas, licença resolvida).
2. Enquanto isso, **piloto barato de música**: 3 faixas de hino PD, arranjos
   distintos, e o Gabriel escuta. Custo: um mês de Suno Pro.
3. Só montar canal e esteira se o piloto passar no ouvido.

**Ressalva honesta:** os números de demonetização (40%+) e os RPMs ($3-$8) vêm de
blogs de nicho, não de comunicado do YouTube. A direção é consistente entre
fontes, mas eu não trataria os números como exatos. A política em si
(conteúdo inautêntico, Content ID, elegibilidade de áudio IA) é verificável.

---

### Fontes

- Licença/Content ID: foximusic.com (glossário 2026 e guia de Content ID),
  stemsplit.io, musicproductionwiki.com, nolo.com (mecânica)
- Domínio público: umc.org (como identificar hino PD), pdinfo.com,
  hymnstogod.org, musicasacra.com
- IA de música: terms.law (direitos do Suno), dynamoi.com, musicinafrica.net
  (mudança de termos pós-Warner), undetectr.com
- Monetização: outlierkit.com, miraflow.ai, lastplaydistro.com
