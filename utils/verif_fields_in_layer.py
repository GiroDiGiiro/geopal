from qgis.core import QgsVectorLayer


def verif_field_in_layer(layer : QgsVectorLayer, fields : list[str]) -> list[str] | None:
    """
    Fonction retournant une liste de champs qui ne serait pas présents dans une couche
    :param layer: La couche à vérifier
    :param fields: liste des noms de champs à vérifier
    :return:
    """

    layer_fields = []
    for field in layer.fields():
        layer_fields.append(field.name())

    champs_manquants = [field for field in fields if field not in layer_fields]

    if len(champs_manquants) > 0:
        return champs_manquants
    else:
        return None