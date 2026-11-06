-- =====================================================================
-- 03_dim_cliente.sql  |  Clientes identificados + un miembro "no identificado"
-- ~23% de las líneas originales no traen Customer ID. En vez de perder esas ventas,
-- se asignan al cliente -1, así los totales siempre cuadran y el análisis por
-- cliente (RFM, cohortes) las excluye de forma explícita.
-- =====================================================================
INSERT INTO dim_cliente (cliente_key, es_identificado, primera_compra, ultima_compra)
VALUES (-1, 0, NULL, NULL);

INSERT INTO dim_cliente (cliente_key, es_identificado, primera_compra, ultima_compra)
SELECT customer_id, 1, MIN(invoice_date), MAX(invoice_date)
FROM clean_ventas
WHERE customer_id IS NOT NULL
GROUP BY customer_id;

-- Clientes que solo aparecen en devoluciones (por si existieran)
INSERT INTO dim_cliente (cliente_key, es_identificado, primera_compra, ultima_compra)
SELECT DISTINCT customer_id, 1, NULL, NULL
FROM clean_devoluciones
WHERE customer_id IS NOT NULL
  AND customer_id NOT IN (SELECT cliente_key FROM dim_cliente);
