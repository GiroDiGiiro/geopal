"""Fonctions de post-traitement pour la fusion des données Canoë vers GEP.

Ce module fournit deux stratégies pour reporter les attributs d'une couche
réseau issue de Canoë (``canoe_layer``) sur une couche GEP (``gep_layer``),
et produire une couche de sortie fusionnée (``output_layer``) :

- :func:`post_canoe_to_gep_localisation` : appariement par intersection
  géométrique (spatial index), sans nécessiter d'identifiant commun.
- :func:`post_canoe_to_gep_field_id` : appariement par correspondance
  d'un champ identifiant entre les deux couches.

Dans les deux cas, les entités de ``canoe_layer`` sans correspondance
trouvée dans ``gep_layer`` sont collectées dans une couche mémoire
d'erreurs, afin de faciliter une vérification manuelle ultérieure.
"""

from typing import Dict, List

from geopal.utils.add_features import add_features
from geopal.utils.create_memory_layer import create_memory_layer
from qgis.core import (
    QgsSpatialIndex,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsVectorLayer,
    QgsFeatureRequest
)

# Champs de gep_layer à conserver tels quels dans la couche de sortie.
FIELDS_GEP_NAMES: List[str] = [
    'nom_bv',
    'nom_troncon',
    'commentaires',
    'gestionnaire',
    'commune',
    'date_creation',
    'source'
]

# Correspondance entre les noms de champs de canoe_layer (clé, nom d'origine)
# et le nom qu'ils doivent porter dans la couche de sortie (valeur, nouveau nom).
FIELDS_CANOE_RENAMING: Dict[str, str] = {
    "nom": "nom_troncon",
    "noeud amont": "noeud_amont",
    "noeud aval": "noeud_aval",
    "longueur": "longueur_ml",
    "cote amont": "fe_amont",
    "cote aval": "fe_aval",
    "pente": "pente_m/m",
    "rugosite": "rugosite",
    "conduite amont": "canalisation",
    "thematique_valeur": "mise_en_charge_%",
    "q_cap": "debit_capable_m3s",
    "cote_sol_a": "tn_amont",
    "cote_sol_a_1": "tn_aval",
}


def post_canoe_to_gep_localisation(canoe_layer: QgsVectorLayer, gep_layer: QgsVectorLayer,
                                   output_layer: QgsVectorLayer) -> str:
    """Fusionne les attributs de gep_layer sur canoe_layer par correspondance spatiale.

    Pour chaque entité de ``canoe_layer``, on cherche dans ``gep_layer`` la
    première entité dont la géométrie intersecte celle de l'entité Canoë
    (via un index spatial construit sur ``gep_layer``). Les attributs de
    ``gep_layer`` définis dans :data:`FIELDS_GEP_NAMES` sont alors reportés
    sur la nouvelle entité, en plus des attributs de ``canoe_layer``
    renommés selon :data:`FIELDS_CANOE_RENAMING`.

    Les entités de ``canoe_layer`` n'ayant trouvé aucune intersection sont
    ajoutées à une couche mémoire d'erreurs (créée uniquement si nécessaire).

    Args:
        canoe_layer: Couche réseau issue de Canoë (source des géométries
            et des attributs Canoë).
        gep_layer: Couche GEP servant de référence pour l'appariement
            spatial et l'apport des attributs GEP.
        output_layer: Couche de destination dans laquelle les nouvelles
            entités fusionnées sont ajoutées.

    Returns:
        Message récapitulatif indiquant le nombre de correspondances
        trouvées sur le nombre total d'entités Canoë analysées.
    """
    # ----------------------------------------------------------------------
    # 1. Récupération des champs des couches de base
    #    et construction du schéma de sortie
    # ----------------------------------------------------------------------
    fields_gep = gep_layer.fields()
    extracted_fields_gep = [f for f in fields_gep if f.name() in FIELDS_GEP_NAMES]

    fields_canoe = canoe_layer.fields()

    # extracted_fields_canoe : champs déjà renommés (schéma de new_feat)
    # canoe_field_name_map   : nouveau nom -> nom d'origine (pour relire
    #                          l'attribut sur feat_canoe, qui garde l'ancien nom)
    extracted_fields_canoe: List[QgsField] = []
    canoe_field_name_map: Dict[str, str] = {}

    for original_name, new_name in FIELDS_CANOE_RENAMING.items():
        idx = fields_canoe.indexOf(original_name)
        if idx == -1:
            # le champ attendu n'existe pas dans canoe_layer : on l'ignore
            continue
        field = QgsField(fields_canoe.field(idx))  # copie, pour ne pas modifier la couche source
        field.setName(new_name)
        extracted_fields_canoe.append(field)
        canoe_field_name_map[new_name] = original_name

    new_fields = QgsFields()
    for f in extracted_fields_canoe:
        new_fields.append(f)
    for f in extracted_fields_gep:
        new_fields.append(f)

    # ----------------------------------------------------------------------
    # 2. Chargement de gep_layer en mémoire + index spatial
    #    avec géométries stockées pour éviter tout accès répété à la couche
    # ----------------------------------------------------------------------
    features_gep = {f.id(): f for f in gep_layer.getFeatures()}

    index_gep = QgsSpatialIndex(
        gep_layer.getFeatures(),
        flags=QgsSpatialIndex.FlagStoreFeatureGeometries
    )

    # ----------------------------------------------------------------------
    # 3. Boucle principale : parcours de Canoe, test contre l'index de GEP
    # ----------------------------------------------------------------------
    new_features_list: List[QgsFeature] = []
    error_features_list: List[QgsFeature] = []

    nb_matches = 0
    nb_features_canoe = 0

    for feat_canoe in canoe_layer.getFeatures():
        new_feat = QgsFeature()
        new_feat.setFields(new_fields)
        new_feat.setGeometry(feat_canoe.geometry())

        for field in extracted_fields_canoe:
            original_name = canoe_field_name_map[field.name()]
            new_feat.setAttribute(field.name(), feat_canoe.attribute(original_name))

        nb_features_canoe += 1
        geom_canoe = feat_canoe.geometry()
        bbox = geom_canoe.boundingBox()

        # Pré-filtrage rapide via l'index spatial (candidats dont la bbox
        # intersecte celle de l'entité Canoë).
        candidats_ids = index_gep.intersects(bbox)

        error = True
        for fid_gep in candidats_ids:
            geom_gep = index_gep.geometry(fid_gep)  # géométrie déjà en mémoire

            # Test d'intersection réel (plus précis que le simple test de bbox).
            if geom_gep.intersects(geom_canoe):
                feat_gep = features_gep[fid_gep]

                for field in extracted_fields_gep:
                    new_feat.setAttribute(field.name(), feat_gep.attribute(field.name()))

                nb_matches += 1
                error = False
                break  # une seule correspondance retenue (la première trouvée)

        if error:
            error_features_list.append(feat_canoe)

        new_features_list.append(new_feat)

    if error_features_list:
        error_layer = create_memory_layer(
            layer_name='Error : Correspondance non trouvé entre couche réseau et post canoë',
            geometry_name='LineStringZ', epsg=3946)
        add_features(features=error_features_list, layer=error_layer, allow_missing_fields=True)

    add_features(features=new_features_list, layer=output_layer, allow_missing_fields=False)

    return f"Terminé : {nb_matches}/{nb_features_canoe} correspondances trouvées sur les entités de Canoë analysées."


def post_canoe_to_gep_field_id(canoe_layer: QgsVectorLayer, gep_layer: QgsVectorLayer, output_layer: QgsVectorLayer,
                               id_canoe_field_name: str, id_gep_field_name: str, geom_method: int = 1) -> str:
    """Fusionne les attributs de gep_layer sur canoe_layer par correspondance d'identifiant.

    Pour chaque entité de ``canoe_layer``, on recherche dans ``gep_layer``
    l'entité dont le champ ``id_gep_field_name`` correspond à la valeur du
    champ ``id_canoe_field_name`` de l'entité Canoë. Les attributs de
    ``gep_layer`` définis dans :data:`FIELDS_GEP_NAMES` sont alors reportés
    sur la nouvelle entité, en plus des attributs de ``canoe_layer``
    renommés selon :data:`FIELDS_CANOE_RENAMING`.

    Les entités de ``canoe_layer`` n'ayant trouvé aucune correspondance
    d'identifiant sont ajoutées à une couche mémoire d'erreurs (créée
    uniquement si nécessaire).

    Args:
        canoe_layer: Couche réseau issue de Canoë (source des géométries
            et des attributs Canoë).
        gep_layer: Couche GEP servant de référence pour l'appariement par
            identifiant et l'apport des attributs GEP.
        output_layer: Couche de destination dans laquelle les nouvelles
            entités fusionnées sont ajoutées.
        id_canoe_field_name: Nom du champ identifiant à lire sur
            ``canoe_layer``.
        id_gep_field_name: Nom du champ identifiant à comparer sur
            ``gep_layer``.
        geom_method: Origine de la géométrie de la nouvelle entité.
            ``1`` pour conserver la géométrie de ``canoe_layer``, ``2``
            pour reprendre celle de ``gep_layer``.

    Returns:
        Message récapitulatif indiquant le nombre de correspondances
        trouvées sur le nombre total d'entités Canoë analysées.
    """
    # ----------------------------------------------------------------------
    # 1. Récupération des champs des couches de base
    #    et construction du schéma de sortie
    # ----------------------------------------------------------------------
    fields_gep = gep_layer.fields()
    extracted_fields_gep = [f for f in fields_gep if f.name() in FIELDS_GEP_NAMES]

    fields_canoe = canoe_layer.fields()

    # extracted_fields_canoe : champs déjà renommés (schéma de new_feat)
    # canoe_field_name_map   : nouveau nom -> nom d'origine (pour relire
    #                          l'attribut sur feat_canoe, qui garde l'ancien nom)
    extracted_fields_canoe: List[QgsField] = []
    canoe_field_name_map: Dict[str, str] = {}

    for original_name, new_name in FIELDS_CANOE_RENAMING.items():
        idx = fields_canoe.indexOf(original_name)
        if idx == -1:
            # le champ attendu n'existe pas dans canoe_layer : on l'ignore
            continue
        field = QgsField(fields_canoe.field(idx))  # copie, pour ne pas modifier la couche source
        field.setName(new_name)
        extracted_fields_canoe.append(field)
        canoe_field_name_map[new_name] = original_name

    new_fields = QgsFields()
    for f in extracted_fields_canoe:
        new_fields.append(f)
    for f in extracted_fields_gep:
        new_fields.append(f)

    new_features_list: List[QgsFeature] = []
    error_features_list: List[QgsFeature] = []

    nb_matches = 0
    nb_features_canoe = 0

    for feat_canoe in canoe_layer.getFeatures():
        nb_features_canoe += 1
        new_feat = QgsFeature()
        new_feat.setFields(new_fields)

        if geom_method == 1:
            new_feat.setGeometry(feat_canoe.geometry())

        for field in extracted_fields_canoe:
            original_name = canoe_field_name_map[field.name()]
            new_feat.setAttribute(field.name(), feat_canoe.attribute(original_name))

        # Construction de l'expression d'attribut pour retrouver l'entité
        # GEP correspondante (les apostrophes de la valeur sont échappées
        # pour rester compatible avec la syntaxe d'expression QGIS).
        valeur = str(feat_canoe[id_canoe_field_name]).replace("'", "''")
        expr = f'"{id_gep_field_name}" = \'{valeur}\''
        it = gep_layer.getFeatures(expr)

        feat_gep = next(it, None)
        if feat_gep is None:
            # Aucune entité GEP ne correspond à l'identifiant Canoë.
            error_features_list.append(feat_canoe)
            continue

        for field in extracted_fields_gep:
            new_feat.setAttribute(field.name(), feat_gep.attribute(field.name()))

        if geom_method == 2:
            new_feat.setGeometry(feat_gep.geometry())

        new_features_list.append(new_feat)
        nb_matches += 1

    if error_features_list:
        error_layer = create_memory_layer(
            layer_name='Error : Correspondance non trouvé entre couche réseau et post canoë',
            geometry_name='LineStringZ', epsg=3946)
        add_features(features=error_features_list, layer=error_layer, allow_missing_fields=True)

    add_features(features=new_features_list, layer=output_layer, allow_missing_fields=False)

    return f"Terminé : {nb_matches}/{nb_features_canoe} correspondances trouvées sur les entités de Canoë analysées."