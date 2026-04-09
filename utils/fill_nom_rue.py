from qgis.core import QgsFeature, QgsPointXY, QgsVectorLayer, QgsSpatialIndex


def fill_nom_rue(layers: list[QgsVectorLayer], rue_layer: QgsVectorLayer) -> bool:
    """
    Implémente le nom des rues dans le champ 'rue' (et 'rue2' pour les linéaires).
    Point     → rue la plus proche du point
    LineString → rue du start point + rue du end point si différentes
    Polygon   → rue la plus proche du centroïde
    :param layers: List des Layers sur lesquels itérer
    :param rue_layer: Layer contenant le nom des rue (généralement de type LineLayer)
    :return: True si réussi, False sinon
    """

    def get_nom(rue_feat) -> str:
        nom = rue_feat['nom_collaboratif_gauche']
        return nom.strip() if nom else ''

    def point_layer(layer, spatial_index, rue_by_id):
        layer.startEditing()
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            result_ids = spatial_index.nearestNeighbor(geom.asPoint(), 1)
            feat['rue'] = get_nom(rue_by_id[result_ids[0]])
            layer.updateFeature(feat)
        layer.commitChanges()

    def line_layer(layer, spatial_index, rue_by_id):
        layer.startEditing()
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            line = geom.constGet()
            vertices = list(line.vertices())
            if len(vertices) < 2:
                print(f"Feature {feat.id()} a moins de 2 vertices, ignorée")
                continue
            start_ids = spatial_index.nearestNeighbor(QgsPointXY(vertices[0].x(), vertices[0].y()), 1)
            end_ids = spatial_index.nearestNeighbor(QgsPointXY(vertices[-1].x(), vertices[-1].y()), 1)
            nom_start = get_nom(rue_by_id[start_ids[0]])
            nom_end = get_nom(rue_by_id[end_ids[0]])
            feat['rue'] = nom_start
            if nom_end and nom_end != nom_start:
                feat['rue2'] = nom_end
            layer.updateFeature(feat)
        layer.commitChanges()

    def polygon_layer(layer, spatial_index, rue_by_id):
        layer.startEditing()
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if geom is None or geom.isEmpty():
                continue
            centroid = geom.centroid()
            result_ids = spatial_index.nearestNeighbor(centroid.asPoint(), 1)
            feat['rue'] = get_nom(rue_by_id[result_ids[0]])
            layer.updateFeature(feat)
        layer.commitChanges()

    try:
        spatial_index = QgsSpatialIndex(rue_layer.getFeatures())
        rue_by_id = {f.id(): f for f in rue_layer.getFeatures()}

        for layer in layers:
            geom_type = layer.geometryType()
            if geom_type == 0:
                point_layer(layer, spatial_index, rue_by_id)
            elif geom_type == 1:
                line_layer(layer, spatial_index, rue_by_id)
            elif geom_type == 2:
                polygon_layer(layer, spatial_index, rue_by_id)
            else:
                raise RuntimeError(f'Type de géométrie non supporté : {geom_type}')

        return True

    except Exception as e:
        print(f"[Error] fill_nom_rue : {e}")
        return False