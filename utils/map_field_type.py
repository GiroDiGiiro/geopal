from PyQt5.QtCore import QVariant


def map_field_type(attr_type: str) -> QVariant.Type:
    """
    Retourne le type QVariant correspondant à un type d'attribut donné.

    :param attr_type: Nom logique du type (ex: 'int', 'string', 'date', ...)
    :return: QVariant.Type
    """
    if not attr_type:
        return 10

    attr_type = attr_type.lower().strip()

    # 1. Fallback avec dictionnaire custom
    type_map = {
        # Numériques
        "int": 2,  # int
        "integer": 2,  # int
        "long": 4,  # LongLong
        "bigint": 4,  # LongLong
        "double": 6,  # double
        "float": 6,  # double

        # Chaînes
        "string": 10,  # string
        "text": 10,  # string
        "varchar": 10,  # string
        "json": 10,  # string

        # Booléens
        "bool": 1,  # bool
        "boolean": 1,

        # Dates & temps
        "date": 14,  # date
        "time": 15,  # time
        "datetime": 16,  # datetime

        # Données binaires
        "binary": 12,  # QByteArray
        "blob": 12,  # QByteArray
    }

    if attr_type in type_map:
        return type_map[attr_type]

    # 2.  Essayer avec Qt directement

    qt_type = QVariant.nameToType(attr_type)
    if qt_type != QVariant.Invalid:
        return qt_type

    # 3. Dernier recours : string
    return 10
