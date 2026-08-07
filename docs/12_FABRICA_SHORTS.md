# 📱 FÁBRICA DE SHORTS — pesquisa e desenho da frente

> Frente: vídeos curtos (Shorts / TikTok / Reels) 100% programáticos.
> Pesquisa: 07/08/2026. Fontes no rodapé; sites de "dicas virais" são
> marketing de ferramenta, então aqui só entrou o que é consistente entre
> várias fontes e o que é mecânica de plataforma verificável.

---

## 1. A mecânica do que viraliza (o que é consenso real)

**Os primeiros 3 segundos decidem tudo.** As três plataformas medem retenção
desde o primeiro frame; quem desliza antes dos 3s mata a distribuição do vídeo.
Vídeos que seguram 60%+ da audiência depois dos 3s são os que entram no
For You / shelf de Shorts.

**Retenção > tudo, com nuance por plataforma:**

| Plataforma | O que o algoritmo pesa mais |
|---|---|
| TikTok | tempo assistido, rewatch, completude |
| Reels | completude (um Reel de 30s assistido inteiro por 60% ganha de um de 15s assistido por 40%) |
| **Shorts** | **CTR e ações de engajamento pesam MAIS que watch-time puro** |

**Estruturas que se repetem em tudo que performa:**
- Arco `gancho → valor → CTA` (o "93% dos que estouram" das ferramentas de clipe)
- **Loop:** o fim emenda no começo; rewatch conta muito no TikTok
- Legenda karaokê palavra a palavra, 3 a 5 palavras por linha, alto contraste
- Gancho verbal + visual simultâneos (texto na tela nos primeiros 2s)
- Duração doce: 30 a 60s pra sermão (autocontido, com arco completo)

**Como as ferramentas de clipe (Opus Clip etc.) escolhem momentos** (a gente
replica isso com LLM próprio, não paga ferramenta):
- picos emocionais e mudanças de tópico na transcrição
- frases-gancho ("a maioria erra nisso", pergunta direta, afirmação chocante)
- trecho AUTOCONTIDO: entende-se sem contexto do vídeo longo
- score relativo dentro do lote (não é previsão absoluta)

**No nicho cristão especificamente:** o que performa é trecho com frase
memorável e aplicável hoje (relacionamento, medo, dinheiro, propósito) mais
que doutrina; tom calmo e visual sóbrio performam em "faceless" há anos.
Spurgeon é PERFEITO pra isso: é aforístico por natureza.

---

## 2. A vantagem injusta que a gente já tem

A parte cara de qualquer fábrica de shorts é: transcrição com timing + seleção
de momento + legenda sincronizada + infra de render. **Tudo isso já existe aqui:**

| Peça da fábrica de shorts | Já temos? |
|---|---|
| 113 sermões narrados (áudio master limpo) | ✅ R2 |
| Transcrição **word-level com timestamp** | ✅ (AssemblyAI JSONs, insumo das legendas do longo) |
| Motor de render (Remotion + ffmpeg na VPS) | ✅ `factorio-render:v5` |
| Seleção de momento por LLM | ✅ padrão LLM-função já usado no `generate_marketing.py` |
| Publicação YouTube autenticada | ✅ token novo, scopes upload + force-ssl |
| Agendador com estado no R2 | ✅ `schedule_channel.py` (generalizar) |

O que NÃO existe ainda: composição Remotion 9:16, o seletor de momentos,
e as credenciais de TikTok/Meta.

---

## 3. Pipeline desenhado (6 estágios, todos programáticos)

```
[1 MINERAR]   LLM lê a transcrição word-level do sermão
              → devolve 3 a 5 clipes candidatos: {início, fim, score, hook_text}
              critérios no prompt: autocontido, arco completo, gancho nos 3s,
              corte SEMPRE em fronteira de frase, 30-60s
[2 CORTAR]    ffmpeg corta o trecho do áudio master (timestamps já existem)
[3 RENDERIZAR] Remotion 1080x1920:
              fundo do canal (visual próprio, não banco genérico)
              + legenda karaokê palavra a palavra (reusa o JSON word-level!)
              + card de hook nos primeiros 2s
              + fim que emenda no começo (loop)
[4 METADADOS] LLM: título, descrição, hashtags por plataforma
[5 PUBLICAR]  Shorts já; TikTok/Reels quando as credenciais saírem (ver §4)
[6 MEDIR]     retenção por clipe → realimenta o prompt do minerador
```

Escala: 113 sermões × 3 clipes = **~340 shorts** = quase 1 ano de 1/dia,
sem gravar nada novo. Render de short (~45s) na VPS: minutos, não é gargalo.

---

## 4. Distribuição: a realidade das APIs (pesquisada, não presumida)

| Plataforma | Caminho | Burocracia | Gotcha |
|---|---|---|---|
| **YouTube Shorts** | mesma Data API v3 que JÁ usamos | ✅ nenhuma nova | vertical + ≤3min = vira Short sozinho |
| **TikTok** | Content Posting API (Direct Post) | app + review (dias a 2 semanas) | ⚠️ **app não auditado só posta PRIVADO**; auditoria é outro passo. Sem agendamento nativo; upload em 2 etapas |
| **Instagram Reels** | Graph API 3 passos (container → poll → publish) | conta Business + app Meta + permissão `instagram_business_content_publish` (review 2-4 semanas) | precisa de **URL pública** do vídeo (R2 público resolve); 9:16, 5-90s |

**Consequência estratégica:** começar pelo Shorts HOJE (zero aprovação nova),
e disparar os dois processos de credencial EM PARALELO já, porque somam
semanas de espera. Alternativa de atalho: APIs de terceiros (Blotato etc.)
postam nas 3, mas viram dependência paga e mais um lugar com nossas chaves.

---

## 5. Decisões pendentes (gates do Gabriel)

- [ ] **S1. Canal novo ou Shorts no canal Spurgeon existente?**
      Recomendação: **no MESMO canal.** Shorts alimentam o longo do próprio
      canal (o algoritmo cruza), o canal já tem OAuth, e "primeiro canal de
      shorts" pode ser esse sem custo. Canal separado só se a identidade for
      outra (ex.: PT/ES no futuro).
- [ ] **S2. Visual do canal:** definir o fundo/identidade dos shorts
      (mesmo tema do longo? animação própria? imagem fixa + kinetic captions?)
- [ ] **S3. Criar app TikTok developers + app Meta** (burocracia tua; eu guio)
- [ ] **S4. Cadência:** 1/dia pra começar (recomendado), subir depois

## 6. Ordem de construção (quando os gates baterem)

1. `mine_clips.py`: seletor de momentos (LLM-função, OpenRouter) → JSON de candidatos
2. Composição Remotion `ShortSermon` (9:16, karaokê, hook card)
3. `render_short.py` na VPS (corte + render + upload R2)
4. Piloto: 5 shorts de 2 sermões diferentes → Gabriel aprova no ouvido/olho
5. Publicação: reusar `publish_youtube.py` (já sobe vídeo; short é só formato)
6. Fila + agendador (generalizar `schedule_channel.py` ou tabela no Teable)
7. TikTok/Reels quando credenciais saírem

---

### Fontes

- Mecânica/hooks: virvid.ai, hypenest.ai, socialync.io, vexub.com (guias 2026)
- Algoritmos por plataforma: almcorp.com, theviralapp.com
- Seleção de momentos: opus.pro (blog oficial), presenc.ai, frankx.ai
- APIs: postproxy.dev (Reels guide), zernio.com (TikTok/IG dev guides),
  getphyllo.com, posteverywhere.ai
- Nicho: sermonshots.com, grokipedia (faceless Christian channels)
