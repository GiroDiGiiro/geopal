from qgis.core import QgsPoint, QgsVectorLayer, QgsFeature, QgsSpatialIndex, QgsGeometry
from typing import Tuple,List

def build_index(layer: QgsVectorLayer) -> Tuple[QgsSpatialIndex, dict]:
    """Construit l'index spatial une seule fois, à réutiliser en boucle."""
    spatial_index = QgsSpatialIndex(layer.getFeatures())
    features_by_id = {f.id(): f for f in layer.getFeatures()}
    return spatial_index, features_by_id


def get_qgis_feature_from_point(point: QgsPoint | Tuple[float, float, float],
                                 layer: QgsVectorLayer,
                                 spatial_index: QgsSpatialIndex = None,
                                 features_by_id: dict = None) -> QgsFeature | None:
    """
    Si spatial_index et features_by_id sont fournis, les réutilise.
    Sinon les construit à la volée.
    """
    if not (isinstance(point, QgsPoint) or
            (isinstance(point, tuple) and len(point) == 3)):
        raise TypeError(f"point doit être un QgsPoint ou un tuple (X,Y,Z), reçu {type(point)}")

    if isinstance(point, tuple):
        point = QgsPoint(point[0], point[1], point[2])

    if spatial_index is None or features_by_id is None:
        spatial_index, features_by_id = build_index(layer)

    point_geom = QgsGeometry(point.clone())
    candidates_ids = spatial_index.nearestNeighbor(point_geom.asPoint(), 1)

    for cand_id in candidates_ids:
        f = features_by_id[cand_id]
        if f.geometry().constGet() == point:
            return f

    return None

def build_indexes(layers: List[QgsVectorLayer]) -> List[Tuple[QgsVectorLayer, QgsSpatialIndex, dict]]:
    """Construit les index de tous les layers en une seule passe."""
    return [(layer, *build_index(layer)) for layer in layers]


def get_qgis_feature_from_point_in_layers(point: QgsPoint | Tuple[float, float, float],
                                           layers: List[QgsVectorLayer],
                                           indexes: List[Tuple] = None) -> Tuple[QgsFeature, QgsVectorLayer] | None:
    if indexes is None:
        indexes = build_indexes(layers)

    for layer, spatial_index, features_by_id in indexes:
        feat = get_qgis_feature_from_point(point, layer, spatial_index, features_by_id)
        if feat is not None:
            return feat, layer

    return None