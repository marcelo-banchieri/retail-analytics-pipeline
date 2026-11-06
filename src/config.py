"""Configuración central: rutas y reglas de negocio del pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SQL_DIR = ROOT / "sql"
WAREHOUSE_DIR = ROOT / "warehouse"
DB_PATH = WAREHOUSE_DIR / "retail.db"
EXPORT_DIR = ROOT / "exports" / "powerbi"

# Dónde buscar el CSV original si no se indica uno explícito con --csv
RAW_CANDIDATES = [
    DATA_DIR / "raw" / "online_retail_II.csv",
    DATA_DIR / "online_retail_II.csv",
]

# --- Reglas de limpieza (justificación en docs/hallazgos_eda.md) ---
# Un código de producto "normal" son 5 dígitos con letras opcionales al final (ej: 85123A).
# Todo lo demás (POST, M, D, B, C2, DOT, BANK CHARGES, ...) no es un producto vendido.
PATRON_PRODUCTO = r"^\d{5}[A-Za-z]*$"

# Dos pedidos digitados por error y cancelados minutos después (ver hallazgos del EDA).
CODIGOS_PEDIDO_ERRONEO = ["23843", "23166"]
UMBRAL_CANTIDAD_ERRONEA = 70_000


def find_raw_csv(explicit: Optional[str] = None) -> Path:
    """Devuelve la ruta del CSV original, o falla con un mensaje claro."""
    if explicit:
        ruta = Path(explicit)
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo indicado: {ruta}")
        return ruta
    for candidato in RAW_CANDIDATES:
        if candidato.exists():
            return candidato
    raise FileNotFoundError(
        "No encontré online_retail_II.csv. Colócalo en data/raw/ (o en data/) "
        "o indica la ruta con --csv."
    )
