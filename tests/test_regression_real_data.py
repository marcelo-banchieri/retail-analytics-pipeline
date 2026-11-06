"""Prueba de regresión contra el dataset real.

Verifica que el pipeline reproduce EXACTAMENTE los números validados en el EDA
(notebooks/EDA_parte2_online_retail_II.ipynb). Si alguien cambia una regla de limpieza
sin querer, esta prueba lo detecta. Se omite automáticamente si el CSV no está disponible.
"""
import sqlite3

import pytest

from src import config
from src.run_pipeline import run

CSV_REAL = next((p for p in config.RAW_CANDIDATES if p.exists()), None)

pytestmark = pytest.mark.skipif(CSV_REAL is None, reason="No está online_retail_II.csv en data/raw/ ni en data/")

# Números validados a mano en el EDA
FILAS_ORIGINALES = 1_067_371
VENTAS_LIMPIAS = 1_003_211
DEVOLUCIONES = 18_283
INGRESO_LIMPIO = 19_397_022.82
MONTO_DEVOLUCIONES = -480_866.19


@pytest.fixture(scope="module")
def resultado(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("real")
    db = carpeta / "retail.db"
    resumen = run(db_path=db, export_dir=carpeta / "exports", exportar_csv=False)
    return resumen, db


def test_conteos_coinciden_con_el_eda(resultado):
    resumen, _ = resultado
    assert resumen["filas_originales"] == FILAS_ORIGINALES
    assert resumen["ventas_limpias"] == VENTAS_LIMPIAS
    assert resumen["devoluciones"] == DEVOLUCIONES


def test_montos_coinciden_con_el_eda(resultado):
    _, db = resultado
    conn = sqlite3.connect(db)
    ingreso = conn.execute("SELECT SUM(ingreso) FROM fact_ventas").fetchone()[0]
    devol = conn.execute("SELECT SUM(ingreso) FROM fact_devoluciones").fetchone()[0]
    conn.close()
    assert ingreso == pytest.approx(INGRESO_LIMPIO, abs=0.01)
    assert devol == pytest.approx(MONTO_DEVOLUCIONES, abs=0.01)


def test_calidad_ok_con_datos_reales(resultado):
    resumen, _ = resultado
    fallas = [c for c in resumen["checks"] if not c["ok"]]
    assert resumen["calidad_ok"], fallas
