#!/usr/bin/env node
// TREVVO 1.0 — sistema financeiro pessoal em 3 bancos (Contas / Lançamentos / Categorias)
// Aditivo: cria no cofre (Newsystem) e migra as linhas existentes. Nada é tocado nos antigos.
import fs from 'node:fs';

const ENV = 'C:/Users/Monegatto/Desktop/EternalL/_factorio/.env';
const TOKEN = fs.readFileSync(ENV, 'utf8').split(/\r?\n/)
  .find(l => l.startsWith('NOTION_TOKEN=')).slice('NOTION_TOKEN='.length).trim();

const COFRE = '3a5f06f1-0ce3-80c3-9b15-c486acb05b67'; // Newsystem

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(path, body, method = 'POST') {
  await sleep(360);
  const res = await fetch(`https://api.notion.com/v1/${path}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!res.ok) { console.error(`✗ ${method} ${path}:`, JSON.stringify(json).slice(0, 500)); throw new Error(json.message); }
  return json;
}

const txt = c => [{ type: 'text', text: { content: c } }];
const title = c => ({ title: txt(c) });
const sel = n => (n ? { select: { name: n } } : { select: null });
const date = d => (d ? { date: { start: d } } : { date: null });
const rel = ids => ({ relation: ids.map(id => ({ id })) });
const num = v => ({ number: v });

// ═══ 1-2. Categorias e Contas já criadas na tentativa anterior — reutilizar ═══
console.log('▸ 1-2/5 reutilizando bancos já criados...');
const cat    = { id: '3a7f06f1-0ce3-81a6-831c-f8f43e0fedce', url: 'https://app.notion.com/p/3a7f06f10ce381a6831cf8f43e0fedce' };
const contas = { id: '3a7f06f1-0ce3-81c8-9414-c18cc156554f', url: 'https://app.notion.com/p/3a7f06f10ce381c89414c18cc156554f' };

// ═══ 3. 💸 Lançamentos ═══
console.log('▸ 3/5 💸 Lançamentos...');
const lanc = await api('databases', {
  parent: { type: 'page_id', page_id: COFRE },
  icon: { type: 'emoji', emoji: '💸' },
  title: txt('💸 Lançamentos'),
  description: txt('TODO movimento de dinheiro é uma linha aqui. Fusão de "Entradas" + "Saídas" + "Transações Bancárias". Transferência usa Conta (origem) + Conta destino.'),
  properties: {
    'Descrição': { title: {} },
    'Tipo': { select: { options: [
      { name: 'Entrada', color: 'green' },
      { name: 'Saída', color: 'red' },
      { name: 'Transferência', color: 'blue' },
    ]}},
    'Valor': { number: { format: 'real' } },
    'Data': { date: {} },
    'Conta': { relation: { database_id: contas.id, type: 'dual_property', dual_property: {} } },
    'Conta destino': { relation: { database_id: contas.id, type: 'dual_property', dual_property: {} } },
    'Categoria': { relation: { database_id: cat.id, type: 'dual_property', dual_property: {} } },
    'Parcelas': { select: { options: Array.from({ length: 11 }, (_, i) => ({ name: String(i + 2).padStart(2, '0') + 'x' })) } },
    'Efeito': { formula: { expression: 'if(empty(prop("Valor")), 0, if(prop("Tipo") == "Entrada", prop("Valor"), -prop("Valor")))' } },
  },
});
console.log(`  ✓ ${lanc.id}`);

// ═══ 4. renomear back-relations + rollups + saldo ═══
console.log('▸ 4/5 rollups e saldo automático...');
// descobrir nomes das back-relations criadas
const contasDb = await api(`databases/${contas.id}`, null, 'GET');
const backs = Object.entries(contasDb.properties).filter(([, p]) => p.type === 'relation');
const renames = {};
for (const [name, p] of backs) {
  if (name.includes('(Conta destino)')) renames[name] = { name: 'Transferências recebidas' };
  else if (name.includes('(Conta)')) renames[name] = { name: 'Lançamentos' };
}
await api(`databases/${contas.id}`, { properties: renames }, 'PATCH');
await api(`databases/${contas.id}`, {
  properties: {
    'Movimentos': { rollup: { relation_property_name: 'Lançamentos', rollup_property_name: 'Efeito', function: 'sum' } },
    'Recebido (transf.)': { rollup: { relation_property_name: 'Transferências recebidas', rollup_property_name: 'Valor', function: 'sum' } },
  },
}, 'PATCH');
await api(`databases/${contas.id}`, {
  properties: {
    'Saldo atual': { formula: { expression: 'if(empty(prop("Saldo inicial")), 0, prop("Saldo inicial")) + prop("Movimentos") + prop("Recebido (transf.)")' } },
  },
}, 'PATCH');
// back-relation de Categorias
const catDb = await api(`databases/${cat.id}`, null, 'GET');
const catBack = Object.entries(catDb.properties).find(([n, p]) => p.type === 'relation' && n.includes('Lançamentos'));
if (catBack) {
  await api(`databases/${cat.id}`, { properties: {
    [catBack[0]]: { name: 'Lançamentos' },
  }}, 'PATCH');
  await api(`databases/${cat.id}`, { properties: {
    'Total movimentado': { rollup: { relation_property_name: 'Lançamentos', rollup_property_name: 'Valor', function: 'sum' } },
  }}, 'PATCH');
}
console.log('  ✓');

// ═══ 5. migrar linhas ═══
console.log('▸ 5/5 migrando dados...');
const CATS = [
  ['Divisão de Lucros', 'Receita'], ['Rendimentos Renda Fixa', 'Receita'],
  ['Proventos Renda Variável', 'Receita'], ['Pró-Labore', 'Receita'],
  ['Educação', 'Despesa'],
];
const C = {};
for (const [nome, tipo] of CATS) {
  const p = await api('pages', { parent: { database_id: cat.id }, properties: { 'Nome': title(nome), 'Tipo': sel(tipo) } });
  C[nome] = p.id;
  console.log(`  ✓ 🏷️ ${nome} (${tipo})`);
}

const CONTAS = [
  // [nome, emoji, tipo, saldoInicial, bandeira, limite, fechamento, vencimento]
  ['Banco Inter', '🏦', 'Conta corrente', 0, null, null, null, null],
  ['Banco Inter PJ', '🏦', 'Conta corrente', null, null, null, null, null],
  ['Cartão Inter GMAC', '💳', 'Cartão de crédito', null, 'Mastercard', 2000, '2024-07-08', '2024-07-15'],
  ['Cartão Inter Black', '💳', 'Cartão de crédito', null, 'Mastercard', 1900, '2024-07-05', '2024-07-12'],
];
const K = {};
for (const [nome, emoji, tipo, saldo, band, lim, fech, venc] of CONTAS) {
  const props = { 'Nome': title(nome), 'Tipo': sel(tipo) };
  if (saldo !== null) props['Saldo inicial'] = num(saldo);
  if (band) props['Bandeira'] = sel(band);
  if (lim !== null) props['Limite'] = num(lim);
  if (fech) props['Fechamento'] = date(fech);
  if (venc) props['Vencimento'] = date(venc);
  const p = await api('pages', { parent: { database_id: contas.id }, icon: { type: 'emoji', emoji }, properties: props });
  K[nome] = p.id;
  console.log(`  ✓ 💳 ${nome}`);
}

// 1 lançamento de exemplo (claramente marcado) pra ver o saldo automático funcionando
await api('pages', {
  parent: { database_id: lanc.id },
  properties: {
    'Descrição': title('EXEMPLO (pode apagar): curso de teste'),
    'Tipo': sel('Saída'),
    'Valor': num(100),
    'Data': date('2026-07-23'),
    'Conta': rel([K['Banco Inter']]),
    'Categoria': rel([C['Educação']]),
  },
});
console.log('  ✓ 💸 1 lançamento de exemplo');

fs.writeFileSync(new URL('./notion-trevvo-ids.json', import.meta.url).pathname.replace(/^\//, ''),
  JSON.stringify({ contas: contas.id, lancamentos: lanc.id, categorias: cat.id }, null, 2));

console.log('\n✅ TREVVO 1.0 no ar — 3 bancos');
console.log(`   💳 Contas:      ${contas.url}`);
console.log(`   💸 Lançamentos: ${lanc.url}`);
console.log(`   🏷️ Categorias:  ${cat.url}`);
