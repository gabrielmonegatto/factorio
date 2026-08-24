# 🏭 A esteira de um canal — como nasce, como roda, como não derruba os outros

> Escrito em 24/08/2026, depois de o Moody custar caro pra nascer.
> **O ponto deste doc: canal 3 não pode custar isso.**

---

## 1. O modelo

Cada canal é uma **esteira isolada**. Não é um pipeline gigante que atende N
canais: são **N pipelines iguais**, cada um com fila própria, estoque próprio e
processo próprio, chamando serviços compartilhados (narrar, legendar, renderizar).

```
minerado (D1)  ──narrar──▶  narrado  ──preparar──▶  pronto  ──render──▶  mp4  ──agendar──▶  YouTube
   works                    sermons                 (R2)                (R2)
```

As quatro etapas são **independentes e idempotentes**. Cada uma olha o estado e
faz o que falta. Não existe orquestrador segurando a mão de ninguém: se uma
falhar, as outras seguem, e na próxima passada ela tenta de novo.

| etapa | quem roda | quando | de → para |
|---|---|---|---|
| **narrar** | `narrar_sermao.py` | cron 4/4h, 2 por vez | capítulo minerado → mp3 + transcrição |
| **preparar** | `generate_marketing` + `narrate_marketing` | cron 1/h, 6 por vez | narrado → copy + hook |
| **render** | `render_buffer.py --loop` | serviço 24/7 | pronto → mp4 |
| **agendar** | `schedule_channel.py` | cron 1x/dia | mp4 → calendário do YouTube |

---

## 2. Por que os canais não se derrubam

Isolamento não é promessa, é consequência de decisões concretas:

| risco | o que impede |
|---|---|
| processo de um canal cair e levar os outros | serviço `systemd` separado por canal (`factory-producer@moody`), com `Restart=always` |
| dois canais escrevendo no mesmo arquivo | `flock` **por canal** (`/tmp/narrar_moody.lock`) |
| um canal comer a máquina inteira | teto de CPU: render `--cpus 8`, narração `--cpus 8`, de 16 |
| um canal sobrescrever o vídeo do outro | todo caminho carrega o slug: `_hybrid/<canal>/`, `storage/sermons/<canal>/`, `renders/<canal>/` |
| asset do canal errado entrar no vídeo | `pick_rotating` só olha o nível de cima da pasta; assets de nome compartilhado baixam com `force=True` |
| estourar a cota da API do YouTube junto | minutos de cron diferentes por canal; a cota é do **projeto**, compartilhada |
| um canal sem acervo travar a fila | fila vazia dorme e recheca; não trava, não estoura |

**Onde o isolamento NÃO existe, e é de propósito:**

- A **cota do YouTube** é do projeto GCP (10.000/dia, ~5 vídeos). Projeto por
  canal é violação de termos, ver `auth_youtube.py`.
- A **máquina** é uma só. Por isso os tetos de CPU acima.
- Os `.env` e o D1 são compartilhados. O que separa é a chave (`YT_MOODY_*`) e a
  coluna `canal`.

---

## 3. Como nasce um canal (a receita)

```bash
# 1. entrada no canais.py: nome, prefixo no R2, voz, cadência, autor da mineração
#    (COPIE a entrada do moody e ajuste — é o molde mais novo)

# 2. criar o canal no YouTube e autenticar (gate humano: conta Google)
python3 auth_youtube.py --canal <slug> --client-id ... --client-secret ... --gravar-env
#    → preencha `youtube_channel_id` no canais.py com o ID que ele imprime

# 3. assets visuais (fundos, bustos, avatar, banner)
python3 scripts/gerar_assets_canal.py --canal <slug>
#    ou gere no Gemini e recorte: scripts/recortar_bustos_gemini.py

# 4. CTAs fixos narrados
python3 remotion/gravar_ctas.py --canal <slug>

# 5. watermark de inscrição
python3 remotion/canal_branding.py --canal <slug>

# 6. mineração do acervo (uma entrada por OBRA, nunca um "lote")
node scripts/mining/expandir_<slug>.mjs && node scripts/mining/mine.mjs

# 7. ligar a esteira
bash scripts/deploy_vps.sh
ssh VPS 'cd /app/_factorio && bash scripts/esteira_canal.sh ligar <slug>'
```

Do passo 7 em diante o canal anda sozinho.

---

## 4. Onde olhar

| o quê | onde |
|---|---|
| fila de cada canal, por etapa | **bi.mananciall.org → aba "Esteira dos canais"**, filtro por canal |
| esteiras ligadas | `esteira_canal.sh estado` |
| log de um canal | `esteira_canal.sh logs <slug>` · `/var/log/factory_{narrar,prep,producer,schedule}_<slug>.log` |
| acervo minerado | BI → aba "Fila de mineração" |

---

## 5. As armadilhas que já custaram caro

Estão aqui pra canal novo não repetir. Todas produziam **vídeo errado sem erro
na tela**, que é a classe de falha mais cara desta fábrica.

1. **Número de sermão não é identificador global.** `(canal, número)` é. Quatro
   diretórios locais colidiram entre Spurgeon e Moody.
2. **Nenhum default, fallback ou prompt pode conter nome próprio.** A thumbnail
   do Moody saía assinada "Charles Spurgeon". Fallback é `"Treasures"`.
3. **Arquivo de descarte não mora na pasta que o rodízio varre.** `_cf_descartado/`
   dentro de `avatars/` fez o vídeo usar o busto rejeitado.
4. **Acervo grande não vale nada se ninguém puxa dele.** O Spurgeon travou em
   113 vídeos tendo 3.541 capítulos minerados, porque narrar era comando manual.
   Toda etapa tem que estar no cron.
5. **O código de render mora DENTRO da imagem Docker.** Editar o `.py` do host
   não muda produção. Use `scripts/deploy_vps.sh`, que faz os dois.
6. **`429` não é erro, é ritmo.** Espera e tenta de novo. `402` é falta de
   dinheiro: pula pro próximo provedor.
