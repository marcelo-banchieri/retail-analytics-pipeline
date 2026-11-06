-- =====================================================================
-- 10_vistas.sql  |  Vistas analíticas que responden las preguntas de negocio
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) Ventas mensuales: ingreso, facturas, ticket promedio y devoluciones.
--    es_mes_parcial = 1 marca diciembre 2011 (el dataset termina el día 9).
-- ---------------------------------------------------------------------
CREATE VIEW vw_ventas_mensuales AS
WITH ventas AS (
    SELECT d.anio_mes,
           d.es_mes_parcial,
           SUM(f.ingreso)                                   AS ingreso,
           COUNT(DISTINCT f.factura)                        AS facturas,
           SUM(f.cantidad)                                  AS unidades,
           COUNT(DISTINCT NULLIF(f.cliente_key, -1))        AS clientes_identificados
    FROM fact_ventas f
    JOIN dim_fecha d ON d.fecha_key = f.fecha_key
    GROUP BY d.anio_mes, d.es_mes_parcial
),
devol AS (
    SELECT d.anio_mes, SUM(-f.ingreso) AS devoluciones
    FROM fact_devoluciones f
    JOIN dim_fecha d ON d.fecha_key = f.fecha_key
    GROUP BY d.anio_mes
)
SELECT v.anio_mes,
       v.es_mes_parcial,
       ROUND(v.ingreso, 2)                                              AS ingreso,
       v.facturas,
       v.unidades,
       v.clientes_identificados,
       ROUND(v.ingreso / v.facturas, 2)                                 AS ticket_promedio,
       ROUND(COALESCE(dv.devoluciones, 0), 2)                           AS devoluciones,
       ROUND(COALESCE(dv.devoluciones, 0) * 100.0 / v.ingreso, 2)       AS tasa_devolucion_pct
FROM ventas v
LEFT JOIN devol dv ON dv.anio_mes = v.anio_mes
ORDER BY v.anio_mes;

-- ---------------------------------------------------------------------
-- 2) RFM: segmentación de clientes identificados.
--    Recencia = días desde su última compra hasta el día siguiente al fin del dataset.
--    Frecuencia = facturas distintas. Monto = ingreso total.
--    Cada métrica se divide en quintiles (1 = peor, 5 = mejor); los quintiles son
--    relativos a este dataset.
-- ---------------------------------------------------------------------
CREATE VIEW vw_rfm AS
WITH ref AS (
    SELECT date(MAX(fecha_hora), '+1 day') AS fecha_ref FROM fact_ventas
),
base AS (
    SELECT f.cliente_key,
           CAST(julianday((SELECT fecha_ref FROM ref)) - julianday(date(MAX(f.fecha_hora))) AS INTEGER) AS recencia_dias,
           COUNT(DISTINCT f.factura) AS frecuencia,
           SUM(f.ingreso)            AS monto
    FROM fact_ventas f
    WHERE f.cliente_key <> -1
    GROUP BY f.cliente_key
),
puntaje AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recencia_dias DESC) AS r_score,   -- menos días = mejor
           NTILE(5) OVER (ORDER BY frecuencia)         AS f_score,
           NTILE(5) OVER (ORDER BY monto)              AS m_score
    FROM base
)
SELECT cliente_key,
       recencia_dias,
       frecuencia,
       ROUND(monto, 2) AS monto,
       r_score, f_score, m_score,
       CASE
           WHEN r_score >= 4 AND f_score >= 4 THEN 'Campeones'
           WHEN r_score >= 3 AND f_score >= 3 THEN 'Leales'
           WHEN r_score >= 4                  THEN 'Nuevos o recientes'
           WHEN r_score <= 2 AND f_score >= 3 THEN 'En riesgo'
           WHEN r_score <= 2                  THEN 'Perdidos'
           ELSE 'Regulares'
       END AS segmento
FROM puntaje;

-- ---------------------------------------------------------------------
-- 3) Cohortes de retención: qué % de los clientes que compraron por primera
--    vez en el mes X vuelve a comprar N meses después.
--    Ojo: la cohorte 2009-12 incluye clientes que ya existían antes del dataset.
-- ---------------------------------------------------------------------
CREATE VIEW vw_cohortes AS
WITH primera AS (
    SELECT cliente_key, strftime('%Y-%m', MIN(fecha_hora)) AS cohorte
    FROM fact_ventas
    WHERE cliente_key <> -1
    GROUP BY cliente_key
),
actividad AS (
    SELECT DISTINCT cliente_key, strftime('%Y-%m', fecha_hora) AS anio_mes
    FROM fact_ventas
    WHERE cliente_key <> -1
),
cruce AS (
    SELECT p.cohorte,
           a.cliente_key,
           (CAST(substr(a.anio_mes, 1, 4) AS INTEGER) - CAST(substr(p.cohorte, 1, 4) AS INTEGER)) * 12
         + (CAST(substr(a.anio_mes, 6, 2) AS INTEGER) - CAST(substr(p.cohorte, 6, 2) AS INTEGER)) AS meses_desde_inicio
    FROM actividad a
    JOIN primera p ON p.cliente_key = a.cliente_key
),
tamano AS (
    SELECT cohorte, COUNT(*) AS clientes_cohorte FROM primera GROUP BY cohorte
)
SELECT c.cohorte,
       c.meses_desde_inicio,
       COUNT(DISTINCT c.cliente_key) AS clientes_activos,
       t.clientes_cohorte,
       ROUND(100.0 * COUNT(DISTINCT c.cliente_key) / t.clientes_cohorte, 1) AS retencion_pct
FROM cruce c
JOIN tamano t ON t.cohorte = c.cohorte
GROUP BY c.cohorte, c.meses_desde_inicio
ORDER BY c.cohorte, c.meses_desde_inicio;
