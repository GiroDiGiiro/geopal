from qgis.core import QgsField, QgsVectorLayer
from typing import List, Union


def add_fields(layer: Union[QgsVectorLayer,str], fields: List[QgsField]) -> bool:
    """
    Ajoute une liste de champs à une couche QGIS à partir d'un dictionnaire.

    :param layer: La couche QGIS (QgsVectorLayer) ou chemin d'accès de la couche (str).
    :param fields: Liste de QgsFields.
    :return: True si les champs sont ajoutés, False sinon.
    """

    # Si le paramètre est un chemin d'accès, charger la couche
    if isinstance(layer, str):
        layer = QgsVectorLayer(layer, "Layer", "ogr")
        if not layer.isValid():
            raise ValueError("Couche invalide")

    if not fields:
        raise ValueError("Aucun champ à ajouter")

    provider = layer.dataProvider()

    ok = provider.addAttributes(fields)
    if not ok:
        raise RuntimeError("Échec de l'ajout des champs")

    layer.updateFields()
    return True