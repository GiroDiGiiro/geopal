from qgis.core import QgsVectorLayer,QgsFeature


def get_by_expression(layer: QgsVectorLayer | str, expression: str) -> list[QgsFeature]:
    """
    Sélectionne les entités basées sur une expression dans une couche QGIS.

    :param layer: La couche QGIS (QgsVectorLayer) ou chemin d'accès de la couche (str).
    :param expression: Expression de sélection (chaîne de caractères).
    :return: Liste des entités sélectionnées.
    """
    # Si le paramètre est un chemin d'accès, charger la couche
    if isinstance(layer, str):
        layer = QgsVectorLayer(layer, "Layer", "ogr")
        if not layer.isValid():
            print("La couche spécifiée est invalide.")
            return []

    # Vérifier si la couche est valide
    if not layer.isValid():
        print("La couche spécifiée est invalide.")
        return []

    try:
        # Appliquer la sélection par expression
        layer.selectByExpression(expression, QgsVectorLayer.SetSelection)

        # Récupérer et retourner les entités sélectionnées
        selected_features = [f for f in layer.selectedFeatures()]
        layer.removeSelection()
        return selected_features
    except Exception as e:
        print(f"Erreur lors de la sélection par expression : {e}")
        return []