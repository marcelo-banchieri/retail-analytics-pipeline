-- =====================================================================
-- 06_fact_devoluciones.sql  |  Una fila por línea de cancelación (facturas "C")
-- Cantidad e ingreso quedan negativos, tal como vienen en el origen.
-- =====================================================================
INSERT INTO fact_devoluciones (
    factura, fecha_key, fecha_hora, producto_key, cliente_key, pais_key,
    cantidad, precio_unitario, ingreso
)
SELECT
    d.invoice,
    CAST(strftime('%Y%m%d', d.invoice_date) AS INTEGER),
    d.invoice_date,
    p.producto_key,
    COALESCE(d.customer_id, -1),
    pa.pais_key,
    d.quantity,
    d.price,
    d.ingreso
FROM clean_devoluciones d
JOIN dim_producto p  ON p.stock_code = d.stock_code
JOIN dim_pais     pa ON pa.pais      = d.country;
