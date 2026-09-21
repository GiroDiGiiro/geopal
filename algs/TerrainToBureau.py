import datetime
import os.path

from PyQt5.QtWidgets import QDialog, QMessageBox
from gep_sd.algs.secondary.calculate_slope import calculate_slope
from gep_sd.algs.secondary.get_and_verif_canalisation import get_and_verif_canalisation
from gep_sd.algs.secondary.load_wfs import load_wfs_reference_layers
from gep_sd.form.ui.terrain_to_bureau import Ui_Form
from gep_sd.utils.add_features import add_features
from gep_sd.utils.create_memory_layer import create_memory_layer
from gep_sd.utils.export_layers_to_gpkg import export_layers_to_gpkg
from gep_sd.utils.get_by_expression import get_by_expression
from gep_sd.utils.load_layers_from_gpkg import load_layers_from_gpkg
from gep_sd.algs.secondary.fill_code_insee import fill_code_insee
from gep_sd.algs.secondary.fill_nom_rue import fill_nom_rue
from gep_sd.utils.get_layers_extend import get_layers_extent
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsVectorLayer


class TerrainToBureau(QDialog, Ui_Form):

    def __init__(self, interface, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.interface = interface

        self.finish_ui()

        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)

    def finish_ui(self):
        self.cb_point.clear()
        self.cb_line.clear()
        self.cb_polygon.clear()

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 0:
                self.cb_point.addItem(layer.name(), layer.id())
            elif layer.geometryType() == 1:
                self.cb_line.addItem(layer.name(), layer.id())
            elif layer.geometryType() == 2:
                self.cb_polygon.addItem(layer.name(), layer.id())

    def _on_cancel(self):
        self.close()

    def _on_ok(self):
        t0 = datetime.datetime.now()
        print(f" start at {t0}")
        # ---------------------------------------------#
        # ------- Instanciation des variables --------#
        # ---------------------------------------------#

        project_path = QgsProject.instance().absolutePath()
        point_id = self.cb_point.currentData()
        line_id = self.cb_line.currentData()
        polygon_id = self.cb_polygon.currentData()

        if not point_id or not line_id or not polygon_id:
            QMessageBox.critical(self, "Error", "Il manque une couche.\nMerci d'utiliser un projet issus d'un Projet GEP QFieldCloud")
            return

        pt_layer_terrain = QgsProject.instance().mapLayer(point_id)
        line_layer_terrain = QgsProject.instance().mapLayer(line_id)
        polygon_layer_terrain = QgsProject.instance().mapLayer(polygon_id)

        # ---------------------------------------------#
        # ------- Création des dictionnaires des champs --------#
        # ---------------------------------------------#

        pts_dict = {
            'Avaloir': {
                'id': 'str',
                'famille': 'int',
                'classe_pre': 'int',
                'service': 'int',
                'photo': 'str',
                'type_reh': 'int',
                'date_reh': 'str',
                'entre_reh': 'str',
                'date_pos': 'str',
                'entre_pos': 'str',
                'prof_rad': 'float',
                'cote_rad': 'float',
                'cote_tamp': 'float',
                'observat': 'int',
                'observation_commentaire': 'str',
                'etat_depot': 'int',
                'etat_inf': 'int',
                'etat_gc': 'int',
                'type_prop': 'int',
                'mod_gest': 'int',
                'gest': 'str',
                'type_ava': 'int',
                'fonc': 'int',
                'decant': 'int',
                'type_tamp': 'int',
                'diam_int': 'int',
                'diam_gri': 'int',
                'mod_pass': 'int',
                'etat_reg': 'int',
                'acces': 'int',
                'diametre': 'int',
                'cote_voi': 'int',

                'code_insee': 'str',
                'rue': 'str',
                'n_ordre': 'str',
                'n_ordre2': 'str',
                'exutoire': 'str',
                'type_eau': 'int',
                'source': 'str',

            },
            'Regard': {
                'id': 'str',
                'famille': 'int',
                'classe_pre': 'int',
                'service': 'int',
                'photo': 'str',
                'type_reh': 'int',
                'date_reh': 'str',
                'entre_reh': 'str',
                'date_pos': 'str',
                'entre_pos': 'str',
                'prof_rad': 'float',
                'cote_rad': 'float',
                'cote_tamp': 'float',
                'observat': 'int',
                'observation_commentaire': 'str',
                'etat_depot': 'int',
                'etat_inf': 'int',
                'etat_gc': 'int',
                'type_prop': 'int',
                'mod_gest': 'int',
                'gest': 'str',
                'acces': 'int',
                'diametre': 'int',
                'cote_voi': 'int',
                'type_reg': 'int',
                'tampon': 'int',
                'mat_tamp': 'int',
                'tamp_ver': 'int',
                'cote_int_1': 'float',
                'cote_int_2': 'float',
                'exploita': 'str',
                'servitude': 'int',
                'type_mat': 'int',

                'code_insee': 'str',
                'rue': 'str',
                'n_ordre': 'str',
                'n_ordre2': 'str',
                'exutoire': 'str',
                'type_eau': 'int',
                'sandre': 'str',
                'zone_inon': 'int',
                'source': 'str',

            },
            'Noeud': {
                'id': 'str',
                'famille': 'int',
                'classe_pre': 'int',
                'service': 'int',
                'photo': 'str',
                'type_reh': 'int',
                'date_reh': 'str',
                'entre_reh': 'str',
                'date_pos': 'str',
                'entre_pos': 'str',
                'prof_rad': 'float',
                'cote_rad': 'float',
                'cote_tamp': 'float',
                'observat': 'int',
                'observation_commentaire': 'str',
                'etat_depot': 'int',
                'etat_inf': 'int',
                'etat_gc': 'int',
                'type_prop': 'int',
                'mod_gest': 'int',
                'gest': 'str',
                'acces': 'int',
                'diametre': 'int',
                'type_noe': 'int',
                'siphon_am': 'int',
                'siphon_av': 'int',
                'masse_eau': 'str',

                'code_insee': 'str',
                'rue': 'str',
                'n_ordre': 'str',
                'n_ordre2': 'str',
                'exutoire': 'str',
                'type_eau': 'int',
                'sandre': 'str',
                'source': 'str',
            },
            'Ouvrage': {
                'id': 'str',
                'famille': 'int',
                'classe_pre': 'int',
                'service': 'int',
                'photo': 'str',
                'type_reh': 'int',
                'date_reh': 'str',
                'entre_reh': 'str',
                'date_pos': 'str',
                'entre_pos': 'str',
                'prof_rad': 'float',
                'cote_rad': 'float',
                'cote_tamp': 'float',
                'observat': 'int',
                'observation_commentaire': 'str',
                'etat_depot': 'int',
                'etat_inf': 'int',
                'etat_gc': 'int',
                'type_prop': 'int',
                'mod_gest': 'int',
                'gest': 'str',

                'exploita': 'str',
                'type_ouv': 'int',
                'type_mat': 'int',
                'have_equipement': 'int',
                'teleg': 'int',
                'etat': 'int',
                'point_dev': 'int',
                'masse_eau': 'str',

                'code_insee': 'str',
                'rue': 'str',
                'n_ordre': 'str',
                'n_ordre2': 'str',
                'exutoire': 'str',
                'type_eau': 'int',
                'sandre': 'str',
                'rad_amt': 'float',
                'cote_sur': 'float',
                'secto': 'str',
                'volume': 'float',
                'nom': 'str',
                'zone_inon': 'int',
                'fiche_ouvr': 'str',
                'source': 'str',
                'equipement_id': 'str',
            },
            'Equipement': {
                'id': 'str',
                'famille': 'int',
                'classe_pre': 'int',
                'service': 'int',
                'photo': 'str',
                'type_reh': 'int',
                'date_reh': 'str',
                'entre_reh': 'str',
                'date_pos': 'str',
                'entre_pos': 'str',
                'observat': 'int',
                'type_prop': 'int',
                'mod_gest': 'int',
                'gest': 'str',
                'acces': 'int',
                'diametre': 'int',
                'type_eq_tr': 'int',
                'etat_ouv': 'int',
                'fabri': 'str',
                'modele': 'str',
                'num_serie': 'str',
                'tron_sup': 'str',

                'code_insee': 'str',
                'rue': 'str',
                'n_ordre': 'str',
                'n_ordre2': 'str',
                'exutoire': 'str',
                'zone_inon': 'int',
                'id_elt_res': 'str',
                'type_eau': 'int',
                'source': 'str',
            },
        }
        troncon_dict = {

            'id': 'str',
            'classe_pre': 'int',
            'date_pos': 'str',
            'entre_pos': 'str',
            'gest': 'str',
            'type_tro': 'int',
            'type_mat': 'int',
            'diam_nom': 'int',
            'com_dim': 'str',
            'forme': 'int',
            'cl_resist': 'int',
            'profondeur_fe_amont': 'int',
            'fil-eau_am': 'float',
            'profondeur_fe_aval': 'int',
            'fil-eau_av': 'float',
            'type_reh': 'int',
            'date_reh': 'str',
            'entre_reh': 'str',
            'mate_reh': 'int',
            'diam_reh': 'int',
            'long_ree': 'float',
            'racl': 'int',
            'domaine': 'int',
            'auto_pas': 'int',
            'visitabl': 'int',
            'exploita': 'str',
            'observat': 'str',
            'type_prop': 'int',
            'service': 'int',
            'mod_gest': 'int',

            'noeud_am': 'str',
            'noeud_av': 'str',
            'code_insee': 'str',
            'rue': 'str',
            'rue2': 'str',
            'n_ordre': 'str',
            'n_ordre2': 'str',
            'exutoire': 'str',
            'secto': 'str',
            'sandre': 'str',
            'type_eau': 'int',
            'long_cal': 'float',
            'pent_moy': 'float',
            'cont_pent': 'float',
            'radier_amont_id': 'str',
            'cot-r_am': 'float',
            'radier_aval_id': 'str',
            'cot-r_av': 'float',
            'lien_num': 'str',
            'source': 'str',

        }
        bassin_dict = {

            'id': 'str',
            'type_bassin': 'int',
            'revetement': 'int',
            'prof_fond': 'int',
            'fond_calcule': 'float',
            'photo': 'str',
            'famille': 'int',

            'code_insee': 'str',
            'rue': 'str',
            'n_ordre': 'str',
            'n_ordre2': 'str',
            'exutoire': 'str',
            'type_eau': 'int',
            'fonction': 'int',
            'fe_entr': 'float',
            'fe_sor': 'float',
            'surface': 'float',
            'volume': 'float',
            'source': 'str',

        }

        # ---------------------------------------------#
        # ------- Création des couches mémoires --------#
        # ------- Et insert des features triées --------#
        # ---------------------------------------------#

        layer_dict = {}
        n = 1
        for layer_name, attributes_dict in pts_dict.items():
            layer = create_memory_layer(layer_name, 'PointZ', 2154, attributes_dict, load_to_project=False)

            if n != 5:
                layer_dict[layer] = get_by_expression(pt_layer_terrain, f'"famille" = {n}')
            else:
                layer_dict[layer] = get_by_expression(pt_layer_terrain, f'"famille" = {n} or "have_equipement" = 1')
            n += 1

        layer = create_memory_layer('Canalisation', 'LineStringZ', 2154, troncon_dict, load_to_project=False)
        layer_dict[layer] = line_layer_terrain.getFeatures()

        layer = create_memory_layer('Bassin de Rétention', 'PolygonZ', 2154, bassin_dict, load_to_project=False)
        layer_dict[layer] = polygon_layer_terrain.getFeatures()

        for layer, features in layer_dict.items():
            succes = add_features(features, layer, True)
            if not succes:
                raise ValueError("Erreur lors de l'ajout des features aux couches temporaires")

        # ---------------------------------------------#
        # ------- Export vers couches sauvegarder localement en GPKG --------#
        # ---------------------------------------------#

        # Création du dossier d'export
        data_dir = os.path.join(project_path, '00_data')
        os.makedirs(data_dir, exist_ok=True)

        data_path = os.path.join(data_dir, 'data.gpkg')

        # Export des layers en gpkg
        succes = export_layers_to_gpkg(layer_dict.keys(), data_path)
        if not succes:
            print("[Error] Erreur lors de l'exports des couches mémoire en gpkg")
            return

        # ---------------------------------------------#
        # ------- création d'un projet Qgis vierge  --------#
        # ---------------------------------------------#

        QgsProject.instance().clear()
        QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(2154))

        # #supression des couches mémoires
        layers_name = [layer.name() for layer in layer_dict.keys()]
        # QgsProject.instance().removeMapLayers(layers_name)

        # Chargement des couches sauvegarder en gpkg
        reversedlist = reversed(list(layers_name))
        layers = load_layers_from_gpkg(data_path, reversedlist)
        if not layers:
            print("[Error] Erreur lors de l'import des couches créée en gpkg")
            return

        # Tri des couches pour usage futur
        pt_layers = [layer for layer in layers if layer.geometryType() == 0]
        line_layers = [layer for layer in layers if layer.geometryType() == 1]
        polygon_layers = [layer for layer in layers if layer.geometryType() == 2]

        # ---------------------------------------------#
        # ------- Ajout des Champs Automatique --------#
        # ---------------------------------------------#

        # print(layers_name) # ['Avaloir', 'Regard', 'Noeud', 'Ouvrage', 'Equipement', 'Canalisation', 'Bassin de Rétention']
        prefix_list = ['RET', 'CAN', 'EQU', 'OUV', 'NOE', 'REG', 'AVA']  # Inverser par apport à l'ordre des layers
        for i, layer in enumerate(layers):
            layer.startEditing()

            for feature in layer.getFeatures():
                # Création des ids personnalisés
                feature['id'] = f'{prefix_list[i]}{feature.id()}'
                # Ajout de la mention "eaux_pluviale"
                feature['type_eau'] = 2
                layer.updateFeature(feature)
            layer.commitChanges()

        # Spécificité pour la couche canalisation
        for layer in line_layers:
            layer.startEditing()
            for feat in layer.getFeatures():
                geom = feat.geometry()
                if geom is None or geom.isEmpty():
                    raise AttributeError('This feature need a geometry ')
                feat['long_cal'] = geom.length()
                layer.updateFeature(feat)
            layer.commitChanges()

            # Vérification topologique
            get_and_verif_canalisation(layer, pt_layers)

            # Calcul de la pente
            calculate_slope(layer)

        # Spécificité pour la couche Bassin de rétention

        for layer in polygon_layers:
            layer.startEditing()
            for feat in layer.getFeatures():
                geom = feat.geometry()
                depth = feat.attribute("fond_calcule")
                area = geom.area()
                feat["surface"] = area
                if depth:
                    feat["volume"] = depth * area
                layer.updateFeature(feat)
            layer.commitChanges()

        # Preparer les données pour remplir le code insee et le nom des rue (import + découpe)
        # Charger les référentiels WFS sans les afficher
        routes_layer, communes_layer = load_wfs_reference_layers(add_to_legend=False)
        if not routes_layer or not communes_layer:
            print("[Error] Impossible de charger les couches de référence WFS")
            return

        # Calauler l'extent total de toute les couches pour réduire le temps de traitement sur les couches importées
        extent = get_layers_extent(layers)

        # Remplir les champs spatiaux sur toutes les couches produites
        succes = fill_code_insee(layers, communes_layer)
        if succes:
            print('code insee ajouté avec succes')

        succes = fill_nom_rue(layers, routes_layer, extent)

        # ---------------------------------------------#
        # ------- Application du style pour la couche canalisation  --------#
        # ---------------------------------------------#

        for layer in line_layers:

            # Chargement du style
            style_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            style_path = os.path.join(style_path,'ressources', "style")
            style_path = os.path.join(style_path, "style_canalisation_bureau.qml")
            print(style_path)
            # Vérification si le fichier de style existe
            if os.path.exists(style_path):
                result = layer.loadNamedStyle(style_path)

                if not result:
                    print(f"❌ Erreur lors du chargement du style depuis {style_path}")
                    return False

                print(f"✅ Style chargé depuis {style_path}")
            else:
                print(f"Style {style_path} n'existe pas")
                return False

        t1 = datetime.datetime.now()
        time = t1 - t0
        print(f"End at {t1}")
        print(f"Completion in {time}")
        self.close()
