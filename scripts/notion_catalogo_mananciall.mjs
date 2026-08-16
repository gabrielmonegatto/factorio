// Carrega o Mapa de Obras (docs/14_MAPA_DE_OBRAS_MANANCIALL.md) no Notion como
// banco EDITÁVEL: "Catálogo Estratégico Mananciall". Este banco é o plano de controle
// humano do catálogo (prioridade, lançamento, status). Difere do "Acervo — Mananciall",
// que é espelho read-only do D1.
//
// Direção: este script SEMEIA/atualiza a partir do mapa. Edições do Gabriel no Notion
// (prioridade, lançamento, cortes) são respeitadas: o upsert só preenche campos de
// catálogo (era, tradução, fonte), nunca sobrescreve Prioridade/Lançamento/Status de
// linhas existentes.
//
// Uso: node scripts/notion_catalogo_mananciall.mjs
// Credencial: NOTION_TOKEN em _factorio/.env

import { readFileSync } from 'node:fs';
import path from 'node:path';

const ENV_PATH = path.resolve(import.meta.dirname, '..', '.env');
const PARENT_PAGE = '3a7f06f1-0ce3-81b1-ad55-dc0239ee270b'; // Et3rnall - Manancial
const DB_TITLE = 'Catálogo Estratégico Mananciall';

function env(key) {
  const raw = readFileSync(ENV_PATH, 'utf8');
  const line = raw.split(/\r?\n/).find((l) => l.startsWith(key + '='));
  if (!line) throw new Error(`${key} não encontrado em _factorio/.env`);
  return line.slice(key.length + 1).trim();
}
const NOTION = env('NOTION_TOKEN');

async function notion(pathname, method = 'GET', body) {
  const res = await fetch(`https://api.notion.com/v1${pathname}`, {
    method,
    headers: {
      Authorization: `Bearer ${NOTION}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!res.ok) throw new Error(`Notion ${method} ${pathname}: ${json.message || res.status}`);
  return json;
}

// ---------------------------------------------------------------------------
// Dados: 1 linha = 1 linha do mapa (docs/14). Campos:
// [obra, autor, era(1-9), prioridade, [coleções], tradução DP, fonte, pd, lançamento, nota]
const V = 'verified', P = 'pending', B = 'blocked';
const ROWS = [
  // ── Era 1 · Apostolic Fathers ──
  ['The Didache (The Teaching of the Twelve Apostles)', 'Anônimo', 1, 'P1', ['Story of the Church', 'Essentials'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, true, ''],
  ['The First Epistle of Clement', 'Clemente de Roma', 1, 'P1', ['Story of the Church'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, false, ''],
  ['The Second Epistle of Clement', 'Atribuído a Clemente', 1, 'P2', ['Story of the Church'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, false, ''],
  ['The Letters of Ignatius (7 cartas)', 'Inácio de Antioquia', 1, 'P1', ['Story of the Church', 'Suffering & Comfort'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, true, 'volume único com as 7 cartas'],
  ['The Epistle of Polycarp to the Philippians', 'Policarpo', 1, 'P1', ['Story of the Church'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, false, ''],
  ['The Martyrdom of Polycarp', 'Anônimo', 1, 'P1', ['Suffering & Comfort'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, true, ''],
  ['The Epistle to Diognetus', 'Anônimo', 1, 'P1', ['Apologetics Classics'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, false, ''],
  ['The Epistle of Barnabas', 'Atribuído a Barnabé', 1, 'P2', ['Story of the Church'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, false, ''],
  ['The Shepherd of Hermas', 'Hermas', 1, 'P2', ['Story of the Church'], 'Lightfoot 1891 / ANF vol.2', 'CCEL', V, false, ''],
  ['Fragments of Papias', 'Papias', 1, 'P3', ['Story of the Church'], 'Lightfoot 1891 / ANF vol.1', 'CCEL', V, false, ''],

  // ── Era 2a · Deuterocanônicos (KJV 1611) ──
  ['Tobit', 'Deuterocanônico', 2, 'P1', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['Judith', 'Deuterocanônico', 2, 'P1', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['The Wisdom of Solomon', 'Deuterocanônico', 2, 'P1', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, true, ''],
  ['Sirach (Ecclesiasticus)', 'Deuterocanônico', 2, 'P1', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['1 Maccabees', 'Deuterocanônico', 2, 'P1', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, 'história intertestamentária'],
  ['2 Maccabees', 'Deuterocanônico', 2, 'P1', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['Baruch + Letter of Jeremiah', 'Deuterocanônico', 2, 'P2', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['The Prayer of Manasseh', 'Deuterocanônico', 2, 'P2', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['1 Esdras', 'Deuterocanônico', 2, 'P2', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['2 Esdras', 'Deuterocanônico', 2, 'P2', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, ''],
  ['Additions to Esther and Daniel (Susanna, Bel and the Dragon, Song of the Three)', 'Deuterocanônico', 2, 'P2', ['Early Christian Library'], 'KJV 1611 Apocrypha', 'Gutenberg', V, false, 'volume único'],

  // ── Era 2b · Pseudepígrafos do VT (R.H. Charles) ──
  ['The Book of Enoch (1 Enoch)', 'Pseudepígrafo', 2, 'P1', ['Early Christian Library'], 'R.H. Charles 1917', 'Archive.org', V, true, 'maior busca orgânica do bloco'],
  ['The Book of Jubilees', 'Pseudepígrafo', 2, 'P1', ['Early Christian Library'], 'R.H. Charles 1902', 'Archive.org', V, false, ''],
  ['The Testaments of the Twelve Patriarchs', 'Pseudepígrafo', 2, 'P2', ['Early Christian Library'], 'R.H. Charles 1908', 'Archive.org', V, false, ''],
  ['2 Baruch', 'Pseudepígrafo', 2, 'P2', ['Early Christian Library'], 'R.H. Charles 1896', 'Archive.org', V, false, 'apocalíptica'],
  ['4 Ezra', 'Pseudepígrafo', 2, 'P2', ['Early Christian Library'], 'R.H. Charles (ed.) 1913', 'Archive.org', V, false, 'apocalíptica'],
  ['The Psalms of Solomon', 'Pseudepígrafo', 2, 'P3', ['Early Christian Library'], 'R.H. Charles (ed.) 1913', 'Archive.org', V, false, ''],
  ['The Letter of Aristeas', 'Pseudepígrafo', 2, 'P3', ['Early Christian Library'], 'R.H. Charles (ed.) 1913', 'Archive.org', V, false, ''],
  ['The Ascension of Isaiah', 'Pseudepígrafo', 2, 'P3', ['Early Christian Library'], 'R.H. Charles 1900', 'Archive.org', V, false, ''],

  // ── Era 2c · Apócrifos do NT (M.R. James 1924 / ANF vol.8) ──
  ['The Protoevangelium of James', 'Apócrifo do NT', 2, 'P1', ['Early Christian Library'], 'M.R. James 1924 / ANF vol.8', 'New Advent', V, true, 'infância de Maria, alta curiosidade'],
  ['The Infancy Gospel of Thomas', 'Apócrifo do NT', 2, 'P1', ['Early Christian Library'], 'M.R. James 1924 / ANF vol.8', 'New Advent', V, false, ''],
  ['The Gospel of Nicodemus (Acts of Pilate)', 'Apócrifo do NT', 2, 'P1', ['Early Christian Library'], 'M.R. James 1924 / ANF vol.8', 'New Advent', V, true, 'descensus ad inferos'],
  ['The Gospel of Peter (fragmento)', 'Apócrifo do NT', 2, 'P2', ['Early Christian Library'], 'M.R. James 1924', 'New Advent', V, false, ''],
  ['The Acts of Paul and Thecla', 'Apócrifo do NT', 2, 'P2', ['Early Christian Library'], 'M.R. James 1924 / ANF vol.8', 'New Advent', V, false, ''],
  ['The Acts of Thomas', 'Apócrifo do NT', 2, 'P2', ['Early Christian Library'], 'M.R. James 1924', 'New Advent', V, false, ''],
  ['The Acts of Peter', 'Apócrifo do NT', 2, 'P2', ['Early Christian Library'], 'M.R. James 1924', 'New Advent', V, false, ''],
  ['The Acts of John', 'Apócrifo do NT', 2, 'P2', ['Early Christian Library'], 'M.R. James 1924', 'New Advent', V, false, ''],
  ['The Apocalypse of Peter', 'Apócrifo do NT', 2, 'P2', ['Early Christian Library'], 'M.R. James 1924', 'New Advent', V, false, ''],
  ['The Apocalypse of Paul', 'Apócrifo do NT', 2, 'P2', ['Early Christian Library'], 'M.R. James 1924', 'New Advent', V, false, ''],
  ['The Gospel of Thomas (copta de Nag Hammadi)', 'Apócrifo do NT', 2, 'P3', ['Early Christian Library'], 'SEM tradução DP do texto completo', 'Archive.org', B, false, 'traduções completas são pós-1945 e protegidas; só fragmentos gregos de Oxyrhynchus têm tradução DP'],

  // ── Era 3 · Apologists ──
  ['The First and Second Apologies', 'Justino Mártir', 3, 'P1', ['Apologetics Classics'], 'ANF vol.1', 'New Advent', V, false, ''],
  ['Dialogue with Trypho', 'Justino Mártir', 3, 'P2', ['Apologetics Classics'], 'ANF vol.1', 'New Advent', V, false, ''],
  ['Against Heresies', 'Irineu de Lyon', 3, 'P2', ['Story of the Church'], 'ANF vol.1', 'New Advent', V, false, '5 livros'],
  ['The Demonstration of the Apostolic Preaching', 'Irineu de Lyon', 3, 'P1', ['Essentials'], 'J.A. Robinson 1920', 'Archive.org', V, true, 'curto e riquíssimo'],
  ['The Apology (Apologeticus)', 'Tertuliano', 3, 'P1', ['Apologetics Classics'], 'ANF vol.3', 'New Advent', V, false, ''],
  ['On Prayer + On Patience + On Repentance', 'Tertuliano', 3, 'P1', ['Prayer Library'], 'ANF vol.3', 'New Advent', V, true, 'coletânea devocional'],
  ['The Prescription Against Heretics', 'Tertuliano', 3, 'P2', ['Story of the Church'], 'ANF vol.3', 'New Advent', V, false, ''],
  ['On Prayer', 'Orígenes', 3, 'P1', ['Prayer Library'], 'ANF (trad. DP)', 'CCEL', V, true, ''],
  ['Against Celsus', 'Orígenes', 3, 'P2', ['Apologetics Classics'], 'ANF vol.4', 'New Advent', V, false, ''],
  ['De Principiis (First Principles)', 'Orígenes', 3, 'P2', [], 'ANF vol.4', 'New Advent', V, false, ''],
  ['Exhortation to Martyrdom', 'Orígenes', 3, 'P3', ['Suffering & Comfort'], 'trad. DP a verificar', 'Archive.org', P, false, ''],
  ['The Octavius', 'Minúcio Félix', 3, 'P2', ['Apologetics Classics'], 'ANF vol.4', 'New Advent', V, false, 'diálogo, ótima porta de entrada'],
  ['On the Unity of the Church', 'Cipriano', 3, 'P1', ['Story of the Church'], 'ANF vol.5', 'New Advent', V, false, ''],
  ['On the Lord\'s Prayer', 'Cipriano', 3, 'P1', ['Prayer Library'], 'ANF vol.5', 'New Advent', V, false, ''],
  ['On Mortality', 'Cipriano', 3, 'P1', ['Suffering & Comfort'], 'ANF vol.5', 'New Advent', V, false, ''],
  ['Exhortation to the Heathen + The Instructor (Paedagogus)', 'Clemente de Alexandria', 3, 'P2', [], 'ANF vol.2', 'New Advent', V, false, ''],
  ['Stromata', 'Clemente de Alexandria', 3, 'P3', [], 'ANF vol.2', 'New Advent', V, false, ''],
  ['A Plea for the Christians', 'Atenágoras', 3, 'P3', ['Apologetics Classics'], 'ANF vol.2', 'New Advent', V, false, ''],
  ['To Autolycus', 'Teófilo de Antioquia', 3, 'P3', ['Apologetics Classics'], 'ANF vol.2', 'New Advent', V, false, ''],

  // ── Era 4 · Golden Age ──
  ['Confessions', 'Agostinho', 4, 'P1', ['Essentials'], 'Pusey 1838', 'CCEL', V, true, 'âncora de SEO da patrística inteira'],
  ['The Enchiridion (Faith, Hope and Love)', 'Agostinho', 4, 'P1', ['Essentials'], 'NPNF-1 vol.3', 'CCEL', V, false, ''],
  ['On Christian Doctrine', 'Agostinho', 4, 'P2', [], 'NPNF-1 vol.2', 'CCEL', V, false, ''],
  ['The City of God', 'Agostinho', 4, 'P2', [], 'Marcus Dods 1871', 'CCEL', V, false, 'tomo; fatiar bem'],
  ['On the Trinity', 'Agostinho', 4, 'P3', [], 'NPNF-1 vol.3', 'CCEL', V, false, ''],
  ['On Grace and Free Will + On the Spirit and the Letter', 'Agostinho', 4, 'P2', [], 'NPNF-1 vol.5', 'CCEL', V, false, 'anti-pelagianos'],
  ['On the Incarnation', 'Atanásio', 4, 'P1', ['Essentials'], 'NPNF-2 vol.4', 'CCEL', V, true, ''],
  ['The Life of Antony', 'Atanásio', 4, 'P1', ['Story of the Church'], 'NPNF-2 vol.4', 'CCEL', V, false, 'pai da literatura monástica'],
  ['On the Priesthood', 'João Crisóstomo', 4, 'P1', [], 'NPNF-1 vol.9', 'CCEL', V, false, ''],
  ['No One Can Harm the Man Who Does Not Injure Himself', 'João Crisóstomo', 4, 'P1', ['Suffering & Comfort'], 'NPNF-1 vol.9', 'CCEL', V, false, ''],
  ['Homilies (seleções: Mateus, João, Romanos)', 'João Crisóstomo', 4, 'P2', [], 'NPNF-1 vols.10-14', 'CCEL', V, false, 'seleções por volume'],
  ['On the Holy Spirit', 'Basílio de Cesareia', 4, 'P2', [], 'NPNF-2 vol.8', 'CCEL', V, false, ''],
  ['The Hexaemeron', 'Basílio de Cesareia', 4, 'P3', [], 'NPNF-2 vol.8', 'CCEL', V, false, ''],
  ['The Five Theological Orations', 'Gregório de Nazianzo', 4, 'P2', [], 'NPNF-2 vol.7', 'CCEL', V, false, ''],
  ['The Great Catechism + On the Soul and the Resurrection', 'Gregório de Nissa', 4, 'P2', [], 'NPNF-2 vol.5', 'CCEL', V, false, ''],
  ['The Ecclesiastical History', 'Eusébio de Cesareia', 4, 'P1', ['Story of the Church'], 'NPNF-2 vol.1', 'CCEL', V, false, ''],
  ['Catechetical Lectures', 'Cirilo de Jerusalém', 4, 'P2', [], 'NPNF-2 vol.7', 'CCEL', V, false, ''],
  ['On the Duties of the Clergy + On the Mysteries', 'Ambrósio', 4, 'P2', [], 'NPNF-2 vol.10', 'CCEL', V, false, ''],
  ['Lives of Illustrious Men + Letters (seleção)', 'Jerônimo', 4, 'P2', [], 'NPNF-2 vols.3 e 6', 'CCEL', V, false, ''],
  ['The Conferences + The Institutes', 'João Cassiano', 4, 'P2', ['Holiness'], 'NPNF-2 vol.11', 'CCEL', V, false, 'ponte pro monasticismo'],
  ['The Commonitory', 'Vicente de Lérins', 4, 'P2', [], 'NPNF-2 vol.11', 'CCEL', V, false, ''],
  ['The Tome + Sermons (seleção)', 'Leão Magno', 4, 'P3', [], 'NPNF-2 vol.12', 'CCEL', V, false, ''],
  ['The Confession of St. Patrick', 'Patrício', 4, 'P1', ['Story of the Church'], 'trad. DP (várias)', 'CCEL', V, true, 'curto, amado, viral em março'],

  // ── Era 5 · Medieval & Mystics ──
  ['The Consolation of Philosophy', 'Boécio', 5, 'P1', ['Suffering & Comfort'], 'W.V. Cooper 1902', 'Gutenberg', V, false, ''],
  ['The Rule of St. Benedict', 'Bento de Núrsia', 5, 'P1', ['Holiness'], 'Gasquet 1909', 'Gutenberg', V, false, ''],
  ['The Pastoral Rule', 'Gregório Magno', 5, 'P2', [], 'NPNF-2 vol.12', 'CCEL', V, false, ''],
  ['The Ecclesiastical History of the English People', 'Beda', 5, 'P2', ['Story of the Church'], 'Sellar 1907', 'Gutenberg', V, false, ''],
  ['Proslogion + Monologion', 'Anselmo', 5, 'P2', [], 'S.N. Deane 1903', 'Gutenberg', V, false, ''],
  ['Cur Deus Homo (Why God Became Man)', 'Anselmo', 5, 'P1', ['Essentials'], 'S.N. Deane 1903', 'Gutenberg', V, false, ''],
  ['On Loving God', 'Bernardo de Claraval', 5, 'P1', ['Essentials', 'Holiness'], 'trad. DP (várias)', 'CCEL', V, true, ''],
  ['On Consideration + Sermons on the Song of Songs (seleção)', 'Bernardo de Claraval', 5, 'P2', [], 'Eales 1895', 'Archive.org', V, false, ''],
  ['The Little Flowers of St. Francis', 'Anônimo (sobre Francisco)', 5, 'P1', [], 'T.W. Arnold 1898', 'Gutenberg', V, false, ''],
  ['Summa Theologica (seleções temáticas)', 'Tomás de Aquino', 5, 'P3', [], 'English Dominican Fathers 1911-25', 'CCEL', V, false, 'tomo gigante; só seleções'],
  ['The Imitation of Christ', 'Tomás de Kempis', 5, 'P1', ['Essentials', 'Daily Devotionals'], 'trad. DP (várias)', 'CCEL', V, true, ''],
  ['The Cloud of Unknowing', 'Anônimo', 5, 'P1', ['Holiness'], 'Underhill 1912', 'Gutenberg', V, false, ''],
  ['The Scale of Perfection', 'Walter Hilton', 5, 'P2', ['Holiness'], 'ed. 1901', 'Archive.org', V, false, ''],
  ['Revelations of Divine Love', 'Juliana de Norwich', 5, 'P1', ['Suffering & Comfort'], 'Grace Warrack 1901', 'Gutenberg', V, true, ''],
  ['Theologia Germanica', 'Anônimo', 5, 'P2', ['Holiness'], 'Winkworth 1854', 'Gutenberg', V, false, ''],
  ['The Dialogue', 'Catarina de Siena', 5, 'P2', [], 'Algar Thorold 1896', 'Archive.org', V, false, ''],
  ['Sermons (seleção)', 'Meister Eckhart', 5, 'P3', [], 'Claud Field 1909', 'Archive.org', V, false, 'posicionamento editorial necessário'],

  // ── Era 6 · Reformation ──
  ['The Freedom of a Christian', 'Lutero', 6, 'P1', ['Essentials'], 'trad. DP (várias)', 'Gutenberg', V, true, ''],
  ['The Bondage of the Will', 'Lutero', 6, 'P2', [], 'Henry Cole 1823', 'Archive.org', V, false, ''],
  ['Commentary on Galatians', 'Lutero', 6, 'P1', [], 'Erasmus Middleton (DP)', 'CCEL', V, false, ''],
  ['The Small Catechism + The Large Catechism', 'Lutero', 6, 'P2', [], 'trad. DP (várias)', 'Gutenberg', V, false, ''],
  ['Table Talk', 'Lutero', 6, 'P2', [], 'Hazlitt 1857', 'Gutenberg', V, false, ''],
  ['The 95 Theses', 'Lutero', 6, 'P1', ['Story of the Church'], 'trad. DP (várias)', 'Gutenberg', V, false, 'curto; empacotar com contexto'],
  ['Institutes of the Christian Religion', 'Calvino', 6, 'P1', ['Essentials'], 'Beveridge 1845', 'CCEL', V, false, 'fatiar em 4 volumes'],
  ['Of Prayer (Institutas III.20 avulso)', 'Calvino', 6, 'P1', ['Prayer Library'], 'Beveridge 1845', 'CCEL', V, true, ''],
  ['A Little Book on the Christian Life (Institutas III.6-10 avulso)', 'Calvino', 6, 'P1', ['Holiness'], 'Beveridge 1845', 'CCEL', V, false, 'NÃO usar a trad. Van Andel 1952 (protegida)'],
  ['The Obedience of a Christian Man + The Parable of the Wicked Mammon', 'Tyndale', 6, 'P2', [], 'original EN', 'Gutenberg', V, false, ''],
  ['The History of the Reformation in Scotland', 'John Knox', 6, 'P3', ['Story of the Church'], 'original EN', 'Archive.org', V, false, ''],
  ['Foxe\'s Book of Martyrs', 'John Foxe', 6, 'P1', ['Suffering & Comfort', 'Story of the Church'], 'original EN', 'CCEL', V, false, ''],
  ['The Heidelberg Catechism', 'Confissão', 6, 'P1', ['Essentials'], 'trad. DP', 'CCEL', V, false, ''],
  ['The Westminster Confession + Shorter Catechism', 'Confissão', 6, 'P1', [], 'original EN', 'CCEL', V, false, ''],
  ['The Augsburg Confession + The Belgic Confession + The 39 Articles', 'Confissão', 6, 'P2', [], 'trad. DP', 'CCEL', V, false, 'volume de confissões'],

  // ── Era 7 · Puritans (+ devocionais do período) ──
  ['The Pilgrim\'s Progress', 'John Bunyan', 7, 'P1', ['Essentials'], 'original EN', 'Gutenberg', V, true, 'o livro cristão mais vendido depois da Bíblia'],
  ['Grace Abounding to the Chief of Sinners', 'John Bunyan', 7, 'P1', [], 'original EN', 'Gutenberg', V, false, ''],
  ['The Holy War', 'John Bunyan', 7, 'P2', [], 'original EN', 'Gutenberg', V, false, ''],
  ['Prayer (I Will Pray with the Spirit) + The Heavenly Footman', 'John Bunyan', 7, 'P2', ['Prayer Library'], 'original EN', 'CCEL', V, false, ''],
  ['The Mortification of Sin', 'John Owen', 7, 'P1', ['Holiness'], 'original EN', 'CCEL', V, true, ''],
  ['Communion with God + The Glory of Christ + Of Temptation', 'John Owen', 7, 'P2', ['Holiness'], 'original EN', 'CCEL', V, false, '3 obras'],
  ['The Reformed Pastor', 'Richard Baxter', 7, 'P2', [], 'original EN', 'CCEL', V, false, ''],
  ['The Saints\' Everlasting Rest', 'Richard Baxter', 7, 'P1', ['Suffering & Comfort'], 'original EN', 'CCEL', V, false, ''],
  ['A Call to the Unconverted', 'Richard Baxter', 7, 'P2', [], 'original EN', 'Gutenberg', V, false, ''],
  ['Precious Remedies Against Satan\'s Devices', 'Thomas Brooks', 7, 'P1', ['Holiness'], 'original EN', 'CCEL', V, false, ''],
  ['All Things for Good (A Divine Cordial)', 'Thomas Watson', 7, 'P1', ['Suffering & Comfort'], 'original EN', 'CCEL', V, false, ''],
  ['The Doctrine of Repentance + A Body of Divinity', 'Thomas Watson', 7, 'P2', [], 'original EN', 'CCEL', V, false, '2 obras'],
  ['The Bruised Reed', 'Richard Sibbes', 7, 'P1', ['Suffering & Comfort'], 'original EN', 'CCEL', V, true, ''],
  ['The Mystery of Providence + Keeping the Heart', 'John Flavel', 7, 'P1', [], 'original EN', 'CCEL', V, false, '2 obras'],
  ['The Letters of Samuel Rutherford (seleção)', 'Samuel Rutherford', 7, 'P1', ['Suffering & Comfort'], 'original EN', 'CCEL', V, false, ''],
  ['The Rare Jewel of Christian Contentment', 'Jeremiah Burroughs', 7, 'P1', ['Holiness'], 'original EN', 'CCEL', V, true, ''],
  ['The Christian in Complete Armour (seleções)', 'William Gurnall', 7, 'P2', [], 'original EN', 'CCEL', V, false, 'tomo; fatiar'],
  ['Human Nature in its Fourfold State', 'Thomas Boston', 7, 'P2', [], 'original EN', 'CCEL', V, false, ''],
  ['An Alarm to the Unconverted', 'Joseph Alleine', 7, 'P2', [], 'original EN', 'CCEL', V, false, ''],
  ['The Existence and Attributes of God', 'Stephen Charnock', 7, 'P3', [], 'original EN', 'CCEL', V, false, 'tomo'],
  ['The Life of God in the Soul of Man', 'Henry Scougal', 7, 'P1', ['Holiness'], 'original EN', 'CCEL', V, false, 'o livro que converteu Whitefield'],
  ['The Practice of the Presence of God', 'Brother Lawrence', 7, 'P1', ['Essentials', 'Prayer Library'], 'trad. DP (várias)', 'Gutenberg', V, true, ''],
  ['Pensées (Thoughts)', 'Blaise Pascal', 7, 'P1', ['Apologetics Classics'], 'W.F. Trotter 1904', 'Gutenberg', V, false, ''],
  ['Christian Perfection (seleções) + Spiritual Letters', 'Fénelon', 7, 'P2', ['Holiness'], 'trad. DP', 'CCEL', V, false, ''],
  ['A Short and Easy Method of Prayer', 'Madame Guyon', 7, 'P2', ['Prayer Library'], 'trad. DP', 'CCEL', V, false, ''],

  // ── Era 8 · Awakening & Wesley ──
  ['Religious Affections', 'Jonathan Edwards', 8, 'P1', ['Holiness'], 'original EN', 'CCEL', V, false, 'conferir os 4 já live no D1 pra não duplicar'],
  ['Sinners in the Hands of an Angry God + sermões selecionados', 'Jonathan Edwards', 8, 'P1', [], 'original EN', 'CCEL', V, false, ''],
  ['The Life and Diary of David Brainerd', 'Jonathan Edwards', 8, 'P1', ['Missions'], 'original EN', 'CCEL', V, false, ''],
  ['Freedom of the Will + Charity and Its Fruits', 'Jonathan Edwards', 8, 'P2', [], 'original EN', 'CCEL', V, false, '2 obras'],
  ['Selected Sermons', 'George Whitefield', 8, 'P1', [], 'original EN', 'CCEL', V, false, ''],
  ['The Journals', 'George Whitefield', 8, 'P2', [], 'original EN', 'Archive.org', V, false, ''],
  ['Fifty-Two Standard Sermons (seleções por volume)', 'John Wesley', 8, 'P2', [], 'original EN', 'CCEL', V, false, ''],
  ['A Plain Account of Christian Perfection', 'John Wesley', 8, 'P1', ['Holiness'], 'original EN', 'CCEL', V, false, ''],
  ['A Serious Call to a Devout and Holy Life', 'William Law', 8, 'P1', ['Holiness', 'Essentials'], 'original EN', 'CCEL', V, true, ''],
  ['The Spirit of Prayer', 'William Law', 8, 'P2', ['Prayer Library'], 'original EN', 'CCEL', V, false, ''],
  ['The Rise and Progress of Religion in the Soul', 'Philip Doddridge', 8, 'P2', [], 'original EN', 'CCEL', V, false, ''],
  ['Cardiphonia (Letters, seleção) + hinos com história', 'John Newton', 8, 'P1', ['Suffering & Comfort'], 'original EN', 'Archive.org', V, false, ''],

  // ── Era 9 · Revival Century & Beyond (XIX até 1930) ──
  ['Sermões: 57 volumes do backlog (lote)', 'Charles Spurgeon', 9, 'P2', [], 'original EN', 'CCEL', V, false, 'já mapeado no Teable, roda em lote na esteira'],
  ['Lectures to My Students + The Soul Winner + Around the Wicket Gate', 'Charles Spurgeon', 9, 'P1', [], 'original EN', 'Archive.org', V, false, '3 obras'],
  ['John Ploughman\'s Talks', 'Charles Spurgeon', 9, 'P2', [], 'original EN', 'Gutenberg', V, false, ''],
  ['The Treasury of David (seleções por livro de Salmos)', 'Charles Spurgeon', 9, 'P3', [], 'original EN', 'Archive.org', V, false, 'tomo gigante'],
  ['Holiness', 'J.C. Ryle', 9, 'P1', ['Holiness'], 'original EN', 'Gutenberg', V, true, 'âncora da coleção Holiness'],
  ['Practical Religion + Thoughts for Young Men', 'J.C. Ryle', 9, 'P1', [], 'original EN', 'Gutenberg', V, false, '2 obras'],
  ['Expository Thoughts on the Gospels (4 sets)', 'J.C. Ryle', 9, 'P2', [], 'original EN', 'CCEL', V, false, ''],
  ['Abide in Christ', 'Andrew Murray', 9, 'P1', ['Daily Devotionals', 'Holiness'], 'original EN', 'CCEL', V, true, ''],
  ['With Christ in the School of Prayer', 'Andrew Murray', 9, 'P1', ['Prayer Library'], 'original EN', 'CCEL', V, true, ''],
  ['Humility + Absolute Surrender + The True Vine', 'Andrew Murray', 9, 'P1', ['Holiness'], 'original EN', 'CCEL', V, false, '3 obras'],
  ['A Narrative of Some of the Lord\'s Dealings (autobiografia)', 'George Müller', 9, 'P1', ['Prayer Library'], 'original EN', 'Archive.org', V, false, ''],
  ['Answers to Prayer', 'George Müller', 9, 'P1', ['Prayer Library'], 'original EN', 'Gutenberg', V, false, ''],
  ['How to Pray + How to Study the Bible', 'R.A. Torrey', 9, 'P1', ['Prayer Library'], 'original EN', 'Gutenberg', V, true, '2 obras'],
  ['The Person and Work of the Holy Spirit', 'R.A. Torrey', 9, 'P2', [], 'original EN', 'Archive.org', V, false, ''],
  ['The Way to God + Prevailing Prayer + Secret Power', 'D.L. Moody', 9, 'P2', ['Prayer Library'], 'original EN', 'Gutenberg', V, false, '3 obras'],
  ['Union and Communion + A Retrospect', 'Hudson Taylor', 9, 'P1', ['Missions'], 'original EN', 'Archive.org', V, false, '2 obras'],
  ['The Christian\'s Secret of a Happy Life', 'Hannah Whitall Smith', 9, 'P1', ['Holiness'], 'original EN', 'Gutenberg', V, false, ''],
  ['Orthodoxy', 'G.K. Chesterton', 9, 'P1', ['Apologetics Classics'], 'original EN 1908', 'Gutenberg', V, true, ''],
  ['The Everlasting Man + Heretics + St. Francis of Assisi', 'G.K. Chesterton', 9, 'P2', ['Apologetics Classics'], 'original EN (pré-1931)', 'Gutenberg', V, false, '3 obras'],
  ['My Utmost for His Highest', 'Oswald Chambers', 9, 'P1', ['Daily Devotionals'], 'original EN 1927 (DP nos EUA desde 2023)', 'Archive.org', V, true, ''],
  ['The Sovereignty of God (1918)', 'A.W. Pink', 9, 'P2', [], 'original EN 1918', 'Archive.org', V, false, 'só obras pré-1931 do Pink'],
  ['Lectures on Revivals of Religion + Autobiography', 'Charles Finney', 9, 'P2', [], 'original EN', 'Gutenberg', V, false, 'posicionamento editorial necessário'],
  ['God\'s Way of Peace', 'Horatius Bonar', 9, 'P2', [], 'original EN', 'Gutenberg', V, false, ''],
  ['Personal Declension and Revival of Religion in the Soul', 'Octavius Winslow', 9, 'P2', ['Holiness'], 'original EN', 'CCEL', V, false, ''],
  ['The Fourfold Gospel', 'A.B. Simpson', 9, 'P3', [], 'original EN', 'CCEL', V, false, ''],
  ['The Secret of Guidance', 'F.B. Meyer', 9, 'P2', [], 'original EN', 'CCEL', V, false, ''],
  ['Things as They Are (1903)', 'Amy Carmichael', 9, 'P3', ['Missions'], 'original EN 1903', 'Archive.org', V, false, 'só obras pré-1931'],
  ['Daily Light on the Daily Path', 'Samuel Bagster', 9, 'P1', ['Daily Devotionals'], 'original EN', 'Gutenberg', V, false, ''],
];

const ERAS = {
  1: '1 Apostolic Fathers', 2: '2 Apocrypha', 3: '3 Apologists', 4: '4 Golden Age',
  5: '5 Medieval & Mystics', 6: '6 Reformation', 7: '7 Puritans', 8: '8 Awakening',
  9: '9 Revival Century',
};

// ---------------------------------------------------------------------------
const PROPS = {
  Obra: { title: {} },
  Autor: { rich_text: {} },
  Era: { select: {} },
  Prioridade: { select: { options: [{ name: 'P1', color: 'green' }, { name: 'P2', color: 'yellow' }, { name: 'P3', color: 'gray' }] } },
  'Coleções': { multi_select: {} },
  'Tradução DP': { rich_text: {} },
  Fonte: { select: {} },
  'Status DP': { select: { options: [{ name: 'verified', color: 'green' }, { name: 'pending', color: 'yellow' }, { name: 'blocked', color: 'red' }] } },
  'Status produção': { select: { options: [
    { name: 'Mapeada', color: 'default' }, { name: 'Minerando', color: 'blue' },
    { name: 'Limpando', color: 'yellow' }, { name: 'Pronta', color: 'orange' },
    { name: 'Publicada', color: 'green' }, { name: 'Cortada', color: 'red' },
  ] } },
  'Lançamento': { checkbox: {} },
  Nota: { rich_text: {} },
};

const found = await notion('/search', 'POST', {
  query: DB_TITLE,
  filter: { value: 'database', property: 'object' },
  page_size: 20,
});
let db = found.results.find((r) => r.title?.map((t) => t.plain_text).join('') === DB_TITLE);

if (!db) {
  db = await notion('/databases', 'POST', {
    parent: { type: 'page_id', page_id: PARENT_PAGE },
    title: [{ type: 'text', text: { content: DB_TITLE } }],
    description: [{ type: 'text', text: { content: 'Plano de controle do catálogo (editável). Prioridade, Lançamento, Status produção e cortes são SEUS: a fábrica lê daqui. Semeado do mapa docs/14 da _factorio.' } }],
    properties: PROPS,
  });
  console.log('banco criado no Notion:', db.id);
} else {
  await notion(`/databases/${db.id}`, 'PATCH', { properties: PROPS });
  console.log('banco existente:', db.id);
}

const txt = (s) => (s ? [{ type: 'text', text: { content: String(s).slice(0, 1900) } }] : []);
const sel = (s) => (s ? { name: String(s).slice(0, 90) } : null);

let created = 0, updated = 0;
for (const [obra, autor, era, pri, cols, trad, fonte, pd, launch, nota] of ROWS) {
  const existing = await notion(`/databases/${db.id}/query`, 'POST', {
    filter: { property: 'Obra', title: { equals: obra } },
    page_size: 1,
  });

  if (existing.results.length) {
    // linha já existe: só atualiza campos de catálogo, respeita edições humanas
    await notion(`/pages/${existing.results[0].id}`, 'PATCH', {
      properties: {
        Autor: { rich_text: txt(autor) },
        Era: { select: sel(ERAS[era]) },
        'Coleções': { multi_select: cols.map((c) => ({ name: c })) },
        'Tradução DP': { rich_text: txt(trad) },
        Fonte: { select: sel(fonte) },
        'Status DP': { select: sel(pd) },
        Nota: { rich_text: txt(nota) },
      },
    });
    updated++;
  } else {
    await notion('/pages', 'POST', {
      parent: { database_id: db.id },
      properties: {
        Obra: { title: txt(obra) },
        Autor: { rich_text: txt(autor) },
        Era: { select: sel(ERAS[era]) },
        Prioridade: { select: sel(pri) },
        'Coleções': { multi_select: cols.map((c) => ({ name: c })) },
        'Tradução DP': { rich_text: txt(trad) },
        Fonte: { select: sel(fonte) },
        'Status DP': { select: sel(pd) },
        'Status produção': { select: sel('Mapeada') },
        'Lançamento': { checkbox: launch },
        Nota: { rich_text: txt(nota) },
      },
    });
    created++;
  }
  await new Promise((r) => setTimeout(r, 350));
}

console.log(`\n${ROWS.length} obras no mapa: ${created} criadas, ${updated} atualizadas`);
console.log(`Lançamento marcado: ${ROWS.filter((r) => r[8]).length} obras`);
console.log(`Notion: https://notion.so/${db.id.replace(/-/g, '')}`);
