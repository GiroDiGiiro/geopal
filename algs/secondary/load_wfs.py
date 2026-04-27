from qgis.core import (
    QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsRectangle
)

# URIs des flux WFS — restrictToRequestBBOX='1' est essentiel :
# le serveur ne renvoie que les features dans l'emprise demandée
WFS_ROUTES_URI = (
    "pagingEnabled='default' "
    "preferCoordinatesForWfsT11='false' "
    "restrictToRequestBBOX='1' "
    "srsname='EPSG:2154' "
    "typename='BDTOPO_V3:troncon_de_route' "
    "url='https://data.geopf.fr/annexes/ressources/wfs/topographie.xml' "
    "version='auto'"
)

WFS_COMMUNES_URI = (
    "pageSize='5000' "
    "pagingEnabled='enabled' "
    "preferCoordinatesForWfsT11='false' "
    "restrictToRequestBBOX='1' "
    "srsname='EPSG:2154' "
    "typename='LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:commune' "
    "url='https://data.geopf.fr/annexes/ressources/wfs/administratif.xml' "
    "version='2.0.0'"
)


def _get_project_extent_in_crs(target_crs: QgsCoordinateReferenceSystem) -> QgsRectangle:
    """
    Retourne l'emprise du projet reprojetée dans le CRS cible.
    Utilisé pour limiter la requête WFS à la zone d'intérêt.
    """
    project = QgsProject.instance()
    project_crs = project.crs()
    extent = project.instance().mapCanvas()  # fallback ci-dessous

    # Récupération de l'emprise via les couches du projet
    layers = list(project.mapLayers().values())
    if not layers:
        raise RuntimeError("Aucune couche dans le projet — impossible de déterminer l'emprise.")

    combined_extent = None
    for layer in layers:
        # Reprojeter l'emprise de chaque couche en EPSG:2154
        transform = QgsCoordinateTransform(layer.crs(), target_crs, project)
        layer_extent = transform.transformBoundingBox(layer.extent())
        if combined_extent is None:
            combined_extent = layer_extent
        else:
            combined_extent.combineExtentWith(layer_extent)

    return combined_extent


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
    print(f"[OK] Couche WFS chargée (non affichée) : {layer_name} — {layer.featureCount()} entités")
    return layer


def load_wfs_routes(add_to_legend: bool = False) -> QgsVectorLayer | None:
    return load_wfs_layer(WFS_ROUTES_URI, "Routes", add_to_legend)


def load_wfs_communes(add_to_legend: bool = False) -> QgsVectorLayer | None:
    return load_wfs_layer(WFS_COMMUNES_URI, "Communes", add_to_legend)


def load_wfs_reference_layers(add_to_legend: bool = False) -> tuple[QgsVectorLayer | None, QgsVectorLayer | None]:
    """
    Charge Routes et Communes en une seule fois.
    :return: (routes_layer, communes_layer)
    """
    routes = load_wfs_routes(add_to_legend)
    communes = load_wfs_communes(add_to_legend)
    return routes, communes