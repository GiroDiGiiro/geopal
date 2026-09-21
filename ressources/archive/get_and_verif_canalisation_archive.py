from typing import List
from qgis.core import QgsPoint,QgsFeature, QgsVectorLayer
from gep_sd.utils.SlopeCalculator import SlopeCalculator
from gep_sd.utils.add_features import add_features
from gep_sd.utils.create_memory_layer import create_memory_layer
from gep_sd.utils.get_qgis_feature_from_point import get_qgis_feature_from_point_in_layers


def get_and_verif_canalisation(layer : QgsVectorLayer, pt_layers : List[QgsVectorLayer]):
    errors = []

    layer.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            raise AttributeError('This feature need a geometry ')
        line = geom.constGet()
        vertices = list(line.vertices())


        result = get_qgis_feature_from_point_in_layers(vertices[0], pt_layers)
        if result:
            feat['radier_amont_id'] = result[0].attribute('id')
            feat['noeud_am'] = result[0].attribute('id')
            feat['cot-r_am'] = result[0].geometry().constGet().z()
        else:
            errors.append(feat)

        result = get_qgis_feature_from_point_in_layers(vertices[-1], pt_layers)
        if result:
            feat['radier_aval_id'] = result[0].attribute('id')
            feat['noeud_av'] = result[0].attribute('id')
            feat['cot-r_av'] = result[0].geometry().constGet().z()
        else:
            if feat not in errors:
                errors.append(feat)

        if len(vertices) > 2 :
            if feat not in errors:
                errors.append(feat)

        layer.updateFeature(feat)
    layer.commitChanges()

    if errors:
        error_layer = create_memory_layer('errors_canalisation','LineStringZ',2154,feat.fields())
        add_features(errors, error_layer)

    return errors