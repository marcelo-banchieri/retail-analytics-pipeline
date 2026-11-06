"""Modelo dimensional: ejecuta los scripts de la carpeta sql/ en orden alfabético."""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from . import config

log = logging.getLogger(__name__)


def construir_modelo(conn: sqlite3.Connection, sql_dir: Optional[Path] = None) -> None:
    """Reconstruye dimensiones, hechos y vistas a partir de las tablas clean_*.

    El orden de los archivos importa: primero el esquema, luego las dimensiones,
    luego los hechos y por último las vistas (por eso llevan prefijo numérico).
    """
    sql_dir = sql_dir or config.SQL_DIR
    conn.execute("PRAGMA foreign_keys = ON")
    for archivo in sorted(sql_dir.glob("*.sql")):
        log.info("Ejecutando %s", archivo.name)
        conn.executescript(archivo.read_text(encoding="utf-8"))
    conn.commit()
