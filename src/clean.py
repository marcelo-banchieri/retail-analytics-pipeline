"""Limpieza: aplica las reglas definidas en el EDA y deja un log de cada paso.

Las cancelaciones (facturas que empiezan con "C") NO se descartan: se separan
en una tabla de devoluciones, porque son información de negocio.
"""
from __future__ import annotations

import logging
import sqlite3
from typing import Tuple

import pandas as pd

from . import config

log = logging.getLogger(__name__)

COLUMNAS_NEGOCIO = [
    "invoice", "stock_code", "description", "quantity",
    "invoice_date", "price", "customer_id", "country",
]
COLUMNAS_SALIDA = COLUMNAS_NEGOCIO + ["ingreso"]


def limpiar(staging: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Devuelve (ventas_limpias, devoluciones, log_de_limpieza)."""
    total = len(staging)
    df = staging.copy()
    df["es_producto"] = df["stock_code"].str.match(config.PATRON_PRODUCTO).fillna(False).astype(bool)
    df["es_cancelacion"] = df["invoice"].str.startswith("C").fillna(False).astype(bool)
    df["ingreso"] = df["quantity"] * df["price"]

    registro = [{"paso": "Datos originales", "filas_removidas": 0, "filas_restantes": total}]
    actual = df

    def aplicar(nombre, mascara):
        nonlocal actual
        antes = len(actual)
        actual = actual[mascara(actual)]
        registro.append(
            {"paso": nombre, "filas_removidas": antes - len(actual), "filas_restantes": len(actual)}
        )

    aplicar(
        "Quitar códigos que no son producto (POST, M, B, etc.)",
        lambda d: d["es_producto"],
    )
    aplicar(
        "Quitar precio <= 0 (ajustes de inventario y deuda incobrable)",
        lambda d: d["price"] > 0,
    )
    aplicar(
        "Quitar 2 pedidos erróneos y sus cancelaciones (líneas de 74.215 y 80.995 unidades)",
        lambda d: ~(
            d["stock_code"].isin(config.CODIGOS_PEDIDO_ERRONEO)
            & (d["quantity"].abs() > config.UMBRAL_CANTIDAD_ERRONEA)
        ),
    )

    # Las cancelaciones se guardan aparte antes de sacarlas de las ventas
    devoluciones = actual[actual["es_cancelacion"]].copy()
    aplicar(
        "Separar cancelaciones (facturas C) a tabla de devoluciones",
        lambda d: ~d["es_cancelacion"],
    )
    aplicar("Quitar cantidades <= 0 restantes", lambda d: d["quantity"] > 0)
    aplicar(
        "Quitar duplicados exactos",
        lambda d: ~d.duplicated(subset=COLUMNAS_NEGOCIO),
    )

    ventas = actual[COLUMNAS_SALIDA].copy()
    devoluciones = devoluciones[COLUMNAS_SALIDA]

    log_df = pd.DataFrame(registro)
    log_df["pct_del_original"] = (log_df["filas_removidas"] / total * 100).round(2)
    return ventas, devoluciones, log_df


def limpiar_desde_db(conn: sqlite3.Connection) -> dict:
    """Lee el staging, limpia y guarda `clean_ventas`, `clean_devoluciones` y `log_limpieza`."""
    staging = pd.read_sql("SELECT * FROM stg_online_retail", conn)
    staging["customer_id"] = staging["customer_id"].astype("Int64")
    ventas, devoluciones, log_df = limpiar(staging)

    ventas.to_sql("clean_ventas", conn, if_exists="replace", index=False, chunksize=100_000)
    devoluciones.to_sql("clean_devoluciones", conn, if_exists="replace", index=False, chunksize=100_000)
    log_df.to_sql("log_limpieza", conn, if_exists="replace", index=False)

    for fila in log_df.itertuples():
        log.info("%-85s -%s -> %s", fila.paso, f"{fila.filas_removidas:,}", f"{fila.filas_restantes:,}")
    return {"ventas": len(ventas), "devoluciones": len(devoluciones)}
