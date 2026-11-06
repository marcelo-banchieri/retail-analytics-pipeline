# Hallazgos del análisis exploratorio (EDA)

Dataset: **Online Retail II** — 1.067.371 filas y 8 columnas, del 2009-12-01 al 2011-12-09.
Cuaderno de origen: [`notebooks/EDA_parte2_online_retail_II.ipynb`](../notebooks/EDA_parte2_online_retail_II.ipynb) (la parte 1 del EDA fue el diagnóstico inicial en Google Colab).

Cada hallazgo termina en una **decisión** que el pipeline aplica en `src/clean.py`.

---

## Parte 1 — Diagnóstico de calidad

| Hallazgo | Detalle | Decisión |
|---|---|---|
| `Description` nula | 4.382 filas (~0,4 %) | Poco relevante; se conservan |
| `Customer ID` nulo | 243.007 filas (22,8 %): casi 1 de cada 4 líneas sin cliente identificado | Se conservan; se asignan al cliente `-1` y se excluyen de RFM y cohortes |
| Filas duplicadas | 34.335 en el dataset original (~3,2 %) | Se eliminan los duplicados exactos de las ventas (ver Parte 2) |
| Rango temporal | 2009-12-01 a 2011-12-09 (2 años) | Suficiente para estacionalidad |
| Precio negativo | 5 filas: ajustes de deuda incobrable (código `B`, "Adjust bad debt") | Se excluyen: no son ventas |
| Precio = 0 | 6.202 filas: ajustes de inventario ("lost", "damages", "mixed") | Se excluyen de las ventas |
| País | Reino Unido concentra ~92 % de las transacciones (981.330 filas) | `dim_pais` agrupa en *Reino Unido* / *Internacional* |
| Estacionalidad | Noviembre es el mes pico en ambos años (78.015 y 84.711 transacciones) | Se documenta; `vw_ventas_mensuales` lo muestra |
| Mes parcial | Diciembre 2011 termina el día 9; su caída no es real | `dim_fecha.es_mes_parcial = 1` |

---

## Parte 2 — Cancelaciones, códigos, outliers e ingresos

### Cantidades negativas
22.950 filas con cantidad negativa:
- **19.493** son cancelaciones reales (facturas que empiezan con "C").
- **3.457** son ajustes de inventario: todas con precio 0 y sin `Customer ID`.

Casos particulares:
- Una factura C con cantidad **positiva** (`C496350`, código `M` "Manual"): ajuste manual, se elimina junto con los códigos no-producto.
- Seis facturas con prefijo A, todas del código `B` ("Adjust bad debt"). Una (`A563185`) tiene precio **positivo** (+£11.062,06) y las dos siguientes son −£11.062,06 cada una. Por eso un filtro solo por precio no basta: **se filtra por tipo de código primero**.

### Códigos que no son productos
6.094 filas (0,57 %). Los más frecuentes: `POST`, `DOT`, `M`, `C2`, `D`.
Regla: un producto real es un código de 5 dígitos con letras opcionales al final (`^\d{5}[A-Za-z]*$`).

### Valores atípicos

- **Dos pedidos erróneos.** `541431` (74.215 unidades por £77.183,60) y `581483` (80.995 unidades por £168.469,60) suman **£245.653,20 (~1,2 % del ingreso)**. Ambos tienen cancelación par (`C541433` y `C581484`, a los 16 y 12 minutos). Si se dejaban, la venta quedaba en el ingreso y la cancelación en las devoluciones, inflando ambos números (los £245.653 eran cerca de un 34 % del monto de devoluciones). **Decisión: eliminar ambos pedidos junto con su cancelación.**
- **Cantidades altas a £0,10–£0,25** (10.000 a 19.000 unidades): pocos clientes, parecen pedidos mayoristas legítimos. Se conservan.
- **Precios altos.** "Flag of St George Car Flag" aparece entre £408 y £1.157 sin cliente: valor implausible, pero de impacto despreciable (~£2.400). Se conserva y se documenta. El resto (cestas de picnic a £649, gabinetes vintage a £295) son artículos caros pero plausibles.

### Duplicados
33.663 duplicados exactos eliminados de las ventas (misma factura, producto, cantidad, precio, fecha y cliente).
**Decisión:** eliminarlos, porque no hay forma de distinguir un registro doble del sistema de una línea legítima repetida.
**Riesgo:** una posible subestimación del ingreso de hasta ~2,3 % (£466.303 de £20.108.979).

### Ingresos (después de limpiar)

| Métrica | Valor |
|---|---:|
| Ingreso total limpio | £19.397.022,82 |
| Sin `Customer ID` | 13,3 % del ingreso |
| Reino Unido | 85,3 % del ingreso |
| Devoluciones | £480.866,19 (2,5 % del ingreso limpio) |
| Filas finales | 1.003.211 de 1.067.371 (94,0 %) |

### Log de limpieza

| Paso | Filas removidas | Filas restantes |
|---|---:|---:|
| Datos originales | 0 | 1.067.371 |
| Quitar códigos que no son producto | 6.094 | 1.061.277 |
| Quitar precio ≤ 0 | 6.116 | 1.055.161 |
| Quitar 2 pedidos erróneos y sus cancelaciones | 4 | 1.055.157 |
| Separar cancelaciones (facturas C) a devoluciones | 18.283 | 1.036.874 |
| Quitar cantidades ≤ 0 restantes | 0 | 1.036.874 |
| Quitar duplicados exactos | 33.663 | 1.003.211 |

Conciliación: 6.094 + 6.116 + 4 + 18.283 + 33.663 = 64.160 filas; 1.067.371 − 64.160 = 1.003.211.
