"""Pruebas unitarias de las reglas de limpieza (no necesitan el dataset real)."""
import pytest

from src.clean import limpiar
from tests.conftest import ESPERADO


def test_conteos_finales(df_ejemplo):
    ventas, devoluciones, _ = limpiar(df_ejemplo)
    assert len(ventas) == ESPERADO["ventas_limpias"]
    assert len(devoluciones) == ESPERADO["devoluciones"]


def test_ingresos(df_ejemplo):
    ventas, devoluciones, _ = limpiar(df_ejemplo)
    assert ventas["ingreso"].sum() == pytest.approx(ESPERADO["ingreso_ventas"])
    assert devoluciones["ingreso"].sum() == pytest.approx(ESPERADO["ingreso_devoluciones"])


def test_codigos_no_producto_se_eliminan(df_ejemplo):
    ventas, devoluciones, _ = limpiar(df_ejemplo)
    codigos = set(ventas["stock_code"]) | set(devoluciones["stock_code"])
    assert "POST" not in codigos and "B" not in codigos


def test_precio_cero_se_elimina(df_ejemplo):
    ventas, _, _ = limpiar(df_ejemplo)
    assert (ventas["price"] > 0).all()
    assert "35956" not in set(ventas["stock_code"])


def test_cancelaciones_van_a_devoluciones_y_no_a_ventas(df_ejemplo):
    ventas, devoluciones, _ = limpiar(df_ejemplo)
    assert not ventas["invoice"].str.startswith("C").any()
    assert devoluciones["invoice"].str.startswith("C").all()
    assert (devoluciones["quantity"] < 0).all()


def test_pedidos_erroneos_se_eliminan_de_ambas_tablas(df_ejemplo):
    ventas, devoluciones, _ = limpiar(df_ejemplo)
    assert "23843" not in set(ventas["stock_code"])
    assert "23843" not in set(devoluciones["stock_code"])


def test_duplicados_exactos_se_eliminan(df_ejemplo):
    ventas, _, _ = limpiar(df_ejemplo)
    assert (ventas["invoice"] == "10005").sum() == 1


def test_el_log_concilia(df_ejemplo):
    ventas, _, log = limpiar(df_ejemplo)
    originales = log.iloc[0]["filas_restantes"]
    assert originales == ESPERADO["filas_originales"]
    assert originales - log["filas_removidas"].sum() == len(ventas)
    # cada fila del log arrastra el total del paso anterior
    assert (log["filas_restantes"].diff().dropna() == -log["filas_removidas"].iloc[1:]).all()
