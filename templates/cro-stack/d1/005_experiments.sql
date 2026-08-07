-- cro-stack :: migration 005: motor de teste A/B.
--
-- O "C" do CRO. Até aqui a estrutura sabia MEDIR; a partir daqui ela sabe TESTAR.
--
-- Como funciona: o porteiro sorteia a variante por HASH da sessão. Determinístico,
-- então a mesma pessoa vê sempre a mesma variante, em qualquer página, sem piscada
-- e sem precisar guardar o sorteio em lugar nenhum. Ligar, pausar e mudar peso é
-- UPDATE nesta tabela: nenhum teste exige deploy.
--
-- Duas formas de variar:
--   1. rota   — a variante aponta pra outra página (`route`). Pra teste radical.
--   2. bandeira — a variante não tem rota; a própria página lê o cookie `_bnd_var`
--      e muda o que precisa. Pra headline, preço, ordem de bloco.
--
-- A regra da casa está gravada como RESTRIÇÃO do banco, não como combinado:
--   · sem hipótese escrita, o teste NÃO entra em 'running'
--   · sem decisão registrada, o teste NÃO vira 'done'
-- Banco recusa. É o que impede a operação de repetir o passado, que foi exatamente
-- o que aconteceu antes ("trocou na quarta e achou que melhorou").

CREATE TABLE IF NOT EXISTS experiments (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  exp_key         TEXT NOT NULL UNIQUE,          -- 'nome-do-teste-01' (aparece no relatório)
  brand           TEXT NOT NULL DEFAULT '',
  domain          TEXT NOT NULL DEFAULT '',      -- '' = vale pra todos os domínios da marca
  path_prefix     TEXT NOT NULL DEFAULT '/',     -- onde o teste vale
  variants        TEXT NOT NULL,                 -- JSON [{"name":"A","weight":50},{"name":"B","weight":50,"route":"/quiz/v2"}]
  status          TEXT NOT NULL DEFAULT 'draft', -- draft | running | paused | done
  hypothesis      TEXT,                          -- o que se espera e POR QUÊ
  min_conversions INTEGER NOT NULL DEFAULT 100,  -- guardrail: abaixo disso não se declara vencedor
  winner          TEXT,                          -- nome da variante vencedora
  decision        TEXT,                          -- o que foi feito com o resultado
  started_at      TEXT,
  ended_at        TEXT,
  created_at      TEXT DEFAULT (datetime('now')),

  CHECK (status IN ('draft', 'running', 'paused', 'done')),
  CHECK (status <> 'running' OR (hypothesis IS NOT NULL AND length(trim(hypothesis)) > 0)),
  CHECK (status <> 'done'    OR (decision   IS NOT NULL AND length(trim(decision))   > 0))
);

CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);

-- A variante sorteada viaja junto de CADA linha de evento. É isso que permite ler
-- o resultado em VENDA (juntando com purchases_sent pela sessão) em vez de em
-- clique, que é a diferença entre teste de CRO e teste de vaidade.
ALTER TABLE data_tracker ADD COLUMN variant TEXT;

CREATE INDEX IF NOT EXISTS idx_data_tracker_variant ON data_tracker(variant);
