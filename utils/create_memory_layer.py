from qgis.core import QgsWkbTypes, QgsVectorLayer, QgsProject

from .add_fields import add_fields
from .map_field_type import map_field_type


def create_memory_layer(layer_name: str,geometry_name: str|int, epsg: int, attributes: dict =None, load_to_project: bool = True) -> QgsVectorLayer | None:
    """
    Permet de créer une couche mémoire et de l'ajouter au projet
    :param layer_name: Nom de la couche à créer
    :param geometry_name: Nom du type de géométrie de la couche
    :param epsg: Epsg de la couche créer
    :param attributes: (optionnel) Permet d'ajouter des attributs à la couche avec un dictionnaire du type {'nom_attribut' : 'type_attribut'}
    :param load_to_project: (optionnel) False pour ne pas ajouter la couche au projet
    :return: La couche nouvellement créer
    """

    try:
        if isinstance(geometry_name, int):  # Si on passe un WkbType
            geom = QgsWkbTypes.displayString(geometry_name)
        elif isinstance(geometry_name, str):  # Si on passe déjà une chaîne
            geom = geometry_name
        else:
            msg = "geometry_name doit être un str (ex: 'Point') ou un WkbType (int)"
            print(msg)
            raise ValueError(msg)

        layer_def = f"{geom}?crs=epsg:{epsg}&field=fid:integer&index=yes"

        mem_layer = QgsVectorLayer(layer_def, layer_name, "memory")
        if not mem_layer.isValid():
            print(f"Impossible de créer la couche mémoire : {layer_def}")
            raise AttributeError

        if attributes:
            add_fields(mem_layer, attributes)

        # Charger dans le projet si demandé
        if load_to_project:
            QgsProject.instance().addMapLayer(mem_layer)

        return mem_layer
    except Exception as e:
        print(f'Exception occurred while creating the memory layer : {e}')
        raise e