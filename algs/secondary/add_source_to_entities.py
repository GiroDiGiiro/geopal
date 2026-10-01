from typing import Dict, Tuple

from gep_sd.utils.update_layer_attribute import update_layer_attributes
from qgis.core import QgsProject

def add_source_to_entities(name_source: str, name_source_field:str, info : Dict[str,bool]) -> Tuple[bool,str] :
    for layer_id, selected_only in info.items():
        layer = QgsProject.instance().mapLayer(layer_id)
        if layer is None:
            return
        succes = update_layer_attributes(layer=layer, updates={name_source_field:name_source},selected_only=selected_only)
        if not succes:
            return False, f"Erreur lors de l'ajout du source de la couche {layer.name()} (nom du champs : {name_source_field})"
    return True,f'Source : {name_source}, ajouté avec succès'