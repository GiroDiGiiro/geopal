from typing import Any, Dict, List, Tuple

from gep_sd.utils.get_db_info import get_db_info
from gep_sd.utils.get_valuemap_from_db import get_valuemap_from_db
from qgis.core import QgsFeature, QgsVectorLayer
from qgis.core.additions.edit import edit


def fill_codes(layer: QgsVectorLayer, code_field: str, type_field: str,
               prefixes: Dict[int, str]) -> None:
    """
    Remplit un champ code pour les features qui n'en ont pas encore, sous la forme PREFIXE + numéro.

    Le numéro est incrémental et indépendant pour chaque type. Les codes déjà remplis ne sont jamais modifiés.

    La couche doit être en mode édition avant l'appel (par exemple via `with edit(layer):`).
    Les modifications sont faites en mémoire ; le commit est à la charge de l'appelant.

    :param layer: couche vectorielle à modifier (doit être en édition)
    :param code_field: nom du champ à remplir (ex: "code", "code_ouvrage")
    :param type_field: nom du champ contenant l'id du type (ex: "regard_type_id")
    :param prefixes: dictionnaire {id_du_type: préfixe}, ex: {1: "REG", 2: "CH"}
    :return: None (la couche est modifiée en place)
    """
    # Position (index) du champ à remplir dans la table attributaire, requis par changeAttributeValue
    code_idx: int = layer.fields().indexOf(code_field)
    # On charge les features dans une liste pour pouvoir les parcourir
    features: List[QgsFeature] = list(layer.getFeatures())

    # ---------------------------------------------------------------------------------------------
    # 1. Plus grand numéro déjà utilisé, pour chaque type
    # ---------------------------------------------------------------------------------------------
    # Un compteur par type, initialisé à 0 : un type sans aucun code existant commencera donc à 1
    counters: Dict[int, int] = {type_id: 0 for type_id in prefixes}
    # Parcours de toutes les features de la couche
    for f in features:
        # Lecture du type et du code actuel de la feature (peuvent valoir NULL côté QGIS)
        type_id: Any
        code: Any
        type_id, code = f[type_field], f[code_field]
        # On ignore la feature si son type est NULL (pas un int) ou inconnu de la table des préfixes
        if not isinstance(type_id, int) or type_id not in prefixes:
            continue
        # On ne traite le code que s'il est du texte (donc pas NULL) et commence par le préfixe de son type
        if isinstance(code, str) and code.startswith(prefixes[type_id]):
            # On retire le préfixe pour ne garder que la partie qui devrait être numérique ("REG12" -> "12")
            suffix: str = code[len(prefixes[type_id]):]
            # On vérifie que le reste est bien composé uniquement de chiffres (évite un plantage de int())
            if suffix.isdigit():
                # On conserve le plus grand numéro rencontré pour ce type
                counters[type_id] = max(counters[type_id], int(suffix))

    # ---------------------------------------------------------------------------------------------
    # 2. Attribution des nouveaux codes
    # ---------------------------------------------------------------------------------------------
    # Deuxième parcours des features, cette fois pour écrire les codes manquants
    for f in features:
        # Même lecture du type et du code qu'à l'étape 1
        type_id, code = f[type_field], f[code_field]
        # Même garde-fou : pas de type valide, pas de code à générer
        if not isinstance(type_id, int) or type_id not in prefixes:
            continue
        # Si le code est du texte non vide (strip() retire les espaces), la feature a déjà un code : on la saute
        if isinstance(code, str) and code.strip():
            continue  # déjà un code
        # On passe au numéro suivant pour ce type
        counters[type_id] += 1
        # On écrit le nouveau code (ex: "REG" + 4 -> "REG4") dans la couche, en mémoire tant qu'elle est en édition
        layer.changeAttributeValue(f.id(), code_idx, f"{prefixes[type_id]}{counters[type_id]}")

        # print(f' feature: {f.id()}, index_field_code = {code_idx}, code = {code} -> {prefixes[type_id]}{counters[type_id]} résultat final : {f['code']}')

def generate_code(point_layer: QgsVectorLayer, line_layer: QgsVectorLayer, polygon_layer: QgsVectorLayer,
                  db_name: str, schema_name: str) -> Tuple[bool, str]:
    """
    Génère les codes uniques manquants sur les couches de points, de lignes et de polygones.

    1. Codes d'identification : préfixes lus en BD (tables de types), un compteur par type.
    2. Codes des exutoires ("EXU" + n°) : un seul compteur partagé par les 3 couches, attribué aux features
       dont "is_exutoire" est vrai et qui n'ont pas encore de "code_exutoire".

    Les 3 couches sont passées en édition, modifiées, puis enregistrées ensemble à la fin.
    En cas d'erreur, tout est annulé (rollback) sur les 3 couches.
    Si l'une des couches est déjà en édition, la fonction s'arrête sans rien modifier.

    :param point_layer: couche de points (code, code_ouvrage, code_equipement, code_exutoire)
    :param line_layer: couche de lignes (code, code_ouvrage, code_exutoire)
    :param polygon_layer: couche de polygones (code, code_exutoire)
    :param db_name: nom de la base, transmis à `get_db_info` pour obtenir les paramètres de connexion
    :param schema_name: nom du schéma Postgres contenant les tables de types
    :return: (True, message de succès) ou (False, message d'erreur)
    """
    # Les 3 couches dans une liste pour pouvoir les traiter en boucle quand le traitement est identique
    layers: List[QgsVectorLayer] = [point_layer, line_layer, polygon_layer]

    # Garde-fou : commitChanges() enregistrerait aussi les modifications en cours de l'utilisateur
    # (et rollBack() les perdrait en cas d'erreur). On préfère s'arrêter avec un message clair.
    already_editing: List[str] = [layer.name() for layer in layers if layer.isEditable()]
    if already_editing:
        return False, f"Couche(s) déjà en édition, enregistrez ou fermez l'édition d'abord : {', '.join(already_editing)}"

    db_info: Dict[str, str] = get_db_info(db_name)

    tables: List[str] = ["regard_type", "ouvrage_ponctuel_type", "equipement_type",
                         "reseau_type", "ouvrage_lineaire_type", "ouvrage_gestion_type"]
    vm: Dict[str, Dict[int, str]] = get_valuemap_from_db(db_info, schema_name, tables, "id", "code")

    # print(vm)
    try:
        # Passage des 3 couches en édition ; startEditing() renvoie False en cas d'échec (elle ne lève rien)
        for layer in layers:
            if not layer.startEditing():
                raise RuntimeError(f"Impossible de passer la couche '{layer.name()}' en édition")

        # -----------------------------------------------------------------------------------------
        # 1. Codes d'identification
        # -----------------------------------------------------------------------------------------
        fill_codes(point_layer, "code", "regard_type_id", vm["regard_type"])
        fill_codes(point_layer, "code_ouvrage", "ouvrage_ponctuel_type_id", vm["ouvrage_ponctuel_type"])
        fill_codes(point_layer, "code_equipement", "equipement_type_id", vm["equipement_type"])

        fill_codes(line_layer, "code", "reseau_type_id", vm["reseau_type"])
        fill_codes(line_layer, "code_ouvrage", "ouvrage_lineaire_type_id", vm["ouvrage_lineaire_type"])

        fill_codes(polygon_layer, "code", "ouvrage_gestion_type_id", vm["ouvrage_gestion_type"])

        # -----------------------------------------------------------------------------------------
        # 2. Codes des exutoires
        # -----------------------------------------------------------------------------------------
        # Plus grand numéro "EXU" déjà utilisé, toutes couches confondues
        max_exu: int = 0
        for layer in layers:
            for f in layer.getFeatures():
                code_exu: Any = f["code_exutoire"]
                # isinstance(str) écarte les NULL QGIS, sur lesquels .strip() / .startswith() planteraient
                if isinstance(code_exu, str) and code_exu.startswith("EXU") and code_exu[3:].isdigit():
                    max_exu = max(max_exu, int(code_exu[3:]))

        # Attribution des nouveaux codes, couche par couche
        for layer in layers:
            exu_idx: int = layer.fields().indexOf("code_exutoire")
            for f in layer.getFeatures():
                code_exu = f["code_exutoire"]
                # Un code non vide existe déjà : on n'y touche pas (sinon on renumérote à chaque lancement)
                already_coded: bool = isinstance(code_exu, str) and bool(code_exu.strip())
                # is_exutoire à NULL est considéré comme faux
                if f["is_exutoire"] and not already_coded:
                    max_exu += 1
                    # Écriture dans la couche : modifier f[...] ne modifierait que la copie locale
                    layer.changeAttributeValue(f.id(), exu_idx, f"EXU{max_exu}")

        # -----------------------------------------------------------------------------------------
        # 3. Enregistrement
        # -----------------------------------------------------------------------------------------
        # commitChanges() renvoie False en cas d'échec (elle ne lève rien) : on lève nous-mêmes l'erreur
        for layer in layers:
            if not layer.commitChanges():
                raise RuntimeError(f"Échec de l'enregistrement de '{layer.name()}' : {'; '.join(layer.commitErrors())}")

    except Exception as e:
        # Annulation sur les 3 couches (sans effet sur une couche déjà enregistrée ou pas en édition)
        for layer in layers:
            layer.rollBack()
        # On ajoute le type de l'exception : certaines (ex: AssertionError) ont un message vide
        return False, f"Erreur lors de la génération des codes : {type(e).__name__}: {e}"

    return True, "Codes générés"