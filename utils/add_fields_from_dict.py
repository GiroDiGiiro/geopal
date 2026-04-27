from qgis.core import QgsField, QgsVectorLayer
from .map_field_type import map_field_type


def add_fields_from_dict(layer: QgsVectorLayer | str, fields_dict: dict, float_precision = 10) -> bool:
    """
    Ajoute une liste de champs à une couche QGIS à partir d'un dictionnaire.

    :param layer: La couche QGIS (QgsVectorLayer) ou chemin d'accès de la couche (str).
    :param fields_dict: Dictionnaire {nom_champ : type_champ} avec type_champ en str ('string', 'int', 'double', etc.).
    :param float_precision: Precision des champs de type float/double/reel (int).
    :return: True si les champs sont ajoutés, False sinon.
    """

    # Si le paramètre est un chemin d'accès, charger la couche
    if isinstance(layer, str):
        layer = QgsVectorLayer(layer, "Layer", "ogr")
        if not layer.isValid():
            raise ValueError("La couche spécifiée est invalide.")
            return False

    try:
        if not fields_dict:
            raise AttributeError("Erreur : Aucun champ à ajouter.")
            return False

        fields = []
        for name, type_str in fields_dict.items():
            if name in layer.fields():
                print(f'champ {name} déja existant dans {layer}')
                continue

            qvariant_type =  map_field_type(type_str.lower())
            if qvariant_type is None:
                raise ValueError(f"Erreur : Type '{type_str}' non reconnu pour le champ '{name}'.")
                return False

            fields.append(QgsField(name, qvariant_type))

        provider = layer.dataProvider()
        if not provider.addAttributes(fields):
            raise RuntimeError("Erreur : L'ajout des champs a échoué.")
            return False

        layer.updateFields()
        return True

    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'ajout des champs : {e}")
        return False