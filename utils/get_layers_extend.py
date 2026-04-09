from typing import List
from qgis.core import QgsVectorLayer, QgsRectangle


def get_layers_extent(layers: List[QgsVectorLayer]) -> QgsRectangle:
    """
    Retourne l'emprise combinée de toutes les couches fournies.
    :param layers: Liste de QgsVectorLayer
    :return: QgsRectangle représentant l'emprise totale
    """
    combined = QgsRectangle()
    for layer in layers:
        extent = layer.extent()
        if not extent.isNull() and not extent.isEmpty():
            combined.combineExtentWith(extent)
    return combined