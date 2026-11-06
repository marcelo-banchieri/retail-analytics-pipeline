-- =====================================================================
-- 00_schema.sql  |  Esquema estrella (SQLite)
-- Se reconstruye completo en cada ejecución (pipeline idempotente).
-- =====================================================================

-- 1. Limpieza: primero vistas, luego hechos y al final dimensiones
DROP VIEW  IF EXISTS vw_cohortes;
DROP VIEW  IF EXISTS vw_rfm;
DROP VIEW  IF EXISTS vw_ventas_mensuales;
DROP TABLE IF EXISTS fact_devoluciones;
DROP TABLE IF EXISTS fact_ventas;
DROP TABLE IF EXISTS dim_producto;
DROP TABLE IF EXISTS dim_cliente;
DROP TABLE IF EXISTS dim_pais;
DROP TABLE IF EXISTS dim_fecha;

-- 2. Dimensiones
CREATE TABLE dim_fecha (
    fecha_key      INTEGER PRIMARY KEY,   -- formato YYYYMMDD
    fecha          TEXT    NOT NULL,      -- YYYY-MM-DD
    anio           INTEGER NOT NULL,
    trimestre      INTEGER NOT NULL,
    mes            INTEGER NOT NULL,
    anio_mes       TEXT    NOT NULL,      -- YYYY-MM
    nombre_mes     TEXT    NOT NULL,
    dia_semana     INTEGER NOT NULL,      -- 1 = lunes ... 7 = domingo
    nombre_dia     TEXT    NOT NULL,
    es_mes_parcial INTEGER NOT NULL       -- 1 si el dataset termina antes de acabar ese mes
);

CREATE TABLE dim_pais (
    pais_key      INTEGER PRIMARY KEY AUTOINCREMENT,
    pais          TEXT NOT NULL UNIQUE,
    grupo_mercado TEXT NOT NULL           -- 'Reino Unido' o 'Internacional'
);

CREATE TABLE dim_cliente (
    cliente_key     INTEGER PRIMARY KEY,  -- = Customer ID original; -1 = cliente no identificado
    es_identificado INTEGER NOT NULL,
    primera_compra  TEXT,
    ultima_compra   TEXT
);

CREATE TABLE dim_producto (
    producto_key INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code   TEXT NOT NULL UNIQUE,
    descripcion  TEXT                     -- la descripción más frecuente de ese código
);

-- 3. Hechos
CREATE TABLE fact_ventas (
    venta_key       INTEGER PRIMARY KEY AUTOINCREMENT,
    factura         TEXT    NOT NULL,
    fecha_key       INTEGER NOT NULL REFERENCES dim_fecha (fecha_key),
    fecha_hora      TEXT    NOT NULL,
    producto_key    INTEGER NOT NULL REFERENCES dim_producto (producto_key),
    cliente_key     INTEGER NOT NULL REFERENCES dim_cliente (cliente_key),
    pais_key        INTEGER NOT NULL REFERENCES dim_pais (pais_key),
    cantidad        INTEGER NOT NULL,
    precio_unitario REAL    NOT NULL,
    ingreso         REAL    NOT NULL      -- cantidad * precio_unitario (libras)
);

CREATE TABLE fact_devoluciones (
    devolucion_key  INTEGER PRIMARY KEY AUTOINCREMENT,
    factura         TEXT    NOT NULL,     -- factura de cancelación (empieza con C)
    fecha_key       INTEGER NOT NULL REFERENCES dim_fecha (fecha_key),
    fecha_hora      TEXT    NOT NULL,
    producto_key    INTEGER NOT NULL REFERENCES dim_producto (producto_key),
    cliente_key     INTEGER NOT NULL REFERENCES dim_cliente (cliente_key),
    pais_key        INTEGER NOT NULL REFERENCES dim_pais (pais_key),
    cantidad        INTEGER NOT NULL,     -- negativa
    precio_unitario REAL    NOT NULL,
    ingreso         REAL    NOT NULL      -- negativo
);

CREATE INDEX ix_fv_fecha    ON fact_ventas (fecha_key);
CREATE INDEX ix_fv_producto ON fact_ventas (producto_key);
CREATE INDEX ix_fv_cliente  ON fact_ventas (cliente_key);
CREATE INDEX ix_fv_pais     ON fact_ventas (pais_key);
CREATE INDEX ix_fv_factura  ON fact_ventas (factura);
CREATE INDEX ix_fd_fecha    ON fact_devoluciones (fecha_key);
