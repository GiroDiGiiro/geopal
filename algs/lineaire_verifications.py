from qgis.core import QgsVectorLayer, QgsExpression


def check_field_error(layer: QgsVectorLayer):
    if layer.fields().indexOf('error') == -1:
        raise AttributeError("La couche doit posséder un champ 'error'")


def check_vertices_number(layer: QgsVectorLayer, expression: QgsExpression = None) -> int:
    check_field_error(layer)

    nb_error = 0
    layer.startEditing()
    for f in layer.getFeatures(expression):
        line = f.geometry().constGet()
        error = 1 if len(line.vertices()) > 2 else None
        if error:
            if not f['error']:
                nb_error += 1
                f['error'] = error
        layer.updateFeature(f)
    layer.commitChanges()

    return nb_error


def check_topologie(layer: QgsLayer, expression: QgsExpression = None) -> int:
    check_field_error(layer)
    if layer.fields().indexOf('radier_amont_id') == -1 or layer.fields().indexOf('radier_aval_id') == -1:
        raise AttributeError("La couche doit posséder un champ 'radier_amont_id' et un champ 'radier_aval_id'")
    nb_error = 0
    layer.startEditing()
    for f in layer.getFeatures(expression):
        # Pas de topologie sur les deux extrémité de la canalisation
        if not f['radier_amont_id'] and not f['radier_aval_id']:
            if not f['error']:
                nb_error += 1
                f['error'] = 2
                layer.updateFeature(f)

        # Pas de topologie en amont de la canalisation
        elif not f['radier_amont_id']:
            if not f['error']:
                nb_error += 1
                f['error'] = 3
                layer.updateFeature(f)

        # Pas de topologie en aval de la canalisation
        elif not f['radier_aval_id']:
            if not f['error']:
                nb_error += 1
                f['error'] = 4
                layer.updateFeature(f)
    layer.commitChanges()
    return nb_error
