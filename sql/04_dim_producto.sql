-- =====================================================================
-- 04_dim_producto.sql  |  Un producto por código de stock
-- Un mismo código puede aparecer con descripciones distintas (errores de digitación,
-- cambios de nombre). Se elige la más frecuente; en empate, la primera alfabéticamente.
-- =====================================================================
INSERT INTO dim_producto (stock_code, descripcion)
WITH conteo AS (
    SELECT stock_code, description, COUNT(*) AS n
    FROM clean_ventas
    WHERE description IS NOT NULL
    GROUP BY stock_code, description
),
ranking AS (
    SELECT stock_code, description,
           ROW_NUMBER() OVER (PARTITION BY stock_code ORDER BY n DESC, description) AS rn
    FROM conteo
),
codigos AS (
    SELECT stock_code FROM clean_ventas
    UNION
    SELECT stock_code FROM clean_devoluciones
)
SELECT c.stock_code, r.description
FROM codigos c
LEFT JOIN ranking r ON r.stock_code = c.stock_code AND r.rn = 1
ORDER BY c.stock_code;
