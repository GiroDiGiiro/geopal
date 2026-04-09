from qgis.core import QgsSpatialIndex, QgsGeometry

def fill_code_insee(layers: list[QgsVectorLayer], communes_layer: QgsVectorLayer):
    """
    Remplit le champ code_insee de chaque feature par intersection avec la couche Communes.
    Utilise un index spatial pour minimiser les calculs.

    :param layers: Liste des layers sur lesquels faire la modifs
    :param communes_layer: Le layer contenant les communes au format AdminExpress
    :return: None
    """
    # Index spatial de la couches des communes
    spatial_index = QgsSpatialIndex(communes_layer.getFeatures())
    # Dictionnaire {feature_id: feature} pour accès rapide
    communes_by_id = {f.id(): f for f in communes_layer.getFeatures()}

    for layer in layers:
        layer.startEditing()
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue

            # 1. Candidats rapides via bounding box (index spatial)
            candidates_ids = spatial_index.intersects(geom.boundingBox())

            # 2. Test géométrique précis uniquement sur les candidats
            for cand_id in candidates_ids:
                commune_feat = communes_by_id[cand_id]
                if commune_feat.geometry().contains(geom):
                    feat['code_insee'] = commune_feat['insee_com']  # adapter le nom du champ
                    layer.updateFeature(feat)
                    break  # Une seule commune possible

        layer.commitChanges()