from qgis.core import QgsProviderRegistry, QgsApplication, QgsAuthMethodConfig


def get_db_info(nom_bd: str ) -> dict | None:
    """
    Récupère les infos stockées en clair dans Qgis d'une base de données depuis un nom

    :param nom_bd: La couche QGIS (QgsVectorLayer) ou chemin d'accès de la couche (str).
    :return: Un dictionnaire contenant l'host, le port, le nom de la base, l'username et le password ou None si la base n'est pas trouvée
    """
    host, port, dbname, username, password = None, None, None, None, None
    metadata = QgsProviderRegistry.instance().providerMetadata("postgres")

    try:

        if metadata.dbConnections()[nom_bd] :
            conn = metadata.dbConnections()[nom_bd]
            decoded_uri = metadata.decodeUri(conn.uri())

            if "host" in decoded_uri:
                host = decoded_uri["host"]

            if "port" in decoded_uri:
                port = decoded_uri["port"]
            if "dbname" in decoded_uri:
                dbname = decoded_uri["dbname"]
            if "authcfg" in decoded_uri:
                auth_id = decoded_uri["authcfg"]
                auth_manager = QgsApplication.authManager()
                auth_config = QgsAuthMethodConfig()
                auth_manager.loadAuthenticationConfig(auth_id, auth_config, True)
                username = decoded_uri["user"]
                password = decoded_uri["password"]
            else:
                if "username" in decoded_uri:
                    username = decoded_uri["username"].strip("'")
                if "password" in decoded_uri:
                    password = decoded_uri["password"].strip("'")

            resu = {'host' : host, 'port':port, 'database':dbname, 'user':username, 'password':password}

            return resu
        else:
            return None
    except Exception as e:
        print(f'Erreur dans la récupération des données de la base de données {nom_bd} : {e}')
        return None