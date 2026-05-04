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
        x1,y1 = vertices[0].x(), vertices[0].y()
        z1 = feat['fil-eau_am']
        x2,y2 = vertices[-1].x(), vertices[-1].y()
        z2 = feat['fil-eau_av']
        if not z1 or not z2:
            continue
        pente = SlopeCalculator((x1,y1,z1), (x2,y2,z2)).slope_percent()
        if pente :
            feat['pent_moy'] = pente
            if pente > 0:
                feat['cont_pent'] = True

        layer.updateFeature(feat)
    layer.commitChanges()

