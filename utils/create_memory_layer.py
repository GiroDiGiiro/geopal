from typing import Union, List
from qgis.core import (
    QgsWkbTypes,
    QgsVectorLayer,
    QgsProject,
    QgsField,
    QgsFields
)
from .add_fields import add_fields
from .add_fields_from_dict import add_fields_from_dict


def create_memory_layer(
    layer_name: str,
    geometry_name: Union[str, int],
    epsg: int,
    attributes: Union[dict, List[QgsField], QgsFields, None] = None,
    load_to_project: bool = True
) -> QgsVectorLayer:
    """
    Permet de créer une couche mémoire et de l'ajouter au projet
    :param layer_name: Nom de la couche à créer
    :param geometry_name: Nom du type de géométrie de la couche
    :param epsg: Epsg de la couche créer
    :param attributes: (optionnel) Permet d'ajouter des attributs à la couche avec un dictionnaire du type {'nom_attribut' : 'type_attribut'}
    :param load_to_project: (optionnel) False pour ne pas ajouter la couche au projet
    :return: La couche nouvellement créer
    """

    # --- Géométrie ---
    if isinstance(geometry_name, int):
        geom = QgsWkbTypes.displayString(geometry_name)
    elif isinstance(geometry_name, str):
        geom = geometry_name
    else:
        raise TypeError("geometry_name doit être str ou int (WkbType)")

    layer_def = f"{geom}?crs=epsg:{epsg}&index=yes"

    layer = QgsVectorLayer(layer_def, layer_name, "memory")
    if not layer.isValid():
        raise RuntimeError(f"Création couche échouée : {layer_def}")

    # --- Attributs ---
    if attributes:

        if isinstance(attributes, dict):
            add_fields_from_dict(layer, attributes)

        elif isinstance(attributes, QgsFields):
            add_fields(layer, list(attributes))

        elif isinstance(attributes, list):
            if any(not isinstance(attribute, QgsField) for attribute in attributes):
                raise ValueError("Tous les éléments doivent être des QgsField")
            add_fields(layer, attributes)
        else:
            raise ValueError(" 'attributes' ne peut être qu'un dictionnaire, un QgsFields, ou une liste de QgsField ")

        # Charger dans le projet si demandé
        if load_to_project:
            QgsProject.instance().addMapLayer(layer)

        return layer
