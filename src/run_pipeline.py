"""Orquestador: ejecuta todo el pipeline de punta a punta.

Uso:
    python -m src.run_pipeline
    python -m src.run_pipeline --csv ruta/al/online_retail_II.csv
    python -m src.run_pipeline --sin-exportar
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional

from . import clean, config, export, ingest, model, quality

log = logging.getLogger("pipeline")


def run(
    csv_path: Optional[str] = None,
    db_path: Optional[Path] = None,
    export_dir: Optional[Path] = None,
    exportar_csv: bool = True,
) -> dict:
    """Ejecuta el pipeline y devuelve un resumen. Es idempotente: se puede correr N veces."""
    csv = config.find_raw_csv(csv_path)
    db_path = Path(db_path or config.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    export_dir = Path(export_dir or config.EXPORT_DIR)

    conn = sqlite3.connect(db_path)
    try:
        inicio = time.time()

        log.info("1/5 Ingesta")
        n_raw = ingest.ingest(csv, conn)

        log.info("2/5 Limpieza")
        conteos = clean.limpiar_desde_db(conn)

        log.info("3/5 Modelo dimensional")
        model.construir_modelo(conn)

        log.info("4/5 Pruebas de calidad")
        resultados = quality.run_checks(conn)
        log.info("\n%s", quality.formatear(resultados))

        exportado = {}
        if exportar_csv and quality.todos_ok(resultados):
            log.info("5/5 Exportación para Power BI")
            exportado = export.exportar(conn, export_dir)
        elif exportar_csv:
            log.error("5/5 Exportación omitida: hay pruebas de calidad que fallaron")

        duracion = time.time() - inicio
        log.info("Listo en %.1f s -> %s", duracion, db_path)
        return {
            "filas_originales": n_raw,
            "ventas_limpias": conteos["ventas"],
            "devoluciones": conteos["devoluciones"],
            "calidad_ok": quality.todos_ok(resultados),
            "checks": resultados,
            "exportado": exportado,
            "segundos": duracion,
        }
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline BI de Online Retail II")
    parser.add_argument("--csv", help="Ruta al online_retail_II.csv (por defecto busca en data/raw/ y data/)")
    parser.add_argument("--sin-exportar", action="store_true", help="No generar los CSV para Power BI")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    resumen = run(csv_path=args.csv, exportar_csv=not args.sin_exportar)
    sys.exit(0 if resumen["calidad_ok"] else 1)


if __name__ == "__main__":
    main()
