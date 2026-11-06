-- =====================================================================
-- 05_fact_ventas.sql  |  Una fila por línea de factura de venta válida
-- =====================================================================
INSERT INTO fact_ventas (
    factura, fecha_key, fecha_hora, producto_key, cliente_key, pais_key,
    cantidad, precio_unitario, ingreso
)
SELECT
    v.invoice,
    CAST(strftime('%Y%m%d', v.invoice_date) AS INTEGER),
    v.invoice_date,
    p.producto_key,
    COALESCE(v.customer_id, -1),
    pa.pais_key,
    v.quantity,
    v.price,
    v.ingreso
FROM clean_ventas v
JOIN dim_producto p  ON p.stock_code = v.stock_code
JOIN dim_pais     pa ON pa.pais      = v.country;
