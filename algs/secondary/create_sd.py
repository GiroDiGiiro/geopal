import os
import shutil
from pathlib import Path
from typing import Tuple, Dict

import psycopg2
from gep_sd.utils.get_db_info import get_db_info
from gep_sd.utils.load_layers_from_gpkg import load_layers_from_gpkg
from gep_sd.utils.move_layers_to_group import move_layers_to_group
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsVectorLayer, QgsEditorWidgetSetup, QgsDataSourceUri, \
    QgsSnappingConfig, QgsTolerance, Qgis, QgsRasterLayer, QgsPointXY, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransform
from qgis.utils import iface

SCHEMA_NAME = 'gep_ref'
LAYERS_NAMES = ['regard', 'reseau', 'ouvrage_polygonal', 'surface_raccordee', 'sousbassin_versant', 'bassin_versant','diametre_par_materiau']
PLUGIN_PATH = Path(__file__).resolve().parent.parent.parent
GPKG_PATH = os.path.join(PLUGIN_PATH, 'ressources', 'gpkg', 'couches_projet.gpkg')
STYLE_DIRECTORY = os.path.join(PLUGIN_PATH, 'ressources', 'style')

REGARD_FIELD_VALUEMAP: Dict[str, str] = {
    'regard_type_id': 'regard_type',
    'regard_subtype_id': 'regard_subtype',
    'equipement_type_id': 'equipement_type',
    'ouvrage_ponctuel_type_id': 'ouvrage_ponctuel_type',
    'tampon_geometrie_id': 'tampon_geometrie',
    'tampon_nature_id': 'tampon_nature',
    'anomalie_type_id': 'anomalie_ponctuel_type',
}
RESEAU_FIELD_VALUEMAP: Dict[str, str] = {
    'reseau_type_id': 'reseau_type',
    'ouvrage_lineaire_type_id': 'ouvrage_lineaire_type',
    'forme_geometrique_id': 'forme_geometrique',
    'materiau_lineaire_id': 'materiau_lineaire',
    'anomalie_lineaire_type_id': 'anomalie_lineaire_type',
}
OUVRAGE_POLYGONAL_FIELD_VALUEMAP: Dict[str, str] = {
    'ouvrage_gestion_type_id': 'ouvrage_gestion_type',
    'equipement_polygonal_type_id': 'equipement_polygonal_type',
    'anomalie_polygonal_type_id': 'anomalie_polygonal_type',
}

SSBV_FIELD_VALUEMAP: Dict[str, str] = {
    'mode_gestion_id': 'mode_gestion',
    'urbanisation_id': 'urbanisation',
}


def _build_field_valuemaps(db_info: dict, field_valuemap: Dict[str, str]) -> Tuple[Dict[str, Dict[str, int]], str]:
    """Se connecte une seule fois et construit {champ: {libellé: id}} pour chaque table référencée."""
    field_valuemap_dict: Dict[str, Dict[str, int]] = {}
    conn = None
    try:
        conn = psycopg2.connect(
            host=db_info['host'],
            port=db_info['port'],
            database=db_info['database'],
            user=db_info['user'],
            password=db_info['password'],
        )
        cursor = conn.cursor()
        for field_name, table_name in field_valuemap.items():
            cursor.execute(f"SELECT id, nom FROM {SCHEMA_NAME}.{table_name};")
            field_valuemap_dict[field_name] = {nom_val: id_val for id_val, nom_val in cursor.fetchall()}
    except (Exception, psycopg2.Error) as error:
        return {}, f'{error}'
    finally:
        if conn:
            conn.close()

    return field_valuemap_dict, ""


def _apply_style_generic(
        db_info: dict,
        layer: QgsVectorLayer,
        style_filename: str,
        style_name: str,
        field_valuemap: Dict[str, str],
        error_label: str,
) -> Tuple[bool, str]:
    style_path = os.path.join(STYLE_DIRECTORY, style_filename)
    if not style_path:
        return False, f"style des {error_label} introuvable. path : {style_path}"

    if not layer.loadNamedStyle(style_path):
        return False, f"Erreur lors du chargement du style depuis {style_path}"

    #Accès au style courant du layer pour lui donner un nom
    style_manager = layer.styleManager()
    if not style_manager.addStyleFromLayer(f'{style_name}') :
        return False, f"Erreur lors du renommage du style depuis {style_path}"

    if not style_manager.setCurrentStyle(f'{style_name}'):
        return False, f" Erreur lors de la séléction du style : {style_name}"

    if not field_valuemap:
        return True, ""


    field_valuemap_dict, error = _build_field_valuemaps(db_info, field_valuemap)
    if error:
        return False, error

    print(field_valuemap_dict)

    # Appliqué les value maps aux champs
    for field_name, valuemap in field_valuemap_dict.items():
        idx = layer.fields().lookupField(field_name)
        if idx == -1:
            print(f"[Warning] Champ introuvable sur la couche : {field_name}")
            continue
        layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup('ValueMap', {'map': valuemap}))

    return True, ""


def apply_style_regard(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'regard_acquisition.qml','acquisition', REGARD_FIELD_VALUEMAP, 'regards')


def apply_style_reseau(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'reseau_acquisition.qml','acquisition', RESEAU_FIELD_VALUEMAP, 'reseau')


def apply_style_ouvrage_polygonal(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'ouvrage_polygonal_acquisition.qml','acquisition', OUVRAGE_POLYGONAL_FIELD_VALUEMAP,
                                'ouvrage polygonal')

def apply_style_surface_raccordee(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'surface_raccordee_traitement.qml','traitement', None,
                                'surface_raccordee')

def apply_style_sousbassin_versant(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'sousbassin_versant_traitement.qml','traitement', SSBV_FIELD_VALUEMAP,
                                'sousbassin_versant')

def apply_style_bassin_versant(db_info: dict, layer: QgsVectorLayer) -> Tuple[bool, str]:
    return _apply_style_generic(db_info, layer, 'bassin_versant_traitement.qml','traitement', None,
                                'bassin_versant')

def create_sd(project_name: str, project_path: str | Path, db_name: str) -> Tuple[bool, str]:
    QgsProject.instance().clear()
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(2154))

    # Copié le gpkg contenant les couches type du plugin vers le dossier de travail
    source = Path(GPKG_PATH)
    destination = os.path.join(project_path, 'data.gpkg')
    shutil.copy2(source, destination)

    # import des couches depuis le gpkg copié
    layers = load_layers_from_gpkg(destination, LAYERS_NAMES)

    if not layers:
        return False, "[Error] Erreur lors de l'import des couches créée en gpkg"

    # Tri des couches pour usage futur
    pt_layers = [layer for layer in layers if layer.geometryType() == 0]
    line_layers = [layer for layer in layers if layer.geometryType() == 1]
    polygon_layers = [layer for layer in layers if layer.geometryType() == 2]
    nogeom_layers = [layer for layer in layers if layer.geometryType() == 4]

    # Récupérer les infos de connection à la base de donné
    db_info = get_db_info(db_name)
    if not db_info:
        return False, f'Impossible de récupérer les info de la bd : {db_name}'

    # Appliqué le style des regards
    _, error = apply_style_regard(db_info, pt_layers[0])
    if error:
        return False, error

    _, error = apply_style_reseau(db_info, line_layers[0])
    if error:
        return False, error

    _, error = apply_style_ouvrage_polygonal(db_info, polygon_layers[0])
    if error:
        return False, error

    _, error = apply_style_surface_raccordee(db_info, polygon_layers[1])
    if error:
        return False, error

    _, error = apply_style_sousbassin_versant(db_info, polygon_layers[2])
    if error:
        return False, error

    _, error = apply_style_bassin_versant(db_info, polygon_layers[3])
    if error:
        return False, error

    # Importer GoogleSat
    # Créer l'URI pour le service XYZ
    uri = QgsDataSourceUri()
    uri.setParam('type', 'xyz')
    uri.setParam('url', 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}')
    uri.setParam('zmax', '18')
    uri.setParam('zmin', '0')

    # Créer et ajouter la couche
    layer = QgsRasterLayer(uri.encodedUri().data().decode(), 'GoogleSat', 'wms')

    if not layer.isValid():
        return False, f" Erreur lors de l'import de GoogleMaps uri : {uri}"
    QgsProject.instance().addMapLayer(layer)

    # Mettre les couches dnas des groupes pour plus de clarté
    move_layers_to_group(['regard', 'reseau', 'ouvrage_polygonal'], 'Acquisition', True)
    move_layers_to_group(['surface_raccordee','sousbassin_versant','bassin_versant',  ], 'Traitement', True)
    move_layers_to_group(['GoogleSat'], 'BaseMap', True)
    move_layers_to_group(['diametre_par_materiau'],'Table de Définition', True)

    # Mettre les options d'accrochage pour une bonne topologie
    my_snap_config = QgsSnappingConfig()
    my_snap_config.setEnabled(True)
    my_snap_config.setType(QgsSnappingConfig.VertexAndSegment)
    my_snap_config.setUnits(QgsTolerance.Pixels)
    my_snap_config.setTolerance(10)
    my_snap_config.setIntersectionSnapping(True)
    my_snap_config.setMode(Qgis.SnappingMode.AllLayers)

    # Appliquer la configuration de snapping au projet
    QgsProject.instance().setSnappingConfig(my_snap_config)

    # Centré sur l'unima
    canvas = iface.mapCanvas()

    src_crs = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS84
    dest_crs = canvas.mapSettings().destinationCrs()  # CRS du canvas

    transform = QgsCoordinateTransform(src_crs, dest_crs, QgsProject.instance())
    point = transform.transform(QgsPointXY(-1.0944229154, 46.1644068195))

    canvas.setCenter(point)
    canvas.zoomScale(1000000)

    # Sauvegarde du projet
    project_path = os.path.join(project_path, f"{project_name}.qgz")
    if not QgsProject.instance().write(project_path):
        msg = f"[Error] Impossible de sauvegarder le projet : {project_path}"
        return False, msg

    # Rafraichir le projet
    iface.addProject(project_path)

    return True, ''
