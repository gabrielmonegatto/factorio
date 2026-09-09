# 🎙️ Catálogo de vozes da rede (fechado em 09/09/2026)

> Decisão do Gabriel: **voz de canal vem de TTS de nuvem com catálogo profissional**,
> escolhendo por free tier e custo-benefício. Motivo: o páreo de modelos abertos
> (Kokoro PT, OmniVoice, Chatterbox, Qwen3-TTS) foi reprovado no ouvido dele em
> 05 e 06/09, e o garimpo de referências abertas (MLS/LibriVox) também: LibriVox
> é gente comum lendo em casa, nunca ia dar voz de estúdio.
>
> Máquina: `scripts/tts_nuvem.py` (3 provedores + trava de gasto). Fila de gasto:
> tabela `tts_uso` no D1.

## §1 A lei que veio antes do catálogo

**O Google NÃO tem cap de caracteres pro TTS.** A cota editável no console é de
REQUISIÇÕES POR MINUTO (`RequestsPerMinutePerProject` 1000, `Chirp3...` 200).
Não existe botão "pare em 1 milhão de caracteres". Ou seja: o prejuízo que o
Gabriel levou não tinha como ser travado lá dentro.

Por isso a trava é NOSSA: o `tts_nuvem.py` conta os caracteres, soma o mês na
tabela `tts_uso` do D1 e **recusa a chamada** ao passar de 90% do free tier.
Vale a lei do Magnific (doc 21): custo se confere no painel, nunca no rótulo.

## §2 Os provedores (free tier conferido em 07/09/2026)

| Provedor | Free tier | Validade | Preço depois | Sermões de 1h/mês grátis |
|---|---|---|---|---|
| **Google Chirp 3 HD** | 1M chars/mês | permanente | US$ 30/1M | ~22 |
| **Azure Neural (F0)** | 500k chars/mês | permanente | US$ 16/1M | ~11 |
| **Amazon Polly Neural** | 1M chars/mês | **só os 12 primeiros meses da conta** | US$ 16/1M | ~22 |

Régua: 1 sermão de 1h ≈ 45.000 caracteres. 1 canal a 1/dia ≈ 1,35M chars/mês.
**Um canal a 1/dia NÃO cabe no free tier de um provedor só** (1,35M contra 1M).
Cabe a 0,5/dia (675k), ou a 1/dia pagando o excedente: ~US$ 10/mês no Google.
Ou seja: o free tier é rede de segurança, não o plano. O plano é que a narração
de um canal custa entre zero e US$ 10 por mês, e a trava garante que não vira 300.

## §3 O catálogo pt-BR (masculinos, narrador de sermão)

Nomes conferidos na doc de cada provedor. A escolha final é do OUVIDO do Gabriel:
`python3 scripts/tts_nuvem.py --amostras --provedor <x> --texto trecho.txt`
gera o mesmo trecho em todos os candidatos do provedor.

### Google Chirp 3 HD (`pt-BR-Chirp3-HD-<nome>`)

| Voz | Nota |
|---|---|
| Charon | grave, o mais "locutor" |
| Fenrir | encorpado, energia alta |
| Orus | médio, neutro |
| Puck | mais jovem, leve |

Femininas na mesma família: Aoede, Kore, Leda, Zephyr.
⚠️ A lista definitiva sai do próprio provedor: `--vozes --provedor google`.

### Azure Neural (`pt-BR-<nome>Neural`)

| Voz | Nota |
|---|---|
| Antonio | padrão da casa Azure, bem redondo |
| Donato | grave |
| Fabio | claro, dicção limpa |
| Julio | médio |
| Nicolau | jovem |
| Valerio | sério |
| Humberto | maduro |

É o provedor com MAIS opção masculina em pt-BR (7). Femininas: Francisca,
Brenda, Elza, Giovanna, Leila, Leticia, Manuela, Thalita, Yara.

### Amazon Polly

| Voz | Nota |
|---|---|
| Thiago | o único masculino pt-BR no motor Neural |

Camila e Vitória são femininas (Camila tem motor Generative em algumas regiões).
Ricardo só existe em Standard (qualidade velha): fora.

## §4 Regras de atribuição (herdadas do doc 10, valem aqui)

1. **1 canal = 1 voz, travada pra sempre.** Trocar timbre no meio de 100 horas
   de acervo é retrabalho total.
2. **Dois canais nunca compartilham voz.** Quem assiste os dois ouve o mesmo
   canal. (A permissão de repetir voz que o Gabriel deu em 27/08 vale pro Kokoro
   em inglês, onde o catálogo é pequeno; aqui há voz de sobra.)
3. **1 provedor por canal.** Não dá pra alternar Google e Azure no mesmo canal.
4. **Velocidade padrão 0,92** e a engenharia de pausa da casa (corte em ponto
   final, aparar pontas, emendar com 0,75s). Vale pros três provedores.

### Atribuição (calculada, não chutada)

Política do Gabriel (09/09): "tudo bem pagar, desde que a gente aproveite todo
mês o free tier das três e vá administrando pra gastar o mínimo".

⚠️ A administração é **por canal**, não por sermão: mandar o sermão de hoje pro
Google e o de amanhã pra Azure trocaria a VOZ do canal no meio. O que se
distribui entre provedores são os canais inteiros.

`python3 scripts/tts_nuvem.py --planejar` faz a conta e busca por força bruta a
atribuição mais barata. Rodado em 09/09, ele corrigiu o meu palpite inicial e
economizou US$ 5,20/mês:

| Canal | vídeos/dia | Provedor | Voz |
|---|---|---|---|
| Spurgeon BR | 1,0 | Google Chirp 3 HD | Charon |
| Bíblia PT | 1,0 | Amazon Polly | Thiago |
| Moody PT | 0,5 | Azure | Antonio |

Custo: **US$ 18,90/mês pelos três canais, com ZERO free tier ocioso.** A regra
que o otimizador achou: o canal MENOR vai pro free tier MENOR (Azure, 500k), e o
excedente cai nos provedores de US$ 16/M em vez do de US$ 30/M.

Reordenar toda vez que entrar canal novo: o `--planejar` avisa se existe
atribuição melhor. Trocar provedor de canal JÁ NO AR não vale (troca a voz).

## §5 Chaves no `.env` (nunca no git)

```
GOOGLE_TTS_API_KEY=...        # chave de API restrita à Text-to-Speech API
AZURE_SPEECH_KEY=...          # recurso Speech, tier F0
AZURE_SPEECH_REGION=brazilsouth
AWS_ACCESS_KEY_ID=...         # usuário IAM só com AmazonPollyReadOnlyAccess
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

## §6 Pendências

- [ ] Gabriel: criar as contas/chaves (§5) e me passar
- [ ] eu: gerar amostras nos 3 provedores e entregar pro ouvido dele
- [ ] eu: plugar o provedor escolhido no `narrar_sermao.py` como motor alternativo
      ao Kokoro, por canal (campo `motor_tts` no `canais.py`)
- [ ] eu: etapa de tradução EN->PT na esteira (LLM-função, cacheada no D1)
- [ ] futuro: voz própria do Gabriel (gravação + clonagem em GPU) como assinatura
      da casa, quando quiser um timbre que não seja de catálogo
