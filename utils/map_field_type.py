from PyQt5.QtCore import QVariant


def map_field_type(attr_type: str) -> QVariant.Type:
    """
    Retourne le type QVariant correspondant à un type d'attribut donné.

    :param attr_type: Nom logique du type (ex: 'int', 'string', 'date', ...)
    :return: QVariant.Type
    """
    if not attr_type:
        return QVariant.String

    attr_type = attr_type.lower().strip()

    # 1. Essayer avec Qt directement
    qt_type = QVariant.nameToType(attr_type)
    if qt_type != QVariant.Invalid:
        return qt_type

    # 2. Fallback avec dictionnaire custom
    type_map = {
        # Numériques
        "int": QVariant.Int,
        "integer": QVariant.Int,
        "long": QVariant.LongLong,
        "bigint": QVariant.LongLong,
        "double": QVariant.Double,
        "float": QVariant.Double,

        # Chaînes
        "string": QVariant.String,
        "text": QVariant.String,
        "varchar": QVariant.String,
        "json": QVariant.String,

        # Booléens
        "bool": QVariant.Bool,
        "boolean": QVariant.Bool,

        # Dates & temps
        "date": QVariant.Date,
        "time": QVariant.Time,
        "datetime": QVariant.DateTime,

        # Données binaires
        "binary": QVariant.ByteArray,
        "blob": QVariant.ByteArray,
    }

    if attr_type in type_map:
        return type_map[attr_type]

    # 3. Dernier recours : string
    return QVariant.String
