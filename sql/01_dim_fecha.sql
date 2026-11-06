-- =====================================================================
-- 01_dim_fecha.sql  |  Calendario continuo entre la primera y la última fecha
-- (sin huecos, para que las series de tiempo en Power BI no salten días)
-- =====================================================================
INSERT INTO dim_fecha (
    fecha_key, fecha, anio, trimestre, mes, anio_mes,
    nombre_mes, dia_semana, nombre_dia, es_mes_parcial
)
WITH RECURSIVE
limite AS (
    SELECT
        date(MIN((SELECT MIN(invoice_date) FROM clean_ventas),
                 (SELECT MIN(invoice_date) FROM clean_devoluciones))) AS min_f,
        date(MAX((SELECT MAX(invoice_date) FROM clean_ventas),
                 (SELECT MAX(invoice_date) FROM clean_devoluciones))) AS max_f
),
calendario (fecha) AS (
    SELECT min_f FROM limite
    UNION ALL
    SELECT date(c.fecha, '+1 day') FROM calendario c, limite l WHERE c.fecha < l.max_f
)
SELECT
    CAST(strftime('%Y%m%d', c.fecha) AS INTEGER),
    c.fecha,
    CAST(strftime('%Y', c.fecha) AS INTEGER),
    (CAST(strftime('%m', c.fecha) AS INTEGER) + 2) / 3,
    CAST(strftime('%m', c.fecha) AS INTEGER),
    strftime('%Y-%m', c.fecha),
    CASE strftime('%m', c.fecha)
        WHEN '01' THEN 'Enero'      WHEN '02' THEN 'Febrero'   WHEN '03' THEN 'Marzo'
        WHEN '04' THEN 'Abril'      WHEN '05' THEN 'Mayo'      WHEN '06' THEN 'Junio'
        WHEN '07' THEN 'Julio'      WHEN '08' THEN 'Agosto'    WHEN '09' THEN 'Septiembre'
        WHEN '10' THEN 'Octubre'    WHEN '11' THEN 'Noviembre' ELSE 'Diciembre'
    END,
    CASE strftime('%w', c.fecha) WHEN '0' THEN 7 ELSE CAST(strftime('%w', c.fecha) AS INTEGER) END,
    CASE strftime('%w', c.fecha)
        WHEN '1' THEN 'Lunes'   WHEN '2' THEN 'Martes'  WHEN '3' THEN 'Miércoles'
        WHEN '4' THEN 'Jueves'  WHEN '5' THEN 'Viernes' WHEN '6' THEN 'Sábado'
        ELSE 'Domingo'
    END,
    -- mes parcial: es el mes de la última fecha y esa fecha no es el último día del mes
    CASE WHEN strftime('%Y-%m', c.fecha) = strftime('%Y-%m', l.max_f)
              AND l.max_f < date(l.max_f, 'start of month', '+1 month', '-1 day')
         THEN 1 ELSE 0 END
FROM calendario c, limite l;
