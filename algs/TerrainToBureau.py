import os.path

from qgis.core import QgsProject, QgsVectorLayer
from geopal.utils.create_memory_layer import create_memory_layer
from geopal.utils.get_by_expression import get_by_expression
from geopal.utils.add_features import add_features
from geopal.utils.export_layers_to_gpkg import export_layers_to_gpkg
from geopal.utils.load_layers_from_gpkg import load_layers_from_gpkg


class TerrainToBureau:



    def run():
        project_path = QgsProject.instance().absolutePath()
        pt_layer_terrain = QgsProject.instance().mapLayersByName("Ponctuels")[0]
        line_layer_terrain = QgsProject.instance().mapLayersByName("Linaires")[0]
        polygon_layer_terrain = QgsProject.instance().mapLayersByName("Polygones")[0]

        communes_layer = QgsProject.instance().mapLayersByName("Communes")[0]
        routes_layer = QgsProject.instance().mapLayersByName("Routes")[0]

        def create_custom_id(layer: QgsVectorLayer, prefix: str) -> bool:
            try:
                for i, f in enumerate(layer.getFeatures()):
                    f["id"] = f"{(prefix.upper())}{i}"
                layer.commitChanges()
                return True
            except Exception as e:
                print(e)
                return False

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
                'equipement_id':'str',
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
            'profondeur_fe_amont ': 'int',
            'fil-eau_am': 'float',
            'profondeur_fe_aval ':'int',
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

            'nœud_am': 'str',
            'nœud_av': 'str',
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
            'cot-r_am': 'float',
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

        layer_dict= {}
        n=1
        for layer_name,attributes_dict in pts_dict.items():
            layer = create_memory_layer(layer_name,'PointZ',2154, attributes_dict, load_to_project=False)

            old_features = get_by_expression(pt_layer_terrain, f'"famille" = {n}')
            layer_dict[layer] = get_by_expression(pt_layer_terrain, f'"famille" = {n}')
            n+=1

        layer = create_memory_layer('Canalisation','LineStringZ',2154, troncon_dict, load_to_project=False)
        layer_dict[layer] = line_layer_terrain.getFeatures()

        layer = create_memory_layer('Bassin de Rétention','PolygonZ',2154,bassin_dict, load_to_project=False)
        layer_dict[layer] = polygon_layer_terrain.getFeatures()

        for layer, features in layer_dict.items():
            succes = add_features(features, layer,True)
            if not succes:
                raise ValueError("Erreur lors de l'ajout des features aux couches temporaires")


        data_dir = os.path.join(project_path, '00_data')
        os.makedirs(data_dir, exist_ok=True)

        data_path = os.path.join(data_dir, 'data.gpkg')

        succes = export_layers_to_gpkg(layer_dict.keys(), data_path)
        if not succes:
            print("[Error] Erreur lors de l'exports des couches mémoire en gpkg")
            return

        layers_name = [layer.name() for layer in layer_dict.keys()]
        QgsProject.instance().removeMapLayers(layers_name)
        reversedlist = reversed(list(layers_name))
        layers = load_layers_from_gpkg(data_path, reversedlist)
        if not layers:
            print("[Error] Erreur lors de l'import des couches créée en gpkg")
            return

        # print(layers_name) # ['Avaloir', 'Regard', 'Noeud', 'Ouvrage', 'Equipement', 'Canalisation', 'Bassin de Rétention']
        prefix_list = ['AVA','REG','NOE','OUV','EQU','CAN','RET']
        for i, layer in enumerate(layers):
            # Création des ids personnalisés
            for feature in layer.getFeatures():
                feature['id'] = prefix_list[i]

                


