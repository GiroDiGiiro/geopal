from typing import Optional, List
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes
from qgis.PyQt.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QMessageBox

from gep_sd.algs.secondary.get_and_verif_canalisation import get_and_verif_canalisation
from gep_sd.form.ui.get_and_verif_canalisation_form import Ui_get_and_verif_canalisation_form

class GetAndVerifCanalisation(QDialog,Ui_get_and_verif_canalisation_form):

    def __init__(self, interface, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.interface = interface

        self.layer: Optional[QgsVectorLayer] = None
        self.pt_layers: Optional[List[QgsVectorLayer]] = []

        self.finish_ui()

        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)

    def finish_ui(self):
        self._populate_combo()
        self._populate_list()

    def _populate_list(self):
        """Remplit la liste avec des items checkables"""
        layers = QgsProject.instance().mapLayers().values()

        for layer in layers:
            if not isinstance(layer, QgsVectorLayer):
                continue

            if layer.geometryType() == 0:  # Point
                item = QListWidgetItem(layer.name())
                item.setData(Qt.UserRole, layer)

                # Rend l'item checkable
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                if layer.name() in ('Avaloir','Regard','Noeud','Ouvrage','Equipement'):
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)



                self.listWidget.addItem(item)


    def _populate_combo(self):
        """Peuple le combobox avec les couches linéaires du projet."""
        self.cb_line_layer.clear()
        line_layers = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 1:
                self.cb_line_layer.addItem(layer.name(), layer.id())
                line_layers.append(layer)

        if not line_layers:
            self.cb_line_layer.addItem("")

    def _on_ok(self):
        pt_layers: list[QgsVectorLayer] = []

        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == Qt.Checked:
                layer = item.data(Qt.UserRole)
                pt_layers.append(layer)

        layer_id = self.cb_line_layer.currentData()
        if not layer_id:
            return

        line_layer: QgsVectorLayer = QgsProject.instance().mapLayer(layer_id)
        errors = get_and_verif_canalisation(line_layer, pt_layers)

        msg = f'{len(errors)} erreurs trouvées sur la couche {line_layer.name()}' if errors else 'Aucune erreur trouvée. Bravo !'
        QMessageBox.information(self, "Info", msg)
        self.close()

    def _on_cancel(self):
        self.close()




