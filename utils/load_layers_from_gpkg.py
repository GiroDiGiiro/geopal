from qgis.core import QgsVectorLayer, QgsProject
from typing import List


def load_layers_from_gpkg(source: str, layers:List[str], add_to_legend : bool = True) -> List[QgsVectorLayer] | None:
    """
    Charge une couche dans le projet qgis depuis un geopackage
    :param source: chemin d'accès du geopackage
    :param layers: Listes du nom des couches enregistrées dans le geopackage
    :param add_to_legend: affiché la couche dans la légende
    :return: le QgsVectorLayer ou none en cas d'échec
    """
    layer_list = []
    for layer_name in layers:
        print(f"[Info] Traitement de {layer_name}...")

        uri = f"{source}|layername={layer_name}"
        layer = QgsVectorLayer(uri, layer_name, "ogr")

        if not layer.isValid():
            print(f"[Error] Échec du chargement de {layer_name}")
            layer_list.append(None)
        else:
            if add_to_legend:
                QgsProject.instance().addMapLayer(layer, True)
                print(f"[OK] Couche {layer_name} ajoutée avec succès")
            else:
                QgsProject.instance().addMapLayer(layer,False)
                print(f"[OK] Couche {layer_name} ajoutée avec succès, non affichée dans la légende")
            layer_list.append(layer)

    if any(layer is None for layer in layer_list):
        return None
    return layer_list

