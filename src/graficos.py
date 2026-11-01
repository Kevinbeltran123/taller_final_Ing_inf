"""Estilo común de las figuras."""

import matplotlib.pyplot as plt

AZUL = "#2a78d6"      # satisfecho
NARANJA = "#eb6834"   # insatisfecho
GRIS = "#7b848c"


def configurar_estilo():
    plt.rcParams.update({
        "figure.figsize": (8, 4),
        "figure.dpi": 110,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.alpha": 0.3,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "font.size": 10,
    })


def guardar(fig, nombre, carpeta="../reports/figuras"):
    fig.savefig(f"{carpeta}/{nombre}.png", dpi=160, bbox_inches="tight")
