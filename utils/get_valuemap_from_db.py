from typing import Tuple, Dict, List
import psycopg2
from psycopg2 import sql

def get_valuemap_from_db(db_info: Dict[str, str], schema_name: str, tables_name: List[str], id_column_name: str,
                         value_column_name: str) -> Dict[str, Dict[int, str]] | None:
    """
    Fonction permettant de récupérer des valuemap depuis une base de donnée Postgres

    :param db_info: Dictionnaire sous la forme {'host' : host, 'port':port, 'database':dbname, 'user':username, 'password':password}
    :param schema_name: nom du schema de la bd
    :param tables_name: Liste du nom tables de la bd
    :param id_column_name: nom column clef
    :param value_column_name: nom column vlaue
    :return: Un dictionnaire sous la forme {nom_table : {key:value,...},nom_table : {key:value,...}}
    :raise: AttributeError en cas d'échec de la transaction
    """
    field_valuemap_dict: Dict[str, Dict[str, str]] = {}
    conn = None

    try :
        conn = psycopg2.connect(
            host=db_info['host'],
            port=db_info['port'],
            database=db_info['database'],
            user=db_info['user'],
            password=db_info['password']
        )
        cursor = conn.cursor()
        for table_name in tables_name:
            result_dict = {}
            query = sql.SQL("SELECT {id_col}, {val_col} FROM {schema}.{table}").format(
                id_col=sql.Identifier(id_column_name),
                val_col=sql.Identifier(value_column_name),
                schema=sql.Identifier(schema_name),
                table=sql.Identifier(table_name),
            )
            cursor.execute(query)
            field_valuemap_dict[table_name] = {id_val : nom_val for id_val, nom_val in cursor.fetchall()}

    except (Exception, psycopg2.Error) as error:
        raise AttributeError(f'Error while connecting to PostgreSQL: {error}')

    finally:
        if conn:
            conn.close()

    return field_valuemap_dict