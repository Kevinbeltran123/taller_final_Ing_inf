# Metodología

## Datos

Se usa el *Brazilian E-Commerce Public Dataset by Olist*: pedidos realizados entre 2016 y 2018 en un marketplace brasileño, distribuidos en nueve tablas relacionadas por identificadores (`order_id`, `customer_id`, `product_id`, `seller_id`).

La construcción del conjunto de datos está en `src/datos.py`:

- Se unen pedidos y reseñas por `order_id` (98.673 pedidos con reseña). Cuando un pedido tiene más de una reseña se conserva la última respondida.
- Los ítems se agregan por pedido: número de productos, número de vendedores distintos, precio y flete totales, peso total y fotos promedio del anuncio.
- Las fechas se convierten en duraciones en días: entrega real, entrega estimada, retraso (real − estimada) y despacho del vendedor frente a su fecha límite.
- La distancia vendedor-cliente se calcula con la fórmula de haversine a partir del promedio de coordenadas de cada código postal.

## Variable objetivo

`insatisfecho = 1` si la reseña tiene 1, 2 o 3 estrellas; `0` si tiene 4 o 5. El 22,9 % de los pedidos pertenece a la clase 1.

La calificación de 3 se agrupa con las negativas porque no corresponde a un cliente satisfecho y, para un caso de uso de atención al cliente, también requiere seguimiento.
## Enfoques de modelado

| | Variables del pedido | Texto de la reseña |
|---|---|---|
| Cuaderno | `02_modelo_variables_pedido` | `03_modelo_texto_resenas` |
| Observaciones | 98.673 pedidos | 40.775 pedidos con comentario |
| Variables (X) | 13 variables numéricas del pedido | Bolsa de palabras binaria, `min_df=5` (3.219 palabras) |
| Insatisfechos | 22,9 % | 35,3 % |
| Preprocesamiento | Imputación con mediana, `StandardScaler`, submuestreo de la clase mayoritaria en entrenamiento | Ninguno adicional |

Las 13 variables del primer enfoque son: `entregado`, `dias_entrega_real`, `dias_entrega_estimada`, `dias_retraso`, `dias_despacho_vs_limite`, `n_items`, `n_vendedores`, `precio_total`, `flete_total`, `peso_total_g`, `distancia_km`, `cuotas` y `fotos_prom`. No se incluye ninguna información derivada de la reseña (por ejemplo, su fecha de respuesta) para evitar fuga de información.

En el segundo enfoque el comentario es la entrada del modelo, por lo que la pregunta pasa a ser si un comentario corresponde a un cliente insatisfecho. El caso de uso es priorizar la atención de reseñas negativas a medida que llegan.

## Procedimiento de evaluación

Ambos enfoques siguen el mismo procedimiento (`src/modelos.py`):

1. Partición estratificada 80/20 en entrenamiento y prueba (`random_state=42`).
2. Entrenamiento de cinco clasificadores de scikit-learn con parámetros por defecto: `DecisionTreeClassifier`, `RandomForestClassifier`, `KNeighborsClassifier`, `LogisticRegression` y `MLPClassifier`.
3. Búsqueda de un hiperparámetro por modelo sobre una partición de validación (20 % del entrenamiento):

   | Modelo | Hiperparámetro | Valores |
   |---|---|---|
   | Decision Tree | `max_depth` | 3, 5, 10, 20, 40, sin límite |
   | Random Forest | `n_estimators` | 10, 50, 100, 200 |
   | KNN | `n_neighbors` | 1, 3, 5, 11, 21, 51 |
   | Regresión logística | `C` | 0,01; 0,1; 1; 10 |
   | MLP | `hidden_layer_sizes` | (10,), (50,), (100,), (100, 50) |

   Se selecciona el valor con el mayor F1 mínimo entre las dos clases.
4. Reentrenamiento con todo el conjunto de entrenamiento y evaluación única en prueba.

La métrica es el F1 por clase. El criterio de aceptación es **F1 > 0,7 en ambas clases**. Con clases desbalanceadas, la exactitud no es informativa: un modelo que siempre predice "satisfecho" tendría 77 % de exactitud y F1 = 0 en la clase de interés.

La selección de hiperparámetros con una partición de validación evita elegir valores en función del conjunto de prueba, que debe mantenerse como evaluación sobre datos no vistos.
