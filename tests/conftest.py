"""Datos de ejemplo mínimos con un caso de cada situación que el EDA encontró en el dataset real."""
import numpy as np
import pandas as pd
import pytest

COLUMNAS = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
UK = "United Kingdom"

# Cada fila lleva un comentario con lo que debería pasar con ella.
FILAS = [
    ("10001", "85123A", "WHITE HANGING HEART", 6, "2010-01-04 10:00:00", 2.55, 100, UK),   # venta válida
    ("10001", "71053", "WHITE METAL LANTERN", 8, "2010-01-04 10:00:00", 3.39, 100, UK),    # venta válida
    ("10001", "POST", "POSTAGE", 1, "2010-01-04 10:00:00", 18.0, 100, UK),                 # código no-producto
    ("10002", "85123A", "WHITE HANGING HEART", 12, "2010-02-10 11:30:00", 2.55, 200, UK),  # venta válida
    ("10002", "22752", "SET 7 BABUSHKA NESTING BOXES", 2, "2010-02-10 11:30:00", 7.65, 200, UK),  # venta válida
    ("C10003", "85123A", "WHITE HANGING HEART", -2, "2010-02-12 09:00:00", 2.55, 200, UK),  # devolución real
    ("10004", "84879", "ASSORTED COLOUR BIRD ORNAMENT", 10, "2011-12-05 14:00:00", 1.69, 300, "France"),  # venta válida
    ("10005", "21730", "GLASS STAR FROSTED T-LIGHT HOLDER", 4, "2011-12-09 12:50:00", 4.25, None, UK),  # venta anónima válida
    ("10005", "21730", "GLASS STAR FROSTED T-LIGHT HOLDER", 4, "2011-12-09 12:50:00", 4.25, None, UK),  # duplicado exacto
    ("10006", "35956", "lost", -50, "2010-01-20 15:00:00", 0.0, None, UK),                 # ajuste de inventario (precio 0)
    ("A10007", "B", "Adjust bad debt", 1, "2010-04-29 13:36:00", -5000.0, None, UK),        # deuda incobrable
    ("10008", "23843", "PAPER CRAFT , LITTLE BIRDIE", 80995, "2011-12-09 09:15:00", 2.08, 400, UK),   # pedido erróneo
    ("C10009", "23843", "PAPER CRAFT , LITTLE BIRDIE", -80995, "2011-12-09 09:27:00", 2.08, 400, UK),  # su cancelación
    ("10010", "85123A", "WHITE HANGING HEART", 6, "2010-03-01 10:00:00", 2.55, 100, UK),   # venta válida (2ª compra del cliente 100)
]

# Resultado esperado al limpiar FILAS (calculado a mano)
ESPERADO = {
    "filas_originales": 14,
    "ventas_limpias": 7,
    "devoluciones": 1,
    "ingreso_ventas": 137.52,
    "ingreso_devoluciones": -5.10,
}


@pytest.fixture
def df_ejemplo() -> pd.DataFrame:
    """Datos de ejemplo con los nombres de columnas ya normalizados (como el staging)."""
    df = pd.DataFrame(FILAS, columns=COLUMNAS)
    df = df.rename(columns={
        "Invoice": "invoice", "StockCode": "stock_code", "Description": "description",
        "Quantity": "quantity", "InvoiceDate": "invoice_date", "Price": "price",
        "Customer ID": "customer_id", "Country": "country",
    })
    df["customer_id"] = df["customer_id"].astype("Int64")
    return df


@pytest.fixture
def csv_ejemplo(tmp_path):
    """El mismo ejemplo escrito como CSV con el formato original del dataset."""
    df = pd.DataFrame(FILAS, columns=COLUMNAS)
    df["Customer ID"] = df["Customer ID"].astype(float)  # en el CSV real viene como 13085.0 / vacío
    ruta = tmp_path / "online_retail_II.csv"
    df.to_csv(ruta, index=False)
    return ruta
