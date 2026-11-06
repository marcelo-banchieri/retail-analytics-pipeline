"""Prueba de punta a punta: corre el pipeline completo sobre datos de ejemplo."""
import sqlite3

import pytest

from src import quality
from src.run_pipeline import run
from tests.conftest import ESPERADO


@pytest.fixture
def resultado(csv_ejemplo, tmp_path):
    db = tmp_path / "retail.db"
    resumen = run(csv_path=str(csv_ejemplo), db_path=db, export_dir=tmp_path / "exports")
    return resumen, db, tmp_path


def test_el_pipeline_termina_con_calidad_ok(resultado):
    resumen, _, _ = resultado
    fallas = [c for c in resumen["checks"] if not c["ok"]]
    assert resumen["calidad_ok"], f"Pruebas de calidad fallidas: {fallas}"


def test_conteos(resultado):
    resumen, _, _ = resultado
    assert resumen["filas_originales"] == ESPERADO["filas_originales"]
    assert resumen["ventas_limpias"] == ESPERADO["ventas_limpias"]
    assert resumen["devoluciones"] == ESPERADO["devoluciones"]


def test_dimensiones(resultado):
    _, db, _ = resultado
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM dim_cliente").fetchone()[0] == 4      # 3 clientes + "no identificado"
    assert conn.execute("SELECT COUNT(*) FROM dim_producto").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM dim_pais").fetchone()[0] == 2
    conn.close()


def test_venta_anonima_queda_en_cliente_menos_uno(resultado):
    _, db, _ = resultado
    conn = sqlite3.connect(db)
    ingreso = conn.execute("SELECT SUM(ingreso) FROM fact_ventas WHERE cliente_key = -1").fetchone()[0]
    assert ingreso == pytest.approx(17.00)  # 4 unidades x 4,25
    conn.close()


def test_vista_ventas_mensuales(resultado):
    _, db, _ = resultado
    conn = sqlite3.connect(db)
    filas = {r[0]: r for r in conn.execute(
        "SELECT anio_mes, es_mes_parcial, ingreso, devoluciones FROM vw_ventas_mensuales")}
    assert filas["2011-12"][1] == 1          # diciembre 2011 es parcial (termina el día 9)
    assert filas["2010-01"][1] == 0
    assert filas["2010-02"][2] == pytest.approx(45.90)
    assert filas["2010-02"][3] == pytest.approx(5.10)  # la devolución cae en febrero
    conn.close()


def test_vista_rfm_solo_clientes_identificados(resultado):
    _, db, _ = resultado
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM vw_rfm").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM vw_rfm WHERE segmento IS NULL").fetchone()[0] == 0
    conn.close()


def test_vista_cohortes(resultado):
    _, db, _ = resultado
    conn = sqlite3.connect(db)
    # Cliente 100 compró en 2010-01 y volvió en 2010-03 (2 meses después)
    mes_0, mes_2 = (conn.execute(
        "SELECT retencion_pct FROM vw_cohortes WHERE cohorte = '2010-01' AND meses_desde_inicio = ?", (m,)
    ).fetchone()[0] for m in (0, 2))
    assert mes_0 == 100.0 and mes_2 == 100.0
    conn.close()


def test_exporta_los_csv_para_power_bi(resultado):
    _, _, tmp_path = resultado
    esperados = {"dim_fecha", "dim_pais", "dim_cliente", "dim_producto", "fact_ventas",
                 "fact_devoluciones", "vw_ventas_mensuales", "vw_rfm", "vw_cohortes", "log_limpieza"}
    generados = {p.stem for p in (tmp_path / "exports").glob("*.csv")}
    assert esperados <= generados


def test_el_pipeline_es_idempotente(csv_ejemplo, tmp_path):
    db = tmp_path / "retail.db"
    primera = run(csv_path=str(csv_ejemplo), db_path=db, export_dir=tmp_path / "e1")
    segunda = run(csv_path=str(csv_ejemplo), db_path=db, export_dir=tmp_path / "e2")
    assert primera["ventas_limpias"] == segunda["ventas_limpias"]
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM fact_ventas").fetchone()[0] == ESPERADO["ventas_limpias"]
    assert quality.todos_ok(quality.run_checks(conn))
    conn.close()


def test_falla_con_mensaje_claro_si_faltan_columnas(tmp_path):
    malo = tmp_path / "malo.csv"
    malo.write_text("Invoice,StockCode\n1,2\n")
    with pytest.raises(ValueError, match="Faltan columnas"):
        run(csv_path=str(malo), db_path=tmp_path / "x.db", exportar_csv=False)
