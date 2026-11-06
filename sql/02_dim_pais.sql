-- =====================================================================
-- 02_dim_pais.sql  |  Un país por fila, con agrupación UK vs Internacional
-- (UK concentra ~92% de las transacciones; agruparlo evita que domine los gráficos)
-- =====================================================================
INSERT INTO dim_pais (pais, grupo_mercado)
SELECT
    pais,
    CASE WHEN pais = 'United Kingdom' THEN 'Reino Unido' ELSE 'Internacional' END
FROM (
    SELECT country AS pais FROM clean_ventas
    UNION
    SELECT country AS pais FROM clean_devoluciones
)
ORDER BY pais;
