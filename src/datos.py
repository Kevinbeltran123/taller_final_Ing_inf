"""Carga de las tablas de Olist y construcción del conjunto de datos a nivel de pedido."""

from pathlib import Path

import numpy as np
import pandas as pd

FECHAS_PEDIDO = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

# Variables explicativas del primer enfoque (solo información del pedido)
VARIABLES_PEDIDO = [
    "entregado",
    "dias_entrega_real",
    "dias_entrega_estimada",
    "dias_retraso",
    "dias_despacho_vs_limite",
    "n_items",
    "n_vendedores",
    "precio_total",
    "flete_total",
    "peso_total_g",
    "distancia_km",
    "cuotas",
    "fotos_prom",
]


def cargar_tablas(ruta):
    """Lee los CSV del dataset y devuelve un diccionario de DataFrames."""
    ruta = Path(ruta)
    leer = lambda nombre, **kw: pd.read_csv(ruta / f"{nombre}.csv", **kw)
    return {
        "pedidos": leer("olist_orders_dataset", parse_dates=FECHAS_PEDIDO),
        "resenas": leer("olist_order_reviews_dataset",
                        parse_dates=["review_creation_date", "review_answer_timestamp"]),
        "items": leer("olist_order_items_dataset", parse_dates=["shipping_limit_date"]),
        "pagos": leer("olist_order_payments_dataset"),
        "productos": leer("olist_products_dataset"),
        "clientes": leer("olist_customers_dataset", dtype={"customer_zip_code_prefix": str}),
        "vendedores": leer("olist_sellers_dataset", dtype={"seller_zip_code_prefix": str}),
        "geo": leer("olist_geolocation_dataset", dtype={"geolocation_zip_code_prefix": str}),
        "categorias": leer("product_category_name_translation"),
    }


def _a_dias(delta):
    return delta.dt.total_seconds() / 86400


def _distancia_km(lat1, lon1, lat2, lon2):
    """Distancia de haversine entre dos puntos (en km)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def construir_pedidos(t):
    """Une las tablas y genera una fila por pedido con reseña.

    Incluye la variable objetivo `insatisfecho` (1 si la reseña tiene 1 a 3 estrellas),
    las variables de VARIABLES_PEDIDO y algunas columnas descriptivas.
    """
    # Algunos pedidos tienen más de una reseña: se conserva la última respondida.
    resenas = (t["resenas"]
               .sort_values(["review_answer_timestamp", "review_id"], kind="mergesort")
               .drop_duplicates("order_id", keep="last")
               [["order_id", "review_score", "review_comment_message"]])

    df = t["pedidos"].merge(resenas, on="order_id", how="inner")
    df["insatisfecho"] = (df["review_score"] <= 3).astype(int)

    # Tiempos de entrega
    df["entregado"] = (df["order_status"] == "delivered").astype(int)
    df["dias_entrega_real"] = _a_dias(df["order_delivered_customer_date"] - df["order_purchase_timestamp"])
    df["dias_entrega_estimada"] = _a_dias(df["order_estimated_delivery_date"] - df["order_purchase_timestamp"])
    df["dias_retraso"] = _a_dias(df["order_delivered_customer_date"] - df["order_estimated_delivery_date"])

    # Productos y vendedores del pedido
    items = (t["items"]
             .merge(t["productos"], on="product_id", how="left")
             .merge(t["categorias"], on="product_category_name", how="left")
             .sort_values(["order_id", "order_item_id"], kind="mergesort"))
    resumen = items.groupby("order_id").agg(
        n_items=("order_item_id", "count"),
        n_vendedores=("seller_id", "nunique"),
        precio_total=("price", "sum"),
        flete_total=("freight_value", "sum"),
        peso_total_g=("product_weight_g", "sum"),
        fotos_prom=("product_photos_qty", "mean"),
        limite_envio=("shipping_limit_date", "max"),
        categoria=("product_category_name_english", "first"),
        seller_id=("seller_id", "first"),
    ).reset_index()
    df = df.merge(resumen, on="order_id", how="left")
    df["dias_despacho_vs_limite"] = _a_dias(df["order_delivered_carrier_date"] - df["limite_envio"])

    # Pagos
    cuotas = t["pagos"].groupby("order_id")["payment_installments"].max().rename("cuotas")
    df = df.merge(cuotas, on="order_id", how="left")

    # Ubicación de cliente y vendedor
    coords = t["geo"].groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]].mean()
    df = df.merge(t["clientes"][["customer_id", "customer_zip_code_prefix", "customer_state"]],
                  on="customer_id", how="left")
    df = df.merge(t["vendedores"][["seller_id", "seller_zip_code_prefix"]], on="seller_id", how="left")
    df = df.merge(coords.add_prefix("cli_"), left_on="customer_zip_code_prefix", right_index=True, how="left")
    df = df.merge(coords.add_prefix("ven_"), left_on="seller_zip_code_prefix", right_index=True, how="left")
    df["distancia_km"] = _distancia_km(df["cli_geolocation_lat"], df["cli_geolocation_lng"],
                                       df["ven_geolocation_lat"], df["ven_geolocation_lng"])

    # Columnas de apoyo para el análisis exploratorio
    df["mes_compra"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["tiene_comentario"] = df["review_comment_message"].notna().astype(int)
    no_entregado = (df["entregado"] == 0) | df["dias_retraso"].isna()
    df["estado_entrega"] = np.select(
        [no_entregado, df["dias_retraso"] > 0],
        ["No entregado", "Tarde"],
        default="A tiempo",
    )

    return df.drop(columns=["cli_geolocation_lat", "cli_geolocation_lng",
                            "ven_geolocation_lat", "ven_geolocation_lng"])


def cargar_pedidos(ruta):
    return construir_pedidos(cargar_tablas(ruta))
