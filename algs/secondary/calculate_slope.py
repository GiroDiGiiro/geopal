from geopal.utils.SlopeCalculator import SlopeCalculator
from qgis.core import QgsVectorLayer


def calculate_slope(layer: QgsVectorLayer):
    layer.startEditing()
    for feat in layer.getFeatures():
        geom = feat.geometry()
        if geom is None or geom.isEmpty():
            raise AttributeError('This feature need a geometry ')
        line = geom.constGet()
        vertices = list(line.vertices())

        pente = SlopeCalculator(vertices[0], vertices[-1]).slope_percent()
        if pente :
            feat['pent_moy'] = pente
            if pente > 0:
                feat['cont_pent'] = True

        layer.updateFeature(feat)
    layer.commitChanges()
