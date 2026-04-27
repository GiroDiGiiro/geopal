
from qgis.core import QgsPointXY, QgsVectorLayer, QgsSpatialIndex, QgsRectangle, QgsFeatureRequest,QgsFeature,QgsGeometry
from typing import List


def get_nom(point: QgsPointXY, features: List[QgsFeature]) -> str:
    f_by_distance = sorted(features, key=lambda f: f.geometry().distance(QgsGeometry.fromPointXY(point)))
    for f in f_by_distance:
        nom = f['nom_collaboratif_gauche']
        if nom :
            return nom.strip()
    return ''

def point_layer(layer, spatial_index, rue_by_id):
    layer.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            continue
        result_ids = spatial_index.nearestNeighbor(geom.asPoint(), 10)
        result_feats = [rue_by_id[result_id] for result_id in result_ids]
        feat['rue'] = get_nom(geom.asPoint(), result_feats)
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
        start_ids = spatial_index.nearestNeighbor(QgsPointXY(vertices[0].x(), vertices[0].y()), 10)
        end_ids = spatial_index.nearestNeighbor(QgsPointXY(vertices[-1].x(), vertices[-1].y()), 10)

        start_feats = [rue_by_id[result_id] for result_id in start_ids]
        end_feats = [rue_by_id[result_id] for result_id in end_ids]

        nom_start = get_nom(QgsPointXY(vertices[0].x(), vertices[0].y()), start_feats)
        nom_end = get_nom(QgsPointXY(vertices[-1].x(), vertices[-1].y()), end_feats)

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
        result_ids = spatial_index.nearestNeighbor(centroid.asPoint(), 10)
        result_feats = [rue_by_id[result_id] for result_id in result_ids]
        feat['rue'] = get_nom(centroid.asPoint(), result_feats)
        layer.updateFeature(feat)
    layer.commitChanges()


def fill_nom_rue(layers: list[QgsVectorLayer], rue_layer: QgsVectorLayer, extent: QgsRectangle = None) -> bool:
    """
    Implémente le nom des rues dans le champ 'rue' (et 'rue2' pour les linéaires).
    Point     → rue la plus proche du point
    LineString → rue du start point + rue du end point si différentes
    Polygon   → rue la plus proche du centroïde
    :param layers: List des Layers sur lesquels itérer
    :param rue_layer: Layer contenant le nom des rue au format
    :param extent: Emprise optionnel pour réduire l'itération sur les entitées
    :return: True si réussi, False sinon
    """
    try:
        request = QgsFeatureRequest()
        if extent:
            request.setFilterRect(extent)

        spatial_index = QgsSpatialIndex(rue_layer.getFeatures(request))
        rue_by_id = {f.id(): f for f in rue_layer.getFeatures(request)}

        for layer in layers:
            print(f"mise à jour de {layer.name()}")
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
