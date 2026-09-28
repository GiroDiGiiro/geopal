from typing import Dict, Tuple

from gep_sd.utils.update_layer_attribute import update_layer_attributes
from qgis.core import QgsProject

def add_gestionnaire_to_entities(name_gestionnaire: str, name_gestionnaire_field:str, info : Dict[str,bool]) -> Tuple[bool,str] :
    for layer_id, selected_only in info.items():
        layer = QgsProject.instance().mapLayer(layer_id)
        if layer is None:
            return
        succes = update_layer_attributes(layer=layer, updates={name_gestionnaire_field:name_gestionnaire},selected_only=selected_only)
        if not succes:
            return False, f"Erreur lors de l'ajout du gestionnaire de la couche {layer.name()} (nom du champs : {name_gestionnaire_field})"
    return True,''