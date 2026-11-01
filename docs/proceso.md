# Proceso y decisiones

Este documento resume el razonamiento que llevó del primer al segundo enfoque de modelado. Los detalles y el código están en los cuadernos de `notebooks/`.

## 1. Pregunta

¿Es posible identificar automáticamente a un cliente insatisfecho (reseña de 1 a 3 estrellas) a partir de los datos de Olist?

## 2. Análisis descriptivo (cuaderno 01)

- El 22,9 % de los 98.673 pedidos con reseña corresponde a clientes insatisfechos.
- La insatisfacción sube en noviembre de 2017 (27,9 %) y en febrero-marzo de 2018 (30,2 % y 32,0 %).
- Es mayor en muebles de oficina (36,9 %) y en los estados de Ceará, Bahía y Río de Janeiro (≈29 %); São Paulo tiene 20,6 %.
- El 63,5 % de los insatisfechos deja comentario, frente al 34,7 % de los satisfechos.

## 3. Análisis diagnóstico (cuaderno 01)

| Estado de la entrega | Pedidos | % insatisfechos |
|---|---:|---:|
| A tiempo | 88.163 | 17,2 |
| Tarde | 7.661 | 65,4 |
| No entregado | 2.849 | 85,6 |

- Desde 4 días de retraso, más del 70 % de los clientes queda insatisfecho. Llegar con mucha anticipación no mejora la satisfacción de forma importante (16,4 % con 14 o más días de anticipación frente a 20,1 % con 0 a 7).
- La serie mensual de entregas tarde y la de insatisfacción tienen una correlación de 0,73.
- Pedidos con varios vendedores: 60,5 % de insatisfechos. Despacho tardío del vendedor: 34,8 % frente a 20,4 %.

Sin embargo, **el 67,1 % de los insatisfechos recibió el pedido a tiempo**. En sus comentarios predominan quejas sobre el producto:

| Tipo de queja (palabras clave) | Insatisfechos con entrega a tiempo | Insatisfechos con retraso o sin entrega |
|---|---:|---:|
| Retraso o no recibido | 20,5 % | 55,4 % |
| Pedido incompleto | 12,7 % | 4,1 % |
| Producto diferente | 9,5 % | 2,1 % |
| Producto dañado | 8,1 % | 1,3 % |
| Calidad o falsificación | 7,4 % | 1,2 % |

**Hipótesis.** Un modelo con variables del pedido identificará la insatisfacción ligada a la entrega, pero no la ligada al producto, que solo aparece en el texto.

## 4. Intento 1: variables del pedido (cuaderno 02)

Trece variables numéricas del pedido, entrenamiento balanceado por submuestreo, cinco clasificadores y búsqueda de hiperparámetros con validación.

| Modelo | Hiperparámetro | F1 satisfecho | F1 insatisfecho |
|---|---|---:|---:|
| Decision Tree | `max_depth=5` | 0,870 | 0,510 |
| Random Forest | `n_estimators=200` | 0,832 | 0,496 |
| KNN | `n_neighbors=51` | 0,845 | 0,504 |
| Regresión logística | `C=0.1` | 0,829 | 0,495 |
| MLP | `hidden_layer_sizes=(10,)` | 0,830 | 0,499 |

Ningún modelo supera 0,7 en la clase insatisfecho. El ajuste de hiperparámetros no cambia la situación: todos quedan cerca de 0,5.

**Análisis del error.** *Recall* de la clase insatisfecho del mejor modelo según la entrega:

| Estado de la entrega | Insatisfechos en prueba | Detectados | Recall |
|---|---:|---:|---:|
| A tiempo | 3.003 | 663 | 22,1 % |
| Tarde | 986 | 920 | 93,3 % |
| No entregado | 536 | 532 | 99,3 % |

El modelo detecta casi todos los insatisfechos con retraso o sin entrega, pero solo el 22,1 % de los que recibieron a tiempo, que son dos tercios del total. Se confirma la hipótesis: la limitación está en la información disponible, no en los algoritmos.

## 5. Decisión

Como la causa de la insatisfacción en los pedidos entregados a tiempo aparece en el comentario y el 63,5 % de los insatisfechos deja uno, el segundo enfoque usa el texto de la reseña como variable explicativa. La pregunta pasa a ser si un comentario corresponde a un cliente insatisfecho, lo que sirve para priorizar la atención de reseñas negativas. Se mantienen los mismos modelos, la misma partición y el mismo criterio para que la comparación sea directa.

## 6. Intento 2: texto de la reseña (cuaderno 03)

40.775 pedidos con comentario, representados como bolsa de palabras binaria (3.219 palabras).

| Modelo | Hiperparámetro | F1 satisfecho | F1 insatisfecho |
|---|---|---:|---:|
| Decision Tree | `max_depth=40` | 0,890 | 0,784 |
| Random Forest | `n_estimators=200` | 0,918 | 0,851 |
| KNN | `n_neighbors=3` | 0,890 | 0,774 |
| Regresión logística | `C=1` | 0,921 | 0,850 |
| MLP | `hidden_layer_sizes=(100, 50)` | 0,918 | 0,855 |

Los cinco modelos superan 0,7 en ambas clases. El mejor es la red neuronal MLP con `hidden_layer_sizes=(100, 50)`, con F1 de 0,918 y 0,855.

| Estado de la entrega | Recall intento 1 | Recall intento 2 |
|---|---:|---:|
| A tiempo | 22,1 % | 83,8 % |
| Tarde | 93,3 % | 93,7 % |
| No entregado | 99,3 % | 95,1 % |

El modelo de texto recupera a los insatisfechos con entrega a tiempo, el grupo que el primer enfoque no detectaba.

## 7. Recomendaciones

1. Clasificar los comentarios al recibirlos y priorizar la atención de los señalados como insatisfechos.
2. Vigilar los pedidos en riesgo de retraso y avisar al cliente antes de la fecha estimada.
3. Reforzar la capacidad logística en noviembre y febrero-marzo.
4. Informar al cliente cuando el pedido tenga varios vendedores y llegue en envíos separados.
5. Hacer seguimiento a vendedores con despachos tardíos y a productos con quejas recurrentes.

## 8. Limitaciones

- Solo el 41,3 % de los clientes deja comentario; el modelo de texto no aplica a los demás.
- La bolsa de palabras no considera el orden ni la negación en contexto ("bueno, pero demoró").
- La búsqueda de palabras clave para clasificar quejas es aproximada.
- Los datos corresponden a Brasil entre 2016 y 2018.
