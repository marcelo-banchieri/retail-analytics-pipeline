"""Pruebas de calidad de datos sobre el modelo ya construido.

Se usan en dos lugares: al final del pipeline (si algo falla, el pipeline termina
con error) y en pytest (tests/test_pipeline_e2e.py).
"""
from __future__ import annotations

import re
import sqlite3
from typing import Dict, List

from . import config

TOLERANCIA = 0.01  # diferencia máxima aceptada al comparar montos (en libras)


def _uno(conn: sqlite3.Connection, sql: str):
    return conn.execute(sql).fetchone()[0]


def run_checks(conn: sqlite3.Connection) -> List[Dict]:
    resultados: List[Dict] = []

    def check(nombre: str, ok: bool, detalle: str = "") -> None:
        resultados.append({"check": nombre, "ok": bool(ok), "detalle": detalle})

    # 1. Conciliación de filas entre capa limpia y modelo
    n_clean = _uno(conn, "SELECT COUNT(*) FROM clean_ventas")
    n_fact = _uno(conn, "SELECT COUNT(*) FROM fact_ventas")
    check("fact_ventas tiene las mismas filas que clean_ventas", n_clean == n_fact,
          f"clean={n_clean:,} fact={n_fact:,}")

    n_clean_d = _uno(conn, "SELECT COUNT(*) FROM clean_devoluciones")
    n_fact_d = _uno(conn, "SELECT COUNT(*) FROM fact_devoluciones")
    check("fact_devoluciones tiene las mismas filas que clean_devoluciones", n_clean_d == n_fact_d,
          f"clean={n_clean_d:,} fact={n_fact_d:,}")

    # 2. Conciliación de montos
    ing_clean = _uno(conn, "SELECT COALESCE(SUM(ingreso), 0) FROM clean_ventas")
    ing_fact = _uno(conn, "SELECT COALESCE(SUM(ingreso), 0) FROM fact_ventas")
    check("El ingreso de fact_ventas coincide con clean_ventas", abs(ing_clean - ing_fact) < TOLERANCIA,
          f"clean={ing_clean:,.2f} fact={ing_fact:,.2f}")

    dev_clean = _uno(conn, "SELECT COALESCE(SUM(ingreso), 0) FROM clean_devoluciones")
    dev_fact = _uno(conn, "SELECT COALESCE(SUM(ingreso), 0) FROM fact_devoluciones")
    check("El monto de fact_devoluciones coincide con clean_devoluciones", abs(dev_clean - dev_fact) < TOLERANCIA,
          f"clean={dev_clean:,.2f} fact={dev_fact:,.2f}")

    # 3. Reglas de negocio sobre los hechos
    malas_v = _uno(conn, "SELECT COUNT(*) FROM fact_ventas "
                         "WHERE cantidad <= 0 OR precio_unitario <= 0 OR ingreso <= 0")
    check("fact_ventas no tiene cantidades, precios ni ingresos <= 0", malas_v == 0, f"filas malas={malas_v:,}")

    malas_d = _uno(conn, "SELECT COUNT(*) FROM fact_devoluciones WHERE cantidad >= 0 OR ingreso >= 0")
    check("fact_devoluciones solo tiene cantidades negativas", malas_d == 0, f"filas malas={malas_d:,}")

    # 4. Integridad referencial y nulos
    for fact in ("fact_ventas", "fact_devoluciones"):
        for dim, clave in (("dim_fecha", "fecha_key"), ("dim_producto", "producto_key"),
                           ("dim_cliente", "cliente_key"), ("dim_pais", "pais_key")):
            huerfanas = _uno(conn, f"SELECT COUNT(*) FROM {fact} f "
                                   f"LEFT JOIN {dim} d ON d.{clave} = f.{clave} WHERE d.{clave} IS NULL")
            check(f"{fact}.{clave} apunta siempre a {dim}", huerfanas == 0, f"huérfanas={huerfanas:,}")
        nulos = _uno(conn, f"SELECT COUNT(*) FROM {fact} WHERE factura IS NULL OR fecha_key IS NULL "
                           "OR producto_key IS NULL OR cliente_key IS NULL OR pais_key IS NULL")
        check(f"{fact} no tiene nulos en sus claves", nulos == 0, f"filas con nulos={nulos:,}")

    # 5. Dimensiones
    codigos = [fila[0] for fila in conn.execute("SELECT stock_code FROM dim_producto")]
    patron = re.compile(config.PATRON_PRODUCTO)
    no_producto = [c for c in codigos if not patron.match(c)]
    check("dim_producto solo contiene códigos de producto reales", not no_producto,
          f"códigos raros={no_producto[:5]}")

    check("dim_cliente incluye el miembro 'cliente no identificado' (-1)",
          _uno(conn, "SELECT COUNT(*) FROM dim_cliente WHERE cliente_key = -1") == 1)

    n_dias = _uno(conn, "SELECT COUNT(*) FROM dim_fecha")
    esperado = _uno(conn, "SELECT CAST(julianday(MAX(fecha)) - julianday(MIN(fecha)) AS INTEGER) + 1 FROM dim_fecha")
    check("dim_fecha es un calendario continuo (sin días faltantes)", n_dias == esperado,
          f"filas={n_dias:,} esperadas={esperado:,}")

    # 6. Conciliación con el log de limpieza
    n_stg = _uno(conn, "SELECT COUNT(*) FROM stg_online_retail")
    originales = _uno(conn, "SELECT filas_restantes FROM log_limpieza ORDER BY rowid LIMIT 1")
    removidas = _uno(conn, "SELECT SUM(filas_removidas) FROM log_limpieza")
    check("El log parte con las filas del staging", originales == n_stg,
          f"log={originales:,} staging={n_stg:,}")
    check("El log concilia: originales - removidas = ventas limpias", originales - removidas == n_clean,
          f"{originales:,} - {removidas:,} = {originales - removidas:,}; ventas limpias={n_clean:,}")

    return resultados


def todos_ok(resultados: List[Dict]) -> bool:
    return all(r["ok"] for r in resultados)


def formatear(resultados: List[Dict]) -> str:
    lineas = []
    for r in resultados:
        marca = "OK   " if r["ok"] else "FALLA"
        detalle = f"  ({r['detalle']})" if r["detalle"] else ""
        lineas.append(f"[{marca}] {r['check']}{detalle}")
    return "\n".join(lineas)
