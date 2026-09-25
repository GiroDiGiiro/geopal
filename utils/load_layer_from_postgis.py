from PyQt5.QtWidgets import QApplication
from qgis._core import QgsDataSourceUri, QgsVectorLayer, QgsProject

from gep_sd.utils.get_db_info import get_db_info


def load_layer_from_postgis(db_name: str,
                            schema_name: str,
                            table_name: str,
                            **kwargs) -> QgsVectorLayer | None:
    """
    Charger une couche Qgis dans un projet depuis une Base de Données avec identifiant écrites dans Qgis
    :param db_name: Nom de la base de données de connection
    :param schema_name: Nom du shema de la table
    :param table_name: Nom de la table
    :param kwargs: <br>
        - geometry (bool, default=True) : Indique si la table contient une géométrie <br>
        - query (str | None, default=None) : Requête SQL pour filtrer les entités à importer <br>
        - output_layer_name (str | None, default=None) : Nom de la couche en sortie <br>
        - geometry_column_name (str, default="geom") : Nom de la colonne géométrique <br>
        - add_to_legend (bool, default=True) : Indique si la couche doit être affichée dans la légende <br>)
    :return: QgsVectorLayer | None
    """
    geom = kwargs.get('geometry', True)
    query = kwargs.get('query', None)
    output_layer_name = kwargs.get('output_layer_name', None)
    geometry_column_name = kwargs.get('geometry_column_name', 'geom')
    add_to_legend = kwargs.get('add_to_legend', True)
    try:
        db_info = get_db_info(db_name)
        uri = QgsDataSourceUri()
        uri.setConnection(db_info['host'], str(db_info['port']), db_info['database'], db_info['user'],
                          db_info['password'])
        if geom:
            uri.setDataSource(schema_name, table_name, geometry_column_name)
        else:
            uri.setDataSource(schema_name, table_name, None)

        if query:
            uri.setSql(query)  # Utilisation de setSql pour spécifier la requête SQL

        if output_layer_name:
            la_couche_resultat = QgsVectorLayer(uri.uri(), output_layer_name, "postgres")
        else:
            la_couche_resultat = QgsVectorLayer(uri.uri(), table_name, "postgres")

        if la_couche_resultat.isValid():
            QgsProject.instance().addMapLayer(la_couche_resultat, add_to_legend)
            print(f'La table {table_name} ajoutée avec succès')
            QApplication.processEvents()
            return la_couche_resultat
        else:
            raise ValueError(f'Erreur: La table {table_name} n\'est pas valide')
            return None
    except Exception as e:
        raise ValueError(f'Erreur lors du chargement de la table {table_name} : {e}')
        return None
