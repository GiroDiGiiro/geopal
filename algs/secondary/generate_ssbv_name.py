from typing import Tuple

from qgis.core import QgsField, QgsVectorLayer
from gep_sd.utils.update_layer_attribute import update_layer_attributes

def generate_ssbv_name(ssbv_layer: QgsVectorLayer, regard_layer: QgsVectorLayer, regard_id_field: int,
                       nom_field: int, code_field: int) -> Tuple[bool,str]:

    # Dictionnaire {id: code} depuis la couche regard
    regard_dict = {}

    for f in regard_layer.getFeatures():

        identifiant = f.id()
        code = f[code_field]

        if identifiant is not None:
            regard_dict[identifiant] = code
    print(regard_dict)

    # Étape 2 : préparer les modifications
    updates = {}

    for f in ssbv_layer.getFeatures():
        fid = f.id()
        regard_id = f[regard_id_field]
        print(f"regard ; {f[regard_id_field]}")
        if regard_id not in regard_dict:
            continue

        valeur = regard_dict[regard_id]

        updates[fid] = {
            nom_field: valeur
        }

    # Étape 3 : appliquer les modifications
    if not updates:
        return False, "Aucun nom de SousBassin Versant à générer"
    print(updates)
    succes = update_layer_attributes(ssbv_layer, updates)
    if not succes:
        return False, f"Erreur lors de la mise à jour de {ssbv_layer.name()}"

    return True, "nom des Sous Bassin Versant générés"

