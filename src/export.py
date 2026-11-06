"""Exportación: deja las tablas del modelo como CSV para conectarlas a Power BI."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd

log = logging.getLogger(__name__)

TABLAS = [
    "dim_fecha", "dim_pais", "dim_cliente", "dim_producto",
    "fact_ventas", "fact_devoluciones",
    "vw_ventas_mensuales", "vw_rfm", "vw_cohortes",
    "log_limpieza",
]


def exportar(conn: sqlite3.Connection, carpeta: Path) -> Dict[str, int]:
    carpeta.mkdir(parents=True, exist_ok=True)
    conteos: Dict[str, int] = {}
    for tabla in TABLAS:
        df = pd.read_sql(f"SELECT * FROM {tabla}", conn)
        df.to_csv(carpeta / f"{tabla}.csv", index=False, encoding="utf-8")
        conteos[tabla] = len(df)
        log.info("Exportado %-22s %10s filas", tabla, f"{len(df):,}")
    return conteos
