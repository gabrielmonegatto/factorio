# Destilado: Ask (Pergunte.) — Ryan Levesque

> Fonte: `Ask-Ryan-Levesque-PT.pdf`, destilado em 2026-07-04. Capítulos cobertos: 11–18 (Parte II, a metodologia) + glossário. Caps. 1–10 (história) e 21–22 descartados; casos dos caps. 19–20 resumidos em Exemplos canônicos.
> Usado pelas skills: quiz-framework-ask-method

## Frameworks

### 1. Ask Formula — o processo em 6 passos

**Preparar → Persuadir → Segmentar → Prescrever → Lucrar → Pivotar.**

A implementação prática (Survey Funnel Strategy) usa 4 pesquisas em 4 pontos do funil:

1. **Deep Dive Survey** (Preparar) — pesquisa aberta, rodada UMA vez, antes de construir o funil. Descobre os buckets reais e a linguagem natural do consumidor.
2. **Micro-Commitment Bucket Survey** (Segmentar) — o quiz permanente do funil. Série de perguntas de múltipla escolha, uma por tela, terminando em nome/e-mail em troca de um diagnóstico personalizado.
3. **Do You Hate Me Survey** (Pivotar) — e-mail a não-compradores perguntando por que não compraram. Revela objeções não tratadas.
4. **Pivot Survey** (Pivotar) — e-mail final: "o que você quer que eu fale a seguir: A, B ou C?" Reinicia o funil com nova oferta.

Entre Segmentar e as pesquisas de e-mail ficam: a **landing page de autodescoberta** (Persuadir, antes do quiz) e a **página de venda na mesma visita** (Prescrever, depois do quiz).

### 2. Deep Dive Survey (Preparar) — de onde vêm os buckets

**Com lista de e-mail:**
1. E-mail simples pedindo 5 minutos: "me diga qual é o maior desafio que você está enfrentando com X agora".
2. Pesquisa abre com a **SMIQ** (Single Most Important Question), aberta: *"Qual é o seu maior desafio nº 1 com [tema] agora?"* — é a pergunta que importa; se a pessoa abandonar depois dela, você já ganhou.
3. Depois da SMIQ: 3–5 perguntas fechadas de baixo limiar (A/B primeiro, depois demográficas) — que também servem de teste para as futuras perguntas do quiz.
4. Última etapa: nome, e-mail e telefone opcionais, com a frase-chave *"prometo não te vender nada"* — o telefone é dado de pontuação, não de venda.

**Sem lista:** landing page temporária com tráfego pago + "suborno ético" (relatório/kit grátis posicionado para resolver o desafio). Nesse caso a SMIQ ganha uma segunda pergunta aberta: *"E o que te levou a buscar a resposta HOJE especificamente?"* (o quê + o porquê-agora).

**Análise (a planilha):**
- `LEN` = comprimento da resposta aberta em caracteres. Resposta longa = maior probabilidade de compra.
- `MULT` = 1,5 se deixou telefone, 1,0 se não (quem deixa telefone é ~50% mais propenso a comprar).
- `SCORE` = LEN × MULT. Ordene decrescente.
- `HYPER` = top 20% dos scores. **A análise de buckets usa SÓ os hiper-responsivos** (e os 20% seguintes se houver menos de 100 respostas no topo). Score acima de ~400 indica segmento hiper-responsivo digno de foco.
- Categorize cada resposta do top 20% em até **3 categorias** (CAT1–3). Primeira passada gera dezenas de categorias.
- Consolide em passadas: (1) funda rótulos idênticos com nomes diferentes; (2) funda sub-buckets pequenos em temas maiores (ex.: "conversão AdWords" + "conversão Bing" + "compliance PPC" → "PPC/tráfego frio"). Preserve os nomes dos sub-buckets — eles viram os pontos específicos da copy de cada segmento.
- Pare quando **3–5 temas cobrirem ~80% das respostas**. Esses temas são os buckets.
- Demografia diz **quem** é o cliente (avatar); as respostas abertas dizem **o que ele quer comprar**. As duas análises são separadas.

### 3. Micro-Commitment Bucket Survey (Segmentar) — o quiz

Uma pergunta por tela. Três categorias de pergunta, nesta ordem:

**A. Pergunta "Engraxar as Rodas" (1ª tela, sempre)**
- Binária, respondível com ~100% de certeza sem pensar ("Homem ou mulher?", "Tempo integral ou tem outro emprego?").
- Critério duplo: (a) a resposta é útil de saber; (b) ninguém para pra pensar.
- Função neurológica: pedir passo grande cedo dispara o alarme de ameaça (sistema límbico → luta/fuga). Pergunta trivial cria "ímpeto de tomada de ação". Analogia do livro: pedir e-mail de cara = estender os braços pra um abraço; essa pergunta = acenar "oi" de longe.

**B. Perguntas de Personalização (2 a 4 telas)**
- Cada uma coleta UMA variável que será usada depois: em merge fields de e-mail ("se você tem [50 anos]..."), na versão da oferta, na segmentação de promoções futuras.
- Opções consolidadas com foco 80/20: o Ryan cortou 6 opções da pesquisa aberta para 2 no quiz, fundindo categorias <5% nas maiores. Menos opções = mais gente responde e avança.
- Dificuldade progressiva: renda, idade, situação íntima vêm depois que o ímpeto foi criado.
- **Colchetes/lógica condicional**: a pergunta seguinte ecoa a resposta anterior ("Em termos do seu [negócio na internet / prática de consultoria]..."). Prova que a pessoa está sendo ouvida; testado, aumenta conclusão. Mas **subestime a personalização** — fraseado natural, não robótico.

**C. Pergunta de Segmentação (última pergunta, sempre)**
- Recapitula as respostas anteriores em linguagem coloquial e pergunta o desafio: *"Os [donos de negócio] com quem trabalho, que faturam [pelo menos $100K] por ano e que têm uma [lista pequena], tendem a enfrentar um destes desafios. Qual é o seu maior desafio agora?"*
- Fraseado natural: "faturam pelo menos $100K" (como numa conversa), não "entre $100K e $499K" (como num formulário).
- As opções SÃO os buckets, descritos como o próprio mercado descreveria (linguagem colhida no Deep Dive), cada uma com 1–2 linhas de contexto.
- **Sempre inclua "Nenhuma das opções acima"** — é instrumento de medição: >10% escolhendo "Outro" = repense os buckets; >20% = com certeza errou.
- Segmente pelo **problema central**, não por demografia. Demografia personaliza a mensagem; problema define o bucket. (No exemplo do livro, os 4 problemas eram os mesmos do negócio de $100K ao de $10M — só a solução prescrita mudava.)

**D. Captura (depois da última pergunta, antes do resultado)**
- Nome + e-mail em troca do diagnóstico/recomendação prometido na landing. Perde-se algum lead aqui, mas o follow-up segmentado compensa com folga. (Exceção rara: mandar direto pra página de venda personalizada, só com motivo específico.)

**A Grande Ideia** (o critério de qualidade de toda pergunta): o quiz deve imitar a experiência de um especialista fazendo perguntas pessoalmente antes de recomendar uma solução — o médico, o vendedor da loja de bolsas ("Que tipo de bolsa sua esposa tem hoje? É pra usar todo dia ou ocasião especial?"). Se a pergunta não soaria natural nessa conversa, está errada.

### 4. Landing page de autodescoberta (Persuadir) — o que vem antes do quiz

Posicionamento: **"brincar de médico"** — diagnosticar e prescrever, nunca "responda pra eu te vender melhor".
Roteiro do vídeo/página, em ordem:
1. **Gancho** em forma de pergunta ("É possível melhorar sua memória em 3 dias usando estas técnicas?") — pergunta desperta curiosidade; afirmação dispara o detector de mentira.
2. **Número finito de possibilidades**: "existem basicamente 7 gargalos possíveis..." (idealmente ≤10). Reduz a ansiedade do infinito para o administrável.
3. **Declarações se-então** inclusivas, uma por tema do Deep Dive ("Se você luta com tráfego frio... se tem um funil que não converte... então...").
4. **Descartar o tamanho-único**: "não existe resposta única para todos" — universal, verdadeiro, e justifica a existência do quiz.
5. **Credibilidade sem se gabar**: "Se você não acompanha futebol, talvez não saiba que o treinador responsável por X é..." (fato informado, não vanglória).
6. **Por que a ferramenta existe e por que é grátis**: arco universal — "eu fazia isso 1-a-1, ficou caro/inviável escalar, transformei numa ferramenta online".
7. **CTA único**: um botão grande que inicia o quiz (teste do desfoque: a 3 metros da tela, só o CTA deve se destacar). Cabeçalho mínimo (<1 polegada), logos de mídia em semitransparência.

### 5. Prescrição pós-quiz (Prescrever) — a página de resultado

Estrutura **Problema → Agitar → Solução**:
1. **Agradecer** a pesquisa e reconhecer a inteligência da decisão.
2. **Diagnosticar com RÓTULO nomeado**: "seu gargalo nº 1 é o que eu chamo de *Maldição do Tráfego Frio*" — rótulo novo e curioso força a pergunta "o que é isso?". O rótulo varia por bucket.
3. **Explicar o que o diagnóstico significa** (a fase Agitar — não encurte): demonstre que (a) você ENTENDE (descreva os sintomas em detalhe vívido, com a linguagem do Deep Dive — reação-alvo: "é como se você lesse meu diário"); (b) o problema é URGENTE; (c) você se IMPORTA genuinamente.
4. **Recomendar a solução** no contexto das alternativas, com os 6 elementos: grande benefício, oferta, bônus, preço, garantia, razão para agir agora.
- Preço, carrinho e copy ficam OCULTOS até o vídeo apresentar a solução.
- Depoimentos: exibidos por escrito na tela, mas só resumidos em voz (ler depoimento literal derruba a retenção do vídeo — testado).
- Mesmo bucket pode receber prescrições calibradas por variável de personalização (negócio de $100K → curso DIY; $1M+ → serviço done-for-you).

### 6. Lucro e Pivô (contexto pós-venda)

- **Upsell 1-click** logo após a compra, em 3 frameworks: (1) mais valor/volume com desconto; (2) velocidade e facilidade (coaching, software, done-for-you); (3) future-pacing de um problema "bom" que a pessoa ainda não tem. Recusou? **Downsell "quase tão bom"**: 80% do resultado a 20% do custo. Oferta única tem que ser única de verdade.
- **Sequência de não-compradores** (12 e-mails): resultados prometidos → 3 histórias → urgência → FAQ → depoimento → último dia → Do You Hate Me → reabertura/webinar → FAQ final → Pivot Survey. Os 4 e-mails do meio miram 4 psicologias de comprador (impulsivo, analítico, emotivo/história, procrastinador). 25–75% das vendas vêm do e-mail.
- As respostas do quiz alimentam tudo isso via merge fields e listas segmentadas.

## Regras operacionais

1. **NUNCA pule o Deep Dive e vá direto pro quiz.** É o maior erro da implementação: quem conhece o mercado acha que sabe os buckets — e erra (o próprio Ryan errou o palpite no caso do livro). Sem dados, buckets são hipóteses e devem ser tratadas como tal (o "Outro" vira o termômetro de validação).
2. **3–5 buckets cobrindo ~80% do mercado.** Cada bucket a mais = mais trabalho e complexidade; "a complexidade mata o projeto antes de decolar". 100% de cobertura é impossível — outliers exigiriam soluções individuais.
3. Bucket só existe se **muda a mensagem, o produto, ou ambos**. Dois buckets com a mesma prescrição = um bucket.
4. Pergunte o **maior desafio**, nunca "o que você quer" — pessoas respondem com precisão apenas (a) o que NÃO querem e (b) comportamento passado; o que "querem" é especulação.
5. **Randomize a ordem das opções** de múltipla escolha (viés de primazia/recência) — exceto a opção aberta/"Outro", que fica por último.
6. Na pesquisa aberta, **feio de propósito**: apresentação bonita atrai curioso; feia filtra quem se importa com o tema (viés de resposta a seu favor).
7. **Sem incentivo caro** (iPad, vale-presente): enviesa os dados para caçadores de brinde. Único incentivo válido: a promessa da solução, ou desconto/acesso antecipado NA solução.
8. Espere **degradação de resposta** (~60–70% chegam à 5ª pergunta): priorize as perguntas mais importantes primeiro (depois da Engraxar Rodas).
9. Toda resposta coletada no quiz **tem que ser usada** — na pergunta seguinte (colchetes), na prescrição, ou no follow-up. Pergunta cuja resposta não muda nada sai.
10. **Contato (nome/e-mail) só no fim**, em troca do diagnóstico. Telefone só na pesquisa aberta, com promessa explícita de não vender.
11. Padrão **"pragmático", não acadêmico**: direcionalmente correto > significância estatística. Mercado anda rápido demais pra esperar p<0,001.
12. Headline e gancho **em forma de pergunta**, nunca afirmação (detector de mentira).
13. No vídeo de vendas, **não leia depoimentos literalmente** — mostre escrito, resuma em voz.
14. Use a fórmula com **integridade**: diagnóstico a serviço do cliente E do vendedor. Se a intenção é manipular, o método não é pra você (aviso do próprio autor).

## Vocabulário

- **SMIQ (Single Most Important Question)** — a pergunta aberta que abre o Deep Dive: "qual seu maior desafio nº 1 com X agora?"
- **Hiper-responsivo** — os 20% do mercado com maior SCORE (resposta longa + telefone); quem realmente compra. Os buckets nascem deles, não da média.
- **Bucket (balde)** — segmento do mercado definido pelo problema central que quer resolver; recebe mensagem/produto próprios.
- **Micro-compromisso** — passo minúsculo e não-ameaçador que cria ímpeto de ação até o pedido de contato.
- **Pergunta Engraxar as Rodas (Grease the Wheels)** — a primeira pergunta do quiz: binária, trivial, sem reflexão.
- **Pergunta de Segmentação** — a última pergunta do quiz; suas opções são os buckets; determina o diagnóstico.
- **Deep Dive Survey** — pesquisa aberta de preparação, rodada uma vez, que revela buckets e linguagem.
- **Do You Hate Me Survey** — e-mail a não-compradores para colher objeções ("foi algo que eu disse... ou você me odeia? :-)").
- **Pivot Survey** — e-mail "o que você quer que eu venda a seguir: A, B ou C?"; reinicia o funil.
- **Prescrição / venda na mesma visita** — página pós-quiz que entrega o diagnóstico e transiciona para a oferta.
- **Rótulo (label)** — nome próprio dado ao diagnóstico de cada bucket ("Maldição do Tráfego Frio"); gera curiosidade e posse.
- **Suborno ético** — brinde (relatório/kit) ligado à solução, oferecido em troca da pesquisa aberta em tráfego frio.
- **Avatar** — descrição composta do cliente ideal (demografia); diz quem é, não o que compra.

## Exemplos canônicos

1. **Agência do Ryan (o exemplo-fio-condutor do livro).** Deep Dive na lista → 4 buckets cobrindo 73% do mercado (perto o bastante dos 80%): (1) vender para vários submercados; (2) fazer tráfego pago converter; (3) consertar funil existente; (4) entrar em mercado novo. Quiz de 6 perguntas: engraxar rodas (tempo integral?), tipo de negócio, situação de tráfego, situação de lista, faturamento, segmentação (recapitulando tudo + "Outro"). Nenhum dos buckets era o que ele esperava.
2. **RocketMemory (mercado novo, sem lista).** Landing temporária "Total Memory Improvement" + AdWords ("como melhorar a memória") + kit grátis como suborno ético + dupla pergunta aberta ("qual sua pergunta mais importante sobre memória? e o que te fez buscar a resposta HOJE?").
3. **Dor nas costas (o poder do LEN).** "Minhas costas doem" vs. o parágrafo do acidente de carro, fisioterapia, morfina, desemprego. O segundo compra. Por isso comprimento de resposta = proxy de compra.
4. **Casos de resultado** (caps. 19–20, referência rápida): instrução de tênis — zero a $250K em 6 meses; ionizadores de água — $750K em 5 dias. No caso do tênis, o Deep Dive revelou que o cliente hiper-responsivo tinha 64 anos, não 55 — refazer avatar, anúncios e referências nostálgicas da década certa disparou abertura, cliques e vendas.

## Contra-intuitivos

1. **O que as pessoas dizem querer não é o que compram.** Só respondem com precisão o que não querem e o que já fizeram. Por isso a SMIQ pergunta desafio, não desejo.
2. **A média do mercado não importa.** Os buckets saem dos 20% hiper-responsivos. Desenhar para a média é desenhar para quem não compra.
3. **Seu palpite sobre os buckets está errado** — mesmo com anos de mercado. O Ryan, com dezenas de mercados nas costas, errou o dele. "Mente de iniciante": deixe os dados decidirem.
4. **Feio converte melhor** (na pesquisa aberta): apresentação feia filtra a favor de quem se importa.
5. **Menos é mais duas vezes**: menos opções por pergunta = mais respostas; menos buckets = mais resultado (3–5 entregam 80% do valor da segmentação).
6. **Demografia é personalização, não segmentação.** Segmentar por problema central bate segmentar por idade/sexo/renda — os problemas atravessam a demografia; a solução prescrita é que se calibra.
7. **Perguntar mais antes de pedir contato AUMENTA o opt-in** — o oposto do instinto de "quanto menos atrito, melhor". Micro-compromissos criam ímpeto; pedir e-mail de cara dispara fuga.
8. **Pedir telefone melhora os dados** (não a lista): é multiplicador de pontuação de quem realmente compra — desde que com a promessa "não vou te vender nada".
9. **Uma máquina não categoriza buckets.** A análise das respostas abertas exige julgamento humano imersivo (a analogia da Times Square: deixar a massa passar por você até formar impressões). Terceirizável para uma pessoa, não para um software.
