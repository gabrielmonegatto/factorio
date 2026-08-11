#!/usr/bin/env node
// DOJO — dicionário de golpes + drills + sistema de faixas (boxe/kickboxing).
// 3 bancos relacionais: Faixas (progressão) ← Técnicas (dicionário) ← Drills (repetição).
// Fontes: trainingcenter/treino-boxe (boxe.db, curriculo_boxe.md, Boxing Canada) e
//         trainingcenter/treino-chutes (chutes.db, curriculo_chutes.md).
// Sistema de faixas inspirado no IKS do Shane Fazen (FIGHTTIPS/MAGNVS): a faixa se GANHA
// cumprindo técnicas + drills + um teste de passagem, não por tempo de casa.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const LIFE_SYSTEM = 'b9e16270-1b1c-463c-95bd-d7778ed94ab7';
const DB_METAS = '3a7f06f1-0ce3-8153-a258-ebbff106eab9';
const META_AM = '3a7f06f1-0ce3-8191-9734-f277e55092b0'; // Maestria: Artes Marciais
const DB_ICON = { type: 'external', external: { url: 'https://www.notion.so/icons/database_green.svg' } };

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, body, method = 'POST') {
  for (let t = 1; ; t++) {
    await sleep(360);
    try {
      const res = await fetch(`https://api.notion.com/v1/${path}`, {
        method,
        headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const json = await res.json();
      if (!res.ok) { console.error(`✗ ${method} ${path}:`, JSON.stringify(json).slice(0, 400)); throw new Error(json.message); }
      return json;
    } catch (e) { if (t >= 4 || e.message !== 'fetch failed') throw e; await sleep(t * 3000); }
  }
}

const txt = c => [{ type: 'text', text: { content: String(c).slice(0, 1900) } }];
const title = c => ({ title: txt(c) });
const sel = n => ({ select: { name: n } });
const rel = ids => ({ relation: ids.filter(Boolean).map(id => ({ id })) });
const rtx = c => ({ rich_text: txt(c) });

const yt = v => `https://www.youtube.com/watch?v=${v}`;

// ── 0. página Dojo ─────────────────────────────────────────────────────
console.log('▸ criando página "Dojo" no Life System...');
const dojo = await api('pages', {
  parent: { type: 'page_id', page_id: LIFE_SYSTEM },
  icon: { type: 'emoji', emoji: '🥊' },
  properties: { title: title('Dojo') },
  children: [
    { object: 'block', type: 'callout', callout: {
      icon: { type: 'emoji', emoji: '🥊' },
      color: 'gray_background',
      rich_text: txt('Dicionário de golpes e drills de boxe/kickboxing + sistema de faixas. A faixa se GANHA: cumpre as técnicas exigidas, roda os drills, passa no teste. Inspirado no IKS (Shane Fazen / FIGHTTIPS). Fonte dos vídeos: boxe.db (1.482) e chutes.db (1.069) em Desktop\\trainingcenter.') } },
  ],
});
console.log(`  ✓ ${dojo.id}`);

// ── 1. banco FAIXAS ────────────────────────────────────────────────────
console.log('▸ criando banco Faixas...');
const dbFaixas = await api('databases', {
  parent: { type: 'page_id', page_id: dojo.id },
  icon: DB_ICON,
  title: txt('Faixas'),
  description: txt('O sistema de progressão. Cada faixa exige um conjunto de Técnicas dominadas + Drills rodados + um teste de passagem. % Domínio é automático (rollup do checkbox Dominado das Técnicas).'),
  properties: {
    'Faixa': { title: {} },
    'Nível': { number: {} },
    'Estado': { select: { options: [
      { name: '🔒 Trancada', color: 'gray' },
      { name: '🥊 Em curso', color: 'blue' },
      { name: '🏅 Conquistada', color: 'green' },
    ]}},
    'Duração alvo': { rich_text: {} },
    'Foco': { rich_text: {} },
    'Teste de passagem': { rich_text: {} },
    'Meta': { relation: { database_id: DB_METAS, type: 'dual_property', dual_property: {} } },
  },
});
console.log(`  ✓ ${dbFaixas.id}`);

// ── 2. banco TÉCNICAS ──────────────────────────────────────────────────
console.log('▸ criando banco Técnicas...');
const dbTec = await api('databases', {
  parent: { type: 'page_id', page_id: dojo.id },
  icon: DB_ICON,
  title: txt('Técnicas'),
  description: txt('O dicionário. 1 linha = 1 golpe, defesa, deslocamento ou conceito. Marque o checkbox Dominado quando virar reflexo — é ele que move o % da Faixa.'),
  properties: {
    'Técnica': { title: {} },
    'Nº': { rich_text: {} },
    'Modalidade': { select: { options: [
      { name: 'Boxe', color: 'red' },
      { name: 'Muay Thai', color: 'orange' },
      { name: 'Kickboxing', color: 'yellow' },
      { name: 'Taekwondo', color: 'purple' },
    ]}},
    'Categoria': { select: { options: [
      { name: 'Base', color: 'brown' },
      { name: 'Ataque', color: 'red' },
      { name: 'Defesa', color: 'blue' },
      { name: 'Footwork', color: 'green' },
      { name: 'Clinch', color: 'purple' },
      { name: 'Conceito', color: 'gray' },
    ]}},
    'Domínio': { select: { options: [
      { name: '📥 Fila', color: 'gray' },
      { name: '🔁 Treinando', color: 'blue' },
      { name: '✅ Dominado', color: 'green' },
    ]}},
    'Dominado': { checkbox: {} },
    'Faixa': { relation: { database_id: dbFaixas.id, type: 'dual_property', dual_property: {} } },
    'Mecânica': { rich_text: {} },
    'Erros comuns': { rich_text: {} },
    'Também chamado': { rich_text: {} },
    'Vídeo': { url: {} },
  },
});
console.log(`  ✓ ${dbTec.id}`);

// ── 3. banco DRILLS ────────────────────────────────────────────────────
console.log('▸ criando banco Drills...');
const dbDrills = await api('databases', {
  parent: { type: 'page_id', page_id: dojo.id },
  icon: DB_ICON,
  title: txt('Drills'),
  description: txt('Como se repete. 1 linha = 1 exercício de repetição, ligado às Técnicas que ele treina e à Faixa que o exige. Round padrão: 3 min trabalho / 1 min descanso.'),
  properties: {
    'Drill': { title: {} },
    'Tipo': { select: { options: [
      { name: 'Sombra', color: 'blue' },
      { name: 'Saco', color: 'red' },
      { name: 'Footwork', color: 'green' },
      { name: 'Follow-along', color: 'purple' },
      { name: 'Padwork virtual', color: 'pink' },
      { name: 'Flexibilidade', color: 'yellow' },
      { name: 'Condicionamento', color: 'orange' },
      { name: 'Aula', color: 'brown' },
      { name: 'Sparring', color: 'gray' },
    ]}},
    'Formato': { rich_text: {} },
    'Faixa': { relation: { database_id: dbFaixas.id, type: 'dual_property', dual_property: {} } },
    'Técnicas': { relation: { database_id: dbTec.id, type: 'dual_property', dual_property: {} } },
    'Como fazer': { rich_text: {} },
    'Vídeo': { url: {} },
  },
});
console.log(`  ✓ ${dbDrills.id}`);

// ── 4. renomear back-relations ─────────────────────────────────────────
console.log('▸ arrumando back-relations...');
async function renomear(dbId, match, novo) {
  const d = await api(`databases/${dbId}`, null, 'GET');
  const ren = {};
  for (const [nome, p] of Object.entries(d.properties))
    if (p.type === 'relation' && nome.toLowerCase().includes(match.toLowerCase()) && nome.includes('(')) ren[nome] = { name: novo };
  if (Object.keys(ren).length) { await api(`databases/${dbId}`, { properties: ren }, 'PATCH'); return Object.keys(ren)[0]; }
  return null;
}
await renomear(dbFaixas.id, 'Técnicas', 'Técnicas');
await renomear(dbFaixas.id, 'Drills', 'Drills');
await renomear(dbTec.id, 'Drills', 'Drills');
await renomear(DB_METAS, 'Faixas', 'Faixas');

// rollup de % de domínio na Faixa
console.log('▸ adicionando rollups na Faixa...');
await api(`databases/${dbFaixas.id}`, { properties: {
  '% Domínio': { rollup: { relation_property_name: 'Técnicas', rollup_property_name: 'Dominado', function: 'percent_checked' } },
  'Técnicas exigidas': { rollup: { relation_property_name: 'Técnicas', rollup_property_name: 'Técnica', function: 'count' } },
}}, 'PATCH');
console.log('  ✓ % Domínio + Técnicas exigidas');

// ── 5. FAIXAS ──────────────────────────────────────────────────────────
const FAIXAS = [
  ['Branca', 1, '🥊 Em curso', '10 semanas',
   'Postura, os dois diretos, o gancho da frente, defesa básica e o chute que mais se usa. Aqui você para de pensar no básico.',
   'Sem parar: 3 rounds de sombra (3min/1min) executando 1, 2, 1-2, 1-2-3, teep e roundhouse com guarda no lugar e retorno da mão. Gravar de frente e de lado, e conferir os erros comuns de cada técnica.'],
  ['Azul', 2, '🔒 Trancada', '12 semanas',
   'Arsenal completo: uppercuts, gancho de trás, golpe no corpo, low kick e joelhada. Defesa que sai do lugar (duck, pull).',
   '5 rounds de sombra com combinações de 3 a 4 golpes misturando mão e perna, sem repetir sequência. 3 rounds de saco com low kick e body kick.'],
  ['Roxa', 3, '🔒 Trancada', '16 semanas',
   'Contra-ataque, feint e ângulo. Aqui você deixa de só atacar e passa a responder.',
   '6 rounds: 3 de padwork virtual (seguir os combos chamados sem atrasar) + 3 de sombra focada em contragolpe e saída lateral após atacar.'],
  ['Marrom', 4, '🔒 Trancada', '20 semanas',
   'Ritmo, distância e economia: entrar e sair, golpear recuando, criar ângulo com shift. Velocidade.',
   '8 rounds contínuos mantendo técnica no último igual ao primeiro. Teste de distância: acertar o teep no alvo sempre no mesmo alcance.'],
  ['Preta', 5, '🔒 Trancada', 'sem prazo',
   'Aplicação. Sparring leve, leitura do oponente e capacidade de ensinar o que sabe.',
   'Sparring técnico controlado sem perder a estrutura, e conseguir explicar/corrigir cada técnica do dicionário para outra pessoa.'],
];
console.log(`▸ inserindo ${FAIXAS.length} faixas...`);
const F = {};
for (const [nome, nivel, estado, dur, foco, teste] of FAIXAS) {
  const p = await api('pages', { parent: { database_id: dbFaixas.id }, properties: {
    'Faixa': title(nome), 'Nível': { number: nivel }, 'Estado': sel(estado),
    'Duração alvo': rtx(dur), 'Foco': rtx(foco), 'Teste de passagem': rtx(teste),
    'Meta': rel([META_AM]),
  }});
  F[nome] = p.id;
}
console.log(`  ✓ ${Object.keys(F).length} faixas`);

// ── 6. TÉCNICAS ────────────────────────────────────────────────────────
// [nome, nº, modalidade, categoria, faixa, também chamado, mecânica, erros, vídeo]
const B = 'Boxe', MT = 'Muay Thai', TKD = 'Taekwondo';
const TECNICAS = [
  // ---------- BASE
  ['Postura de boxe', '', B, 'Base', 'Branca', 'stance / guarda',
   'Pé da frente apontando pro alvo, pé de trás a ~45°, largura de ombros e um passo de distância. Joelhos moles, peso 50/50 nos metatarsos. Queixo pra baixo, mãos na altura da maçã do rosto, cotovelos colados nas costelas.',
   'Pés na mesma linha (perde equilíbrio lateral) ou muito abertos (não anda). Calcanhar de trás no chão. Ombros levantados e tensos. Ficar de perfil demais: tira o cross do jogo.',
   yt('PLU3-tlD3y4')],
  ['Postura de Muay Thai', '', MT, 'Base', 'Branca', 'stance thai',
   'Mais frontal e mais alta que a de boxe, peso levemente atrás pra poder levantar a perna da frente a qualquer momento. Mãos mais altas e à frente do rosto, cotovelos fechados. Quique leve, nunca peso morto no calcanhar.',
   'Copiar a postura de boxe (baixa e de lado): trava o teep e você come low kick. Ficar de base larga demais, sem conseguir checar.',
   yt('640rsP_0WgY')],

  // ---------- BOXE ATAQUE
  ['Jab', '1', B, 'Ataque', 'Branca', 'direto da frente',
   'Sai reto do queixo pelo caminho mais curto, sem carregar. Gira o punho no impacto e o ombro sobe pra proteger o queixo. Volta pela mesma linha mais rápido do que foi. O jab mede e abre: não é pra derrubar.',
   'Puxar a mão pra trás antes de sair (telegrafa). Deixar a mão cair na volta. Travar o cotovelo no fim. Prender a respiração: solta o ar curto no impacto.',
   yt('FSVcmMd9bR4')],
  ['Cross', '2', B, 'Ataque', 'Branca', 'direto de trás / straight right',
   'Gira o pé de trás como se esmagasse um cigarro, o quadril acompanha e a mão sai reta atrás. A força vem do chão e da rotação, não do braço. Queixo atrás do ombro que golpeia.',
   'Bater só com o braço, sem girar quadril. Jogar o corpo pra frente e sair do eixo. Baixar a mão da frente na hora do golpe.',
   yt('sK-6Ujp3KYY')],
  ['1-2', '1-2', B, 'Ataque', 'Branca', 'jab + cross',
   'O cross começa antes do jab voltar por completo: as duas mãos se cruzam no meio do caminho. Os pés reposicionam junto, nunca cruzam. É a combinação mais usada do boxe.',
   'Esperar o jab voltar inteiro (perde o tempo). Parar e admirar depois do 2 em vez de sair ou continuar.',
   yt('vyTaKpylOcU')],
  ['Lead hook', '3', B, 'Ataque', 'Branca', 'cruzado de frente',
   'Braço em L com o cotovelo na altura do punho. Gira o pé e o quadril da frente; o braço só acompanha. Curto: se esticar vira tapa e perde a força.',
   'Abrir o braço (vira swing e telegrafa). Baixar a mão antes pra "carregar". Cotovelo abaixo do punho: o pulso dobra no impacto.',
   yt('i3G3HsI1GGU')],
  ['Rear hook', '4', B, 'Ataque', 'Azul', 'cruzado de trás',
   'Mesma mecânica do lead hook, mas girando o pé e o quadril de trás. Percurso maior, então só entra depois que algo abriu a guarda: raramente é o primeiro golpe.',
   'Usar como golpe de entrada (chega tarde demais e você toma o contra). Girar demais e ficar de costas pro oponente.',
   yt('NRFqnAOpgQw')],
  ['Lead uppercut', '5', B, 'Ataque', 'Azul', 'uppercut de frente',
   'Flexiona levemente o joelho da frente, deixa a mão cair um pouco e sobe em linha reta pelo meio da guarda, palma pra você. O impulso é das pernas subindo.',
   'Abaixar demais antes de subir. Abrir o cotovelo pra fora (vira gancho de baixo torto). Perder a guarda de trás enquanto sobe.',
   yt('zl2bZwxM_ws')],
  ['Rear uppercut', '6', B, 'Ataque', 'Azul', 'uppercut de trás',
   'Gira o quadril de trás e sobe pelo meio, entre os braços do oponente. Vive de distância curta: de longe não alcança e te deixa aberto.',
   'Jogar de longe. Recuar o braço antes pra ganhar impulso. Levantar o queixo junto com o golpe.',
   yt('iInkodqd5pE')],
  ['Overhand', '', B, 'Ataque', 'Azul', 'overhand right / cruzado por cima',
   'Direito que descreve um arco por cima da guarda, com inclinação do tronco pra fora da linha de ataque. Serve contra quem mantém a guarda alta e fechada.',
   'Virar um "swing de rua" sem rotação de quadril. Fechar os olhos e mergulhar de cabeça.',
   yt('h7Sv6fzSSkQ')],
  ['Shovel hook', '', B, 'Ataque', 'Roxa', 'gancho de pá',
   'Meio termo entre gancho e uppercut, a 45°, mirando as costelas e o fígado. Cotovelo perto do corpo, entra por dentro dos braços do oponente.',
   'Fazer de longe. Baixar a cabeça pra frente ao entrar (encontra o joelho ou o uppercut).',
   yt('_LKGaPiU4Ho')],
  ['Double jab', '', B, 'Ataque', 'Roxa', 'jab duplo',
   'Dois jabs seguidos: o primeiro mede e ocupa a visão, o segundo entra com passo e peso. Ritmo desigual (rápido-pausa-forte) é o que engana.',
   'Dar os dois com a mesma força e cadência (vira aviso). Não acompanhar com o pé no segundo.',
   yt('mhlkn88S-hY')],
  ['Check hook', '', B, 'Ataque', 'Roxa', 'gancho de saída',
   'Gancho da frente jogado enquanto você pivota pra fora, contra quem avança em linha reta. Ataque e saída no mesmo movimento.',
   'Pivotar depois de bater em vez de junto. Usar contra quem não está avançando: não tem o que aproveitar.',
   yt('yZ_gLhusT2s')],
  ['Golpe no corpo', '', B, 'Ataque', 'Azul', 'body punching',
   'Dobra os joelhos pra descer o corpo inteiro, não a cabeça. O golpe sai na mesma mecânica de cima, só que na altura das costelas. Gasta o gás do oponente e faz a guarda descer.',
   'Curvar a coluna em vez de flexionar as pernas. Descer sem cobrir a cabeça: é onde se toma joelhada e uppercut.',
   yt('rOH5yKFIILU')],
  ['Liver shot', '', B, 'Ataque', 'Roxa', 'golpe no fígado',
   'Gancho ou shovel hook da frente logo abaixo das costelas do lado direito do oponente. Golpe de parada: dói com atraso e trava a respiração.',
   'Mirar alto demais (bate no cotovelo) ou baixo demais (bate no quadril).',
   yt('7H0qK_lelwg')],

  // ---------- BOXE DEFESA
  ['Guarda alta', '', B, 'Defesa', 'Branca', 'block / high guard',
   'Punhos na altura das sobrancelhas, cotovelos fechados cobrindo as costelas, olhos entre as luvas. Absorve com o antebraço, sem empurrar a luva contra o golpe.',
   'Guarda passiva o tempo todo (só toma). Afastar as luvas do rosto: o golpe empurra sua mão contra você.',
   yt('Hr2R7N5NJDo')],
  ['Parry', '', B, 'Defesa', 'Branca', 'aparar',
   'Toque curto e seco na mão que vem, desviando a linha do golpe. Movimento mínimo: desvia, não bate. Deixa o oponente aberto pro contra imediato.',
   'Dar um tapão amplo e abrir a própria guarda. Esticar o braço pra buscar o golpe.',
   yt('SGai4lbnpcM')],
  ['Slip', '', B, 'Defesa', 'Branca', 'esquiva lateral',
   'Rotação curta do tronco tirando a cabeça da linha reta, com os olhos sempre no oponente. Move só o necessário: alguns centímetros bastam.',
   'Esquivar com a cintura pra trás (perde o contra). Fechar os olhos. Slipar sempre pro mesmo lado: vira padrão previsível.',
   yt('nP2rbvSe38A')],
  ['Duck / roll', '', B, 'Defesa', 'Azul', 'agachar e rolar',
   'Flexiona as pernas pra passar por baixo do golpe circular e sobe do outro lado, já em posição de contra-atacar. Cabeça nunca sai da linha do corpo.',
   'Abaixar só a cabeça pra frente. Descer e ficar parado embaixo. Rolar sem ir pra lugar nenhum.',
   yt('7Vor1MSQxfw')],
  ['Pull', '', B, 'Defesa', 'Azul', 'recuo de tronco',
   'Joga o peso pro pé de trás, tirando o rosto do alcance sem mover os pés. O golpe passa raspando e você volta na mesma hora com o contra.',
   'Recuar em linha reta repetidas vezes (te encurralam). Levantar o queixo ao recuar.',
   yt('jca5U-ZqRPw')],
  ['Bloqueio de uppercut', '', B, 'Defesa', 'Roxa', '',
   'Mão desce em pá com a palma pra baixo, encontrando o golpe que sobe antes que ele chegue ao queixo. Cotovelo continua fechado.',
   'Baixar a mão cedo demais e abrir o rosto pro direto. Recuar a cabeça pra cima (encontra o golpe).',
   yt('dUkyFSLVipA')],
  ['Bloqueio de corpo', '', B, 'Defesa', 'Azul', '',
   'Cotovelo desce e fecha contra a costela do lado atacado, sem mudar a altura da mão. Absorve com o osso do cotovelo e antebraço.',
   'Baixar a mão junto com o cotovelo e abrir a cabeça. Girar o tronco de frente pro golpe.',
   yt('uCSwxyhV89U')],
  ['Defesa de golpe forte', '', B, 'Defesa', 'Azul', 'defense for power shots',
   'Contra golpe pesado, combina cobertura com deslocamento: bloqueia e sai do eixo ao mesmo tempo. Nunca só apara de pé firme.',
   'Ficar parado confiando na guarda. Recuar reto na linha do golpe.',
   yt('vMuJCFlH7Eo')],
  ['Movimento de cabeça', '', B, 'Defesa', 'Roxa', 'head movement',
   'Cabeça nunca fica dois tempos no mesmo lugar: alterna slip, pull e leve deslocamento enquanto se aproxima e enquanto ataca.',
   'Movimentar a cabeça só quando o golpe já vem. Balançar em ritmo fixo (vira alvo previsível).',
   yt('74NBtPfWoUo')],

  // ---------- BOXE FOOTWORK
  ['Passo frente e trás', '', B, 'Footwork', 'Branca', 'step and drag',
   'O pé mais próximo da direção vai primeiro, o outro arrasta atrás recuperando a base. A distância entre os pés nunca muda.',
   'Cruzar os pés. Saltar com os dois ao mesmo tempo. Ficar de base larga demais depois do passo.',
   yt('Zlm-CWo9g_4')],
  ['Movimento lateral', '', B, 'Footwork', 'Branca', 'lateral motion',
   'Mesma lógica lateral: pé do lado do movimento sai, o outro recupera. Andar pro lado de fora do pé de trás do oponente é o caminho mais seguro.',
   'Cruzar as pernas. Andar sempre pro mesmo lado. Parar de mexer as mãos enquanto anda.',
   yt('h7Sv6fzSSkQ')],
  ['Pivot', '', B, 'Footwork', 'Branca', 'giro sobre o pé da frente',
   'Gira sobre o metatarso do pé da frente levando o pé de trás em arco: muda o ângulo sem mudar a distância. Sai da linha de ataque e deixa o oponente de lado pra você.',
   'Pivotar sobre o calcanhar. Levantar a guarda do lugar durante o giro. Girar demais e ficar de costas.',
   yt('MnpuVl5J1zs')],
  ['Pendulum step', '', B, 'Footwork', 'Azul', 'passo pêndulo',
   'Balanço rítmico pra frente e pra trás que mantém você sempre em movimento: entra na distância no tempo em que o oponente sai, e vice-versa.',
   'Virar um pula-pula sem intenção. Ficar previsível no ritmo do balanço.',
   yt('Zlm-CWo9g_4')],
  ['L-step', '', B, 'Footwork', 'Azul', 'step off',
   'Depois do jab (ou do jab duplo), o pé da frente sai em L pro lado, criando ângulo novo enquanto o oponente ainda responde à linha antiga.',
   'Sair antes de terminar o golpe. Dar o passo curto demais pra mudar o ângulo de verdade.',
   yt('3IadvcoAX8g')],
  ['Gazelle step', '', B, 'Footwork', 'Roxa', 'passo gazela',
   'Impulso explosivo do pé de trás que cobre distância longa com o golpe da frente: usado pra entrar de fora do alcance direto pra dentro.',
   'Pular com os dois pés juntos. Chegar sem base pra continuar a combinação.',
   yt('SGai4lbnpcM')],
  ['Crosswalking', '', B, 'Footwork', 'Roxa', '',
   'Deslocamento em que os pés trocam de posição de forma controlada pra cobrir terreno rápido mantendo a possibilidade de golpear.',
   'Cruzar os pés no momento errado e ficar sem base pra golpear ou defender.',
   yt('Hr2R7N5NJDo')],
  ['Shift / switch step', '', B, 'Footwork', 'Marrom', 'troca de base',
   'Troca o pé da frente durante o ataque, criando ângulo novo e transformando o golpe de trás em golpe da frente. Muda toda a geometria da troca.',
   'Trocar a base parado, sem golpe junto: fica só exposto. Perder o alinhamento do quadril.',
   yt('CrB_ih_YdU4')],
  ['Sair depois de atacar', '', B, 'Footwork', 'Roxa', 'get out',
   'Toda combinação termina com uma saída: passo pra trás com ângulo ou pivot. Ficar parado depois de atacar é onde a maioria toma o contra.',
   'Admirar o próprio golpe. Sair reto pra trás na mesma linha em que atacou.',
   yt('UAyoU8thj9M')],

  // ---------- BOXE CONCEITO
  ['Feint', '', B, 'Conceito', 'Roxa', 'finta',
   'Início de movimento verdadeiro que não vira golpe: ombro, olhar, pé ou meio-jab. Serve pra provocar reação e atacar a abertura que ela cria.',
   'Fintar sem intenção (não engana ninguém). Fintar e não ter plano pro que vem depois.',
   yt('6xHnO1zAVrI')],
  ['Contra-ataque', '', B, 'Conceito', 'Roxa', 'counter punching',
   'Responder no tempo em que o oponente ainda está estendido. Cada defesa tem um contra natural: parry abre o cross, slip abre o gancho, pull abre o direto.',
   'Defender e só depois pensar em atacar (tarde). Contra-atacar sempre com o mesmo golpe.',
   yt('Kor1Wj3XZiY')],
  ['Pull counter', '', B, 'Conceito', 'Marrom', '',
   'Recua o tronco pro golpe passar e devolve o direto no exato momento em que a mão do oponente volta. Timing puro.',
   'Recuar cedo demais (ele corrige a distância). Devolver depois que ele já recompôs a guarda.',
   yt('jca5U-ZqRPw')],
  ['Entrar e sair', '', B, 'Conceito', 'Marrom', 'in and out boxing',
   'Vive fora do alcance, entra com a combinação e sai antes da resposta. Exige leitura de distância e pernas descansadas.',
   'Entrar sem plano de saída. Ficar na distância média, que é onde se toma tudo.',
   yt('U_J2ZkpjRAU')],
  ['Velocidade', '', B, 'Conceito', 'Marrom', '',
   'Velocidade vem de relaxamento e economia de trajeto, não de força. Punho fecha só no impacto, ombros soltos, sem movimento preparatório.',
   'Tentar ser rápido com o corpo tenso. Confundir velocidade de braço com velocidade de reação.',
   yt('yugiN3PQaFM')],
  ['Golpear recuando', '', B, 'Conceito', 'Marrom', '',
   'Manter poder e precisão enquanto anda pra trás, transferindo peso no pé que apoia. Impede que o oponente avance de graça.',
   'Recuar sem golpear (convida a pressão). Cruzar os pés ao recuar.',
   yt('j_ibqwbloBE')],
  ['Sparring', '', B, 'Conceito', 'Preta', '',
   'Aplicação com parceiro em intensidade controlada. Objetivo é testar leitura e estrutura, não vencer o treino.',
   'Tratar sparring leve como luta. Abandonar tudo que treinou e virar briga de rua.',
   yt('1SECyKqds1E')],

  // ---------- CHUTES
  ['Arm swing no chute', '', MT, 'Base', 'Branca', 'mecânica do braço no chute',
   'O braço do lado que chuta desce e vai pra trás enquanto o quadril gira: é o contrapeso que dá velocidade e alcance ao chute. Sem ele o chute é só perna.',
   'Manter os dois braços na guarda e chutar só com a perna (chute fraco). Jogar o braço sem girar o quadril junto.',
   yt('3WH6VaFWnSY')],
  ['Teep', '', MT, 'Ataque', 'Branca', 'push kick / chute-empurrão',
   'Levanta o joelho, estende o quadril pra frente e empurra com a planta ou o calcanhar. É o jab das pernas: mede distância, interrompe o avanço e desequilibra. Recolhe a perna na mesma velocidade.',
   'Chutar com a ponta do pé. Deixar a perna estendida depois (te agarram). Inclinar demais pra trás e perder a base.',
   yt('a4OG796FsOc')],
  ['Roundhouse', '', MT, 'Ataque', 'Branca', 'chute rodado / round kick',
   'Passo aberto do pé de apoio, gira o pé de apoio até o calcanhar apontar pro alvo, quadril gira junto e a perna vem inteira como um taco. Bate com a canela, não com o peito do pé. O corpo todo gira, não só a perna.',
   'Não girar o pé de apoio (mata a força e machuca o joelho). Bater com o peito do pé. Chutar sem o arm swing. Ficar de pé plantado no chão.',
   yt('eGCmHcW1E0s')],
  ['Low kick', '', MT, 'Ataque', 'Azul', 'chute na perna / leg kick',
   'Mesmo roundhouse, mirando a coxa do oponente, um pouco acima do joelho. A intenção é atravessar o alvo, não parar nele. Golpe de acúmulo: destrói a mobilidade ao longo do treino.',
   'Chutar de frente sem ângulo (bate no bloqueio). Mirar o joelho por fora. Não recolher a perna depois.',
   yt('VNuWXCl_fSE')],
  ['Body kick', '', MT, 'Ataque', 'Azul', 'chute no corpo',
   'Roundhouse na altura das costelas, com o quadril bem virado pra ganhar altura. Costuma vir depois de golpes de mão que ocupam a guarda alta.',
   'Chutar com o corpo ereto (não alcança). Deixar a guarda cair no lado que chuta.',
   yt('wy_Kp-CtT78')],
  ['High kick', '', MT, 'Ataque', 'Roxa', 'chute alto',
   'Mesmo roundhouse na altura da cabeça. Exige quadril aberto: é a flexibilidade que libera esse golpe, não a força. Só entra depois que a guarda desce por causa dos golpes baixos.',
   'Forçar altura sem mobilidade (chute torto e lento). Chutar alto de cara, sem ter ameaçado embaixo.',
   yt('jO84APlNN9s')],
  ['Switch kick', '', MT, 'Ataque', 'Azul', 'chute com troca de base',
   'Troca rápida dos pés no lugar pra chutar com a perna da frente com a potência da de trás. A troca e o chute são um movimento só.',
   'Fazer a troca devagar e telegrafar. Saltar alto na troca em vez de trocar rente ao chão.',
   yt('eziZcWnjP2s')],
  ['Check', '', MT, 'Defesa', 'Branca', 'defesa de low kick',
   'Levanta o joelho e vira a canela pra fora, encontrando o chute com osso. Peso fica no pé de apoio, guarda não muda de lugar.',
   'Levantar o pé sem virar a canela (leva na panturrilha). Checar tarde. Perder o equilíbrio ao levantar a perna.',
   yt('Z3xMglkVfvw')],
  ['Joelhada', '', MT, 'Ataque', 'Azul', 'knee / kao',
   'Puxa o quadril pra frente e pra cima levando o joelho no alvo, com o braço do mesmo lado descendo em contrapeso. Arma de distância curta.',
   'Bater só levantando a perna, sem projetar o quadril. Curvar as costas pra frente e ficar de cabeça baixa.',
   yt('Tc3xCAl9Zs4')],
  ['Cotovelada', '', MT, 'Ataque', 'Roxa', 'elbow / sok',
   'Gira igual ao gancho, mas com a distância encurtada: o contato é com a ponta do cotovelo. Corta e é a arma natural do clinch.',
   'Bater com o antebraço em vez da ponta. Abrir a guarda ao girar.',
   yt('63FDy1O-3P0')],
  ['Clinch', '', MT, 'Clinch', 'Roxa', 'plum / pescoçada',
   'Mãos entrelaçadas na nuca, cotovelos fechados colados no peito do oponente, postura ereta puxando pra baixo. Quem controla a cabeça controla o corpo.',
   'Entrelaçar os dedos (machuca e trava). Cotovelos abertos (o oponente entra por dentro). Curvar pra frente e perder a base.',
   yt('EKFytLBP-Iw')],
  ['Side kick', '', TKD, 'Ataque', 'Marrom', 'chute lateral',
   'Levanta o joelho, gira o quadril de lado e estende empurrando com o calcanhar, corpo alinhado do pé de apoio ao calcanhar que bate. Serve como barreira de distância.',
   'Chutar com o pé "de pá" em vez do calcanhar. Perder o alinhamento e virar um chute torto.',
   yt('FgX0RnZy-0M')],
  ['Spinning back kick', '', MT, 'Ataque', 'Marrom', 'chute giratório',
   'Gira olhando por cima do ombro pra achar o alvo antes de estender, e empurra com o calcanhar em linha reta. Alto risco, alto retorno.',
   'Girar sem olhar (chuta o vazio e fica de costas). Usar sem preparação: é o golpe mais punível se errar.',
   yt('0qhpNLerO24')],
];

console.log(`▸ inserindo ${TECNICAS.length} técnicas...`);
const T = {};
let nt = 0, errosT = [];
for (const [nome, num, mod, cat, faixa, alias, mec, err, video] of TECNICAS) {
  const props = {
    'Técnica': title(nome), 'Modalidade': sel(mod), 'Categoria': sel(cat),
    'Domínio': sel('📥 Fila'), 'Dominado': { checkbox: false },
    'Faixa': rel([F[faixa]]), 'Mecânica': rtx(mec), 'Erros comuns': rtx(err),
  };
  if (num) props['Nº'] = rtx(num);
  if (alias) props['Também chamado'] = rtx(alias);
  if (video) props['Vídeo'] = { url: video };
  try { const p = await api('pages', { parent: { database_id: dbTec.id }, properties: props }); T[nome] = p.id; nt++; }
  catch (e) { errosT.push(`${nome} :: ${e.message}`); }
}
console.log(`  ✓ ${nt}/${TECNICAS.length} técnicas`);

// ── 7. DRILLS ──────────────────────────────────────────────────────────
// [nome, tipo, faixa, formato, como fazer, [técnicas], vídeo]
const DRILLS = [
  ['Round timer 3/1', 'Condicionamento', 'Branca', '3 min trabalho / 1 min descanso',
   'O metrônomo do treino. Todo drill roda dentro dessa estrutura: 3 minutos de trabalho contínuo, 1 minuto de descanso. Começa com 3 rounds e sobe até 12.',
   [], null],
  ['Portal — aula em ordem', 'Aula', 'Branca', '1 lição por sessão, na ordem',
   'Curso sequencial do Precision Striking, 26 lições. Assiste a lição inteira uma vez, depois repete só a parte prática. Lições #1 a #10 são o fundamento puro e sustentam a faixa branca.',
   ['Postura de boxe', 'Jab', 'Cross'], yt('wCGHLDNArrI')],
  ['Sombra por números', 'Sombra', 'Branca', '3 rounds',
   'Chama os números em voz alta e executa: 1, 2, 1-2, 1-2-3, 1-2-3-2. Repete até parar de contar e virar reflexo. É o equivalente ao rudimento de bateria.',
   ['Jab', 'Cross', '1-2', 'Lead hook'], yt('rqDulIinPM0')],
  ['Sombra estática de defesa', 'Sombra', 'Branca', '1 min por sequência',
   'Sem sair do lugar, repete: jab→duck→cross · duck→jab→cross · jab→slip→hook. Um minuto em cada, focando no encaixe entre golpe e esquiva.',
   ['Slip', 'Duck / roll', 'Jab', 'Cross'], null],
  ['Slip line', 'Sombra', 'Branca', '3 rounds',
   'Corda ou elástico esticado na altura dos ombros: passa por baixo esquivando pra um lado e pro outro enquanto golpeia. Ensina a esquivar sem perder a base.',
   ['Slip', 'Movimento de cabeça'], yt('k2M_aDFbFOw')],
  ['Footwork em padrão', 'Footwork', 'Branca', '3 rounds',
   'Marca um padrão no chão (fita ou linhas da quadra) e percorre: frente/trás, lateral, pivot. Sem golpear, só pé. Depois repete golpeando.',
   ['Passo frente e trás', 'Movimento lateral', 'Pivot'], yt('m7ryD1l_5qM')],
  ['Saco progressivo', 'Saco', 'Branca', '5 min',
   'Minuto 1: golpes isolados. Minuto 2: combinações de 2. Minuto 3: combinações de 3. Minutos 4 e 5: livre mantendo a técnica. A técnica cai antes do gás: quando cair, para.',
   ['Jab', 'Cross', '1-2'], yt('O-WFsfN8TOE')],
  ['Corda — boxer skip', 'Condicionamento', 'Branca', '3 a 5 rounds',
   'Pulo alternando os pés no ritmo do boxe. Aquecimento padrão antes de qualquer treino de golpe e o melhor exercício de leveza de pés.',
   ['Passo frente e trás'], yt('1-KvIEU03yc')],
  ['Alongamento dinâmico', 'Flexibilidade', 'Branca', '10 min antes de treinar',
   'Rotina de mobilidade do GNT pra abrir o quadril antes de chutar. Sempre antes, nunca depois de frio.',
   ['Roundhouse', 'Teep'], yt('OSzftunrPf0')],
  ['Sombra de Muay Thai', 'Sombra', 'Branca', '13 min',
   'Dez drills de sombra que misturam mão, teep e roundhouse. É onde o boxe e o chute viram uma coisa só.',
   ['Teep', 'Roundhouse', 'Postura de Muay Thai'], yt('uFJSSYECov4')],
  ['Teep no alvo', 'Saco', 'Branca', '3 rounds',
   'Teep repetido no saco buscando sempre a mesma altura e distância, recolhendo a perna na mesma velocidade que estendeu. Alterna perna da frente e de trás.',
   ['Teep'], yt('a4OG796FsOc')],
  ['Roundhouse no saco', 'Saco', 'Branca', '3 rounds',
   'Chute rodado no saco checando as três coisas: pé de apoio girando, arm swing e contato com a canela. Vinte de cada lado por round.',
   ['Roundhouse', 'Arm swing no chute'], yt('wy_Kp-CtT78')],
  ['Check drill', 'Footwork', 'Branca', '2 rounds',
   'Levanta a canela em posição de check alternando as pernas, mantendo guarda e equilíbrio. Depois, com parceiro ou saco, checa chutes leves.',
   ['Check'], yt('Z3xMglkVfvw')],
  ['Training camp workout', 'Follow-along', 'Azul', '30 a 45 min',
   'Treino guiado completo do Precision Striking: aquecimento, técnica e rounds. Serve como sessão pronta quando não quiser planejar nada.',
   [], yt('oKSiXDr2lzU')],
  ['Padwork virtual', 'Padwork virtual', 'Azul', '10 rounds',
   'O vídeo chama os combos e você executa no tempo dele, sem atrasar. É o teste real de se a numeração virou reflexo.',
   ['1-2', 'Lead hook', 'Rear uppercut'], yt('44L5QVrmaz8')],
  ['10 rounds 10 combos', 'Sombra', 'Azul', '10 rounds',
   'Um combo novo por round, acumulando. No décimo round você encadeia todos. Ótimo pra sair do 1-2 automático.',
   ['1-2', 'Lead hook', 'Rear hook', 'Lead uppercut'], yt('wH8GyHcCcsw')],
  ['Saco com low kick', 'Saco', 'Azul', '3 rounds',
   'Combina mão e perna no saco: sempre termina a combinação de mãos com low kick. Ensina a esconder o chute atrás dos golpes de mão.',
   ['Low kick', 'Body kick', '1-2'], yt('VNuWXCl_fSE')],
  ['Alongamento profundo', 'Flexibilidade', 'Azul', '20 min, dias de folga',
   'Rotina de flexibilidade profunda do GNT pra ganhar altura de chute. Faz nos dias sem treino de impacto, nunca antes de treinar.',
   ['High kick'], yt('jO84APlNN9s')],
  ['Head movement drill', 'Sombra', 'Roxa', '3 rounds',
   'Sombra em que a cabeça nunca fica dois tempos no mesmo lugar: entra, esquiva, golpeia e sai sempre por ângulo diferente.',
   ['Movimento de cabeça', 'Slip', 'Sair depois de atacar'], yt('74NBtPfWoUo')],
  ['Velocidade de chute', 'Flexibilidade', 'Roxa', '2 rounds',
   'Drill do GNT pra ganhar velocidade de perna: repetições rápidas sem carga, priorizando o recolhimento tão rápido quanto a extensão.',
   ['Roundhouse', 'High kick'], yt('sj_xUc39kOg')],
  ['Sombra filmada', 'Sombra', 'Branca', '1 round por ângulo',
   'Grava um round de frente e um de lado, assiste comparando com os erros comuns da técnica no dicionário. É a correção que substitui o professor quando se treina sozinho.',
   [], null],
  ['Sparring técnico', 'Sparring', 'Preta', '3 a 5 rounds leves',
   'Intensidade controlada com parceiro, focando em manter estrutura e leitura. Não é competição.',
   ['Sparring', 'Contra-ataque'], yt('1SECyKqds1E')],
];

console.log(`▸ inserindo ${DRILLS.length} drills...`);
let nd = 0, errosD = [];
for (const [nome, tipo, faixa, formato, como, tecs, video] of DRILLS) {
  const props = {
    'Drill': title(nome), 'Tipo': sel(tipo), 'Faixa': rel([F[faixa]]),
    'Formato': rtx(formato), 'Como fazer': rtx(como),
    'Técnicas': rel(tecs.map(t => T[t])),
  };
  if (video) props['Vídeo'] = { url: video };
  try { await api('pages', { parent: { database_id: dbDrills.id }, properties: props }); nd++; }
  catch (e) { errosD.push(`${nome} :: ${e.message}`); }
}
console.log(`  ✓ ${nd}/${DRILLS.length} drills`);

fs.writeFileSync(new URL('./notion-dojo-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ pagina: dojo.id, faixas: dbFaixas.id, tecnicas: dbTec.id, drills: dbDrills.id }, null, 2));

console.log(`\n✅ Dojo no ar: ${dojo.url}`);
console.log(`   Faixas   ${dbFaixas.url}`);
console.log(`   Técnicas ${dbTec.url}`);
console.log(`   Drills   ${dbDrills.url}`);
if (errosT.length) { console.log(`⚠️ técnicas com falha:`); errosT.forEach(e => console.log('   ', e)); }
if (errosD.length) { console.log(`⚠️ drills com falha:`); errosD.forEach(e => console.log('   ', e)); }
