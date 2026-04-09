from qgis.core import QgsSpatialIndex, QgsVectorLayer, QgsRectangle

def point_layer(layer, spatial_index, communes_by_id):
    layer.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            continue

        results_id = spatial_index.intersects(geom.boundingBox())


        commune_feat = communes_by_id[results_id[0]]
        idx = feat.fieldNameIndex('code_insee')
        feat.setAttribute(idx, commune_feat['code_insee'])
        layer.updateFeature(feat)
    layer.commitChanges()

def line_layer(layer, spatial_index, communes_by_id):
    layer.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            continue

        candidates_ids = spatial_index.intersects(geom.boundingBox())
        if not candidates_ids:
            continue

        best_insee = None

        if len(candidates_ids) == 1:
            # Cas simple : un seul candidat
            best_insee = communes_by_id[candidates_ids[0]]['code_insee']

        else:
            # Cas multiple : commune avec le plus grand overlap
            best_length = 0.0
            for cand_id in candidates_ids:
                commune_geom = communes_by_id[cand_id].geometry()
                intersection = geom.intersection(commune_geom)
                if intersection.isEmpty():
                    continue
                length = intersection.length()
                if length > best_length:
                    best_length = length
                    best_insee = communes_by_id[cand_id]['code_insee']

        if best_insee:
            feat['code_insee'] = best_insee
            layer.updateFeature(feat)
    layer.commitChanges()
def polygon_layer(layer, spatial_index, communes_by_id):
    layer.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            continue

        candidates_ids = spatial_index.intersects(geom.boundingBox())
        if not candidates_ids:
            continue

        best_insee = None

        if len(candidates_ids) == 1:
            # Cas simple : un seul candidat
            best_insee = communes_by_id[candidates_ids[0]]['code_insee']

        else:
            # Cas multiple : commune avec le plus grand overlap
            best_area = 0.0
            for cand_id in candidates_ids:
                commune_geom = communes_by_id[cand_id].geometry()
                intersection = geom.intersection(commune_geom)
                if intersection.isEmpty():
                    continue
                area = intersection.area()
                if area > best_area:
                    best_area = area
                    best_insee = communes_by_id[cand_id]['code_insee']

        if best_insee:
            feat['code_insee'] = best_insee
            layer.updateFeature(feat)
    layer.commitChanges()

def fill_code_insee(layers: list[QgsVectorLayer], communes_layer: QgsVectorLayer, extent: QgsRectangle = None) -> bool:
    """
    Remplit le champ code_insee de chaque feature par intersection avec la couche Communes.
    Utilise un index spatial pour minimiser les calculs.

    :param layers: Liste des layers sur lesquels faire la modifs
    :param communes_layer: Le layer contenant les communes au format AdminExpress
        :param extent: Emprise optionnel pour réduire l'itération sur les entitées
    :return: None
    """
    try:
        # Index spatial de la couches des communes
        spatial_index = QgsSpatialIndex(communes_layer.getFeatures())
        # Dictionnaire {feature_id: feature} pour accès rapide
        communes_by_id = {f.id(): f for f in communes_layer.getFeatures()}

        for layer in layers:
            print(f"mise à jour de {layer.name()}")
            geom_type = layer.geometryType()
            if geom_type == 0:
                point_layer(layer, spatial_index, communes_by_id)
            elif geom_type == 1:
                line_layer(layer, spatial_index, communes_by_id)
            elif geom_type == 2:
                polygon_layer(layer, spatial_index, communes_by_id)
            else:
                raise RuntimeError(f'Type de géométrie non supporté : {geom_type}')

        return True

    except Exception as e:
        print(f"[Error] fill_code_insee : {e}")
        return False
