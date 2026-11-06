# Diccionario de datos

Todos los montos están en **libras esterlinas (£)**. Las tablas se generan con `python -m src.run_pipeline` y también se exportan como CSV en `exports/powerbi/`.

## Capas intermedias

| Tabla | Descripción |
|---|---|
| `stg_online_retail` | Copia fiel del CSV original, con columnas en snake_case |
| `clean_ventas` | Ventas válidas después de la limpieza (más la columna `ingreso`) |
| `clean_devoluciones` | Cancelaciones (facturas "C") separadas de las ventas |
| `log_limpieza` | Filas removidas y restantes en cada paso de limpieza |

## Dimensiones

### `dim_fecha` — un día por fila, calendario continuo
| Columna | Tipo | Descripción |
|---|---|---|
| `fecha_key` | entero (PK) | Fecha como `YYYYMMDD` |
| `fecha` | texto | `YYYY-MM-DD` |
| `anio`, `trimestre`, `mes` | entero | Componentes de la fecha |
| `anio_mes` | texto | `YYYY-MM` |
| `nombre_mes`, `nombre_dia` | texto | En español |
| `dia_semana` | entero | 1 = lunes … 7 = domingo |
| `es_mes_parcial` | entero | 1 si el dataset termina antes de acabar ese mes (dic 2011) |

### `dim_producto` — un código de stock por fila
| Columna | Tipo | Descripción |
|---|---|---|
| `producto_key` | entero (PK) | Clave sustituta |
| `stock_code` | texto (único) | Código del producto (ej. `85123A`) |
| `descripcion` | texto | Descripción más frecuente de ese código |

### `dim_cliente` — un cliente por fila
| Columna | Tipo | Descripción |
|---|---|---|
| `cliente_key` | entero (PK) | `Customer ID` original; **`-1` = cliente no identificado** |
| `es_identificado` | entero | 1 si tiene `Customer ID`, 0 para el miembro `-1` |
| `primera_compra`, `ultima_compra` | texto | Fecha-hora de su primera y última venta |

### `dim_pais` — un país por fila
| Columna | Tipo | Descripción |
|---|---|---|
| `pais_key` | entero (PK) | Clave sustituta |
| `pais` | texto (único) | Nombre del país |
| `grupo_mercado` | texto | `Reino Unido` o `Internacional` |

## Hechos

### `fact_ventas` — una línea de factura de venta válida
### `fact_devoluciones` — una línea de cancelación (misma estructura)

| Columna | Tipo | Descripción |
|---|---|---|
| `venta_key` / `devolucion_key` | entero (PK) | Clave sustituta |
| `factura` | texto | Número de factura (en devoluciones, empieza con `C`) |
| `fecha_key` | entero (FK) | → `dim_fecha` |
| `fecha_hora` | texto | Fecha y hora de la factura |
| `producto_key` | entero (FK) | → `dim_producto` |
| `cliente_key` | entero (FK) | → `dim_cliente` (`-1` si no hay cliente) |
| `pais_key` | entero (FK) | → `dim_pais` |
| `cantidad` | entero | Unidades (negativa en devoluciones) |
| `precio_unitario` | decimal | Precio por unidad |
| `ingreso` | decimal | `cantidad × precio_unitario` (negativo en devoluciones) |

## Vistas analíticas

### `vw_ventas_mensuales`
| Columna | Descripción |
|---|---|
| `anio_mes`, `es_mes_parcial` | Mes y marca de mes incompleto |
| `ingreso`, `facturas`, `unidades` | Totales del mes |
| `clientes_identificados` | Clientes distintos con `Customer ID` |
| `ticket_promedio` | `ingreso / facturas` |
| `devoluciones` | Monto devuelto en el mes (positivo) |
| `tasa_devolucion_pct` | `devoluciones / ingreso × 100` del mismo mes |

### `vw_rfm` — un cliente identificado por fila
| Columna | Descripción |
|---|---|
| `recencia_dias` | Días desde su última compra hasta el día siguiente al fin del dataset |
| `frecuencia` | Facturas distintas |
| `monto` | Ingreso total |
| `r_score`, `f_score`, `m_score` | Quintiles de 1 (peor) a 5 (mejor), relativos a este dataset |
| `segmento` | Campeones, Leales, Nuevos o recientes, En riesgo, Perdidos, Regulares |

Reglas de segmento: *Campeones* (R ≥ 4 y F ≥ 4), *Leales* (R ≥ 3 y F ≥ 3), *Nuevos o recientes* (R ≥ 4), *En riesgo* (R ≤ 2 y F ≥ 3), *Perdidos* (R ≤ 2), *Regulares* (el resto).

### `vw_cohortes`
| Columna | Descripción |
|---|---|
| `cohorte` | Mes de la primera compra (`YYYY-MM`) |
| `meses_desde_inicio` | Meses transcurridos desde esa primera compra |
| `clientes_activos` | Clientes de la cohorte que compraron ese mes |
| `clientes_cohorte` | Tamaño de la cohorte |
| `retencion_pct` | `clientes_activos / clientes_cohorte × 100` |
