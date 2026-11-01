"""Clasificadores, búsqueda de hiperparámetros y evaluación."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier

SEMILLA = 42
UMBRAL_F1 = 0.7

# Hiperparámetro evaluado para cada modelo y valores de la búsqueda
REJILLA = {
    "Decision Tree": ("max_depth", [3, 5, 10, 20, 40, None]),
    "Random Forest": ("n_estimators", [10, 50, 100, 200]),
    "KNN": ("n_neighbors", [1, 3, 5, 11, 21, 51]),
    "Regresión logística": ("C", [0.01, 0.1, 1, 10]),
    "MLP": ("hidden_layer_sizes", [(10,), (50,), (100,), (100, 50)]),
}


def crear_modelos():
    return {
        "Decision Tree": DecisionTreeClassifier(random_state=SEMILLA),
        "Random Forest": RandomForestClassifier(random_state=SEMILLA, n_jobs=-1),
        "KNN": KNeighborsClassifier(),
        "Regresión logística": LogisticRegression(max_iter=2000),
        "MLP": MLPClassifier(random_state=SEMILLA, early_stopping=True),
    }


def submuestrear(X, y, semilla=SEMILLA):
    """Iguala las clases tomando al azar tantos ejemplos de la clase 0 como haya de la clase 1."""
    y = np.asarray(y)
    rng = np.random.RandomState(semilla)
    idx_1 = np.where(y == 1)[0]
    idx_0 = rng.choice(np.where(y == 0)[0], len(idx_1), replace=False)
    idx = np.concatenate([idx_0, idx_1])
    rng.shuffle(idx)
    X_sub = X.iloc[idx] if hasattr(X, "iloc") else X[idx]
    return X_sub, y[idx]


def entrenar_y_evaluar(modelo, X_ent, y_ent, X_eval, y_eval):
    modelo.fit(X_ent, y_ent)
    pred = modelo.predict(X_eval)
    return f1_score(y_eval, pred, average=None), confusion_matrix(y_eval, pred)


def comparar_modelos(X_ent, y_ent, X_prueba, y_prueba, balancear=False):
    """Entrena los cinco modelos con sus parámetros por defecto y reporta F1 por clase."""
    if balancear:
        X_ent, y_ent = submuestrear(X_ent, y_ent)
    filas, matrices = [], {}
    for nombre, modelo in crear_modelos().items():
        f1, cm = entrenar_y_evaluar(modelo, X_ent, y_ent, X_prueba, y_prueba)
        filas.append({"modelo": nombre, "f1_satisfecho": f1[0], "f1_insatisfecho": f1[1]})
        matrices[nombre] = cm
    return pd.DataFrame(filas).set_index("modelo").round(3), matrices


def buscar_hiperparametros(X_ent, y_ent, balancear=False, tam_validacion=0.2):
    """Prueba los valores de REJILLA sobre una partición de validación tomada del entrenamiento.

    El criterio de selección es el menor F1 entre las dos clases, ya que el objetivo
    es superar el umbral en ambas.
    """
    X_a, X_val, y_a, y_val = train_test_split(
        X_ent, y_ent, test_size=tam_validacion, random_state=SEMILLA, stratify=y_ent)
    if balancear:
        X_a, y_a = submuestrear(X_a, y_a)

    filas = []
    for nombre, (param, valores) in REJILLA.items():
        for valor in valores:
            modelo = crear_modelos()[nombre].set_params(**{param: valor})
            f1, _ = entrenar_y_evaluar(modelo, X_a, y_a, X_val, y_val)
            filas.append({"modelo": nombre, "parametro": param, "valor": str(valor),
                          "f1_satisfecho": f1[0], "f1_insatisfecho": f1[1], "f1_min": f1.min()})
    resultados = pd.DataFrame(filas)

    mejores = {}
    for nombre, (param, valores) in REJILLA.items():
        sub = resultados[resultados["modelo"] == nombre].reset_index(drop=True)
        mejores[nombre] = valores[int(sub["f1_min"].idxmax())]
    return resultados.round(3), mejores


def evaluar_finales(mejores, X_ent, y_ent, X_prueba, y_prueba, balancear=False):
    """Reentrena cada modelo con su mejor valor sobre todo el entrenamiento y lo evalúa en prueba."""
    if balancear:
        X_ent, y_ent = submuestrear(X_ent, y_ent)
    filas, matrices, modelos = [], {}, {}
    for nombre, valor in mejores.items():
        param = REJILLA[nombre][0]
        modelo = crear_modelos()[nombre].set_params(**{param: valor})
        f1, cm = entrenar_y_evaluar(modelo, X_ent, y_ent, X_prueba, y_prueba)
        filas.append({"modelo": nombre, "hiperparametro": f"{param}={valor}",
                      "f1_satisfecho": round(f1[0], 3), "f1_insatisfecho": round(f1[1], 3),
                      "supera_umbral": bool(f1.min() > UMBRAL_F1)})
        matrices[nombre], modelos[nombre] = cm, modelo
    return pd.DataFrame(filas).set_index("modelo"), matrices, modelos


def recall_por_grupo(y_real, y_pred, grupos):
    """Proporción de insatisfechos detectados dentro de cada grupo (p. ej., estado de entrega)."""
    d = pd.DataFrame({"real": np.asarray(y_real), "pred": np.asarray(y_pred), "grupo": np.asarray(grupos)})
    d = d[d["real"] == 1]
    return d.groupby("grupo").agg(insatisfechos=("real", "size"), detectados=("pred", "sum")) \
            .assign(recall=lambda x: (x["detectados"] / x["insatisfechos"]).round(3))
