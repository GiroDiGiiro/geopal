from qgis.core import (
    QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsRectangle
)



def load_wfs_layer(uri: str, layer_name: str, add_to_legend: bool = False) -> QgsVectorLayer | None:
    """
    Charge une couche WFS dans le projet sans l'afficher par défaut.
    Le paramètre restrictToRequestBBOX dans l'URI garantit que seules
    les features dans l'emprise courante sont téléchargées.

    :param uri: URI WFS complète
    :param layer_name: Nom affiché dans le projet
    :param add_to_legend: False = couche chargée en mémoire, non visible dans le panneau
    :return: QgsVectorLayer ou None
    """
    layer = QgsVectorLayer(uri, layer_name, "WFS")

    if not layer.isValid():
        print(f"[Error] Couche WFS invalide : {layer_name}")
        return None

    # addMapLayer(layer, False) = ajouté au registre mais PAS à la légende
    # Sans ça la couche n'existe pas pour le reste du code
    QgsProject.instance().addMapLayer(layer, add_to_legend)
    print(f"[OK] Couche WFS chargée ({'affiché'if add_to_legend else 'non affiché' }) : {layer_name} — {layer.featureCount()} entités")
    return layer
