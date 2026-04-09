import os

from PyQt5.QtWidgets import QApplication
from qgis.core import QgsVectorFileWriter, QgsProject


from .add_fields import add_fields


def export_layers_to_gpkg(layers: list, export_path: str) -> bool:
    """
    Exporte plusieurs couches dans un même fichier GeoPackage avec leur symbologie
    et les ajoute au projet QGIS.

    Args:
        layers (list): Liste des couches à exporter.
        export_path (str): Chemin vers le fichier GeoPackage.

    Returns:
        bool: True si l'export a réussi, False sinon.
    """
    try:
        transform_context = QgsProject.instance().transformContext()
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"

        for layer in layers:

            # --- Détection PK ---
            pk_indexes = layer.primaryKeyAttributes()
            print(f"PK détectée pour {layer.name()} : {pk_indexes}")

            if not pk_indexes:
                # Ajouter PK
                layer.startEditing()
                add_fields(layer, {'fid': 'int'})
                layer.updateFields()

                idx_fid = layer.fields().indexFromName("fid")
                updates = {feat.id(): {idx_fid: i + 1} for i, feat in enumerate(layer.getFeatures())}
                layer.dataProvider().changeAttributeValues(updates)
                layer.commitChanges()

                pk_field_name = "fid"
            else:
                # Récupération du nom du champ PK
                pk_field_name = layer.fields()[pk_indexes[0]].name()
                print(f"PK existante : {pk_field_name}")

            # Options d’export
            options.layerName = layer.name()
            options.layerOptions = [f"FID={pk_field_name}"]

            if os.path.exists(export_path):
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

            result = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, export_path, transform_context, options
            )

            if result[0] != QgsVectorFileWriter.NoError:
                raise RuntimeError(f"Erreur OGR : {result[1]}")

            QApplication.processEvents()

        return True

    except Exception as e:
        print(f"[Error] Export GPKG : {e}")
        return False

