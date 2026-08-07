-- ============================================================
-- cro-stack :: migration 003: corpo da resposta do CAPI
--
-- POR QUE ISTO EXISTE (aprendizado real, 22/07/2026 no ZOAC):
-- o tracker gravava só `meta_status_code`. Quando a Meta devolveu 400,
-- não havia como saber o motivo: foi preciso reproduzir a chamada na mão
-- contra a Graph API pra descobrir que o token tinha escopo de leitura.
-- Com esta coluna, o diagnóstico vira uma query.
--
-- `purchases_sent` já guardava `meta_response`; `data_tracker` não. Agora guarda.
-- ============================================================

ALTER TABLE data_tracker ADD COLUMN meta_response TEXT;
ALTER TABLE data_tracker ADD COLUMN ga4_response TEXT;

-- Diagnóstico rápido depois de um deploy:
--   SELECT event_name, meta_status_code, substr(meta_response,1,300)
--   FROM data_tracker
--   WHERE meta_response_ok = 0 AND meta_status_code IS NOT NULL
--   ORDER BY created_at DESC LIMIT 5;
