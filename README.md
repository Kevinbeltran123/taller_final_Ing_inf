# Clasificación de clientes insatisfechos en Olist

Taller final de Ingeniería de la Información. Se aplica clasificación supervisada al dataset público de Olist para identificar a los clientes insatisfechos (reseñas de 1 a 3 estrellas).

| Archivo | Contenido |
|---|---|
| `clasificacion_olist.ipynb` | Análisis completo: datos, analítica descriptiva, diagnóstica, predictiva y prescriptiva |
| `sustentacion.pptx` / `sustentacion.pdf` | Presentación |
| `requirements.txt` | Librerías usadas |

## Resultados

| Variables usadas | Mejor modelo | F1 satisfecho | F1 insatisfecho | ¿F1 > 0,7 en ambas? |
|---|---|---:|---:|---|
| Datos del pedido (13 variables) | Decision Tree, `max_depth=5` | 0,870 | 0,510 | No, ningún modelo |
| Texto de la reseña (bolsa de palabras) | MLP, `hidden_layer_sizes=(100, 50)` | 0,918 | 0,855 | Sí, los cinco modelos |

Con los datos del pedido el modelo detecta la insatisfacción causada por retrasos, pero no la causada por el producto: solo encuentra el 22 % de los insatisfechos que recibieron a tiempo, que son dos tercios del total. Esa información está en el comentario, por lo que el segundo intento usa el texto de la reseña. Con los mismos modelos y el mismo procedimiento, los cinco superan el umbral.

## Ejecución

1. Descargar el [dataset de Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) y descomprimir los CSV en una carpeta `dataset/` junto al notebook.
2. Instalar las librerías: `pip install -r requirements.txt`
3. Abrir y ejecutar `clasificacion_olist.ipynb`.
