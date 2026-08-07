-- ============================================================
-- cro-stack :: migration 004: roteamento por fato + scripts de terceiro
-- Colunas novas em domain_config. Generalização das migrations 011/013/014/016
-- do bluue, com as lições embutidas.
-- ============================================================

-- ROTA DA RAIZ: declara FATO ("a raiz serve /quiz/v1/"), nunca categoria.
-- O bluue teve uma tabelinha role->rota no porteiro; a categoria envelheceu e a
-- virada quase mandou 16 anúncios ativos pra página errada. NULL/vazio = a raiz
-- serve a home do app. SEMPRE conferir renderizando a página, nunca pelo título.
ALTER TABLE domain_config ADD COLUMN root_route TEXT;

-- Etiqueta de inventário (site | funil | ponte | reserva...). HUMANOS leem;
-- código NÃO roteia por ela. Existe pra Notion/BI, não pro porteiro.
ALTER TABLE domain_config ADD COLUMN role TEXT;

-- Ponte entre domínios (LP num domínio, funil noutro): destino do salto.
-- O clique carrega a sessão em `?_sid=` porque cookie não atravessa domínio.
ALTER TABLE domain_config ADD COLUMN bridge_target TEXT;

-- SCRIPTS DE TERCEIRO por domínio, agnóstica de propósito (coluna com nome de
-- fornecedor envelhece na primeira ferramenta nova). JSON:
--   [{"src":"https://exemplo.com/tag.js","type":"text/javascript"},
--    {"code":"console.log('inline')"}]
-- Chaves: src (só https) · code · type · async · defer. Injetado no FIM do
-- <head> pelo porteiro, no servidor. Vazio = nada.
-- Caso real: a tag da Popsixle (que injeta o pixel dela e manda eventos) migrou
-- de dois domínios sem 1 linha de código.
ALTER TABLE domain_config ADD COLUMN scripts TEXT;

-- Checkout embutido (1 = domínio na whitelist de CORS do gateway; 0 = redirect).
ALTER TABLE domain_config ADD COLUMN checkout_embed INTEGER DEFAULT 0;

-- Microsoft Clarity: UM projeto por MARCA, não por domínio (domínio é
-- descartável; Clarity por domínio zeraria o histórico a cada troca).
ALTER TABLE domain_config ADD COLUMN clarity_id TEXT;

-- Política de pool de domínios (producao | reserva | homologacao | legado |
-- terceiro). Operação: 1 rodando + reservas frias, pro dia do aperto.
ALTER TABLE domain_config ADD COLUMN pool_status TEXT;
