"""Ingesta: lee el CSV original y lo carga sin transformar a la tabla de staging."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

# Nombres originales del dataset -> nombres normalizados (snake_case)
COLUMNAS = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}


def leer_csv(ruta: Path) -> pd.DataFrame:
    """Lee el CSV, valida columnas y normaliza tipos (sin tocar los valores)."""
    df = pd.read_csv(
        ruta,
        dtype={"Invoice": str, "StockCode": str, "Description": str, "Country": str},
    )
    faltantes = set(COLUMNAS) - set(df.columns)
    if faltantes:
        raise ValueError(
            f"Faltan columnas en el CSV: {sorted(faltantes)}. "
            f"Columnas encontradas: {list(df.columns)}"
        )
    df = df[list(COLUMNAS)].rename(columns=COLUMNAS)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    # En el CSV el ID viene como decimal (13085.0) porque hay nulos; lo pasamos a entero con nulos
    df["customer_id"] = df["customer_id"].astype("Int64")
    return df


def ingest(ruta: Path, conn: sqlite3.Connection) -> int:
    """Carga el CSV a `stg_online_retail`. Reemplaza la tabla si existe (idempotente)."""
    log.info("Leyendo %s", ruta)
    df = leer_csv(ruta)
    df.to_sql("stg_online_retail", conn, if_exists="replace", index=False, chunksize=100_000)
    log.info("Staging cargado: %s filas", f"{len(df):,}")
    return len(df)
