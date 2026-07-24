"""Boîte de dialogue QGIS pour le post-traitement Canoë -> GEP.

Ce module définit :class:`PostCanoeToGep`, la fenêtre permettant à
l'utilisateur de choisir une couche Canoë, une couche GEP et une couche
de sortie, puis de lancer l'une des deux méthodes de fusion définies dans
``geopal.algs.secondary.post_canoe_to_gep`` :

- par correspondance spatiale (``post_canoe_to_gep_localisation``) ;
- par correspondance d'un champ identifiant
  (``post_canoe_to_gep_field_id``), avec choix de la géométrie à conserver.
"""

from typing import Optional

from PyQt5.QtWidgets import QDialog, QMessageBox, QButtonGroup
from geopal.algs.secondary.post_canoe_to_gep import post_canoe_to_gep_localisation, post_canoe_to_gep_field_id
from geopal.form.ui.post_canoe import Ui_post_canoe_form_ui
from geopal.form.help_text.post_canoe_help_text import HELP_TEXT_POST_CANOE_TO_GEP
from qgis.core import QgsProject, QgsVectorLayer


class PostCanoeToGep(QDialog, Ui_post_canoe_form_ui):
    """Boîte de dialogue de configuration et de lancement de la fusion Canoë -> GEP."""

    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        """Initialise la boîte de dialogue et connecte l'interface.

        Args:
            interface: Interface QGIS (référence conservée pour un usage
                éventuel par la boîte de dialogue).
            parent: Widget parent Qt, le cas échéant.
        """
        super().__init__(parent)
        self.setupUi(self)
        self.interface = interface

        self.finish_ui()
        self.connect_signals()

        self.pb_ok.pressed.connect(self._on_ok)
        self.pb_cancel.pressed.connect(self._on_cancel)

    def finish_ui(self) -> None:
        """Termine la construction de l'UI : peuple les combobox et groupe les boutons radio."""
        self._populate_combo()

        group_method = QButtonGroup(self)
        group_method.addButton(self.rb_attribut)
        group_method.addButton(self.rb_localisation)

        geom_group = QButtonGroup(self)
        geom_group.addButton(self.rb_geom_canoe)
        geom_group.addButton(self.rb_geom_gep)

        self.textBrowser.setHtml(HELP_TEXT_POST_CANOE_TO_GEP)

    def connect_signals(self) -> None:
        """Connecte les signaux Qt des combobox et boutons radio à leurs slots."""

        self.cb_canoe_layer.currentIndexChanged.connect(self._controle_coherence)
        self.cb_gep_layer.currentIndexChanged.connect(self._controle_coherence)
        self.cb_output_layer.currentIndexChanged.connect(self._controle_coherence)

        self.rb_attribut.toggled.connect(self._rb_change)
        self.rb_localisation.toggled.connect(self._rb_change)

    def _populate_combo(self) -> None:
        """Peuple le combobox."""

        # avec les couches linéaires du projet
        self.cb_canoe_layer.clear()
        self.cb_gep_layer.clear()
        self.cb_output_layer.clear()
        line_layers = []

        for layer in QgsProject.instance().mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.geometryType() == 1:
                self.cb_canoe_layer.addItem(layer.name(), layer.id())
                self.cb_gep_layer.addItem(layer.name(), layer.id())
                self.cb_output_layer.addItem(layer.name(), layer.id())
                line_layers.append(layer)
        self._controle_coherence()

        if not line_layers:
            self.cb_canoe_layer.addItem("")
            self.cb_gep_layer.addItem("")

        # avec les champs des couches séléctionné
        self.cb_id_canoe.clear()
        self.cb_id_gep.clear()
        for field in QgsProject.instance().mapLayer(self.cb_canoe_layer.currentData()).fields():
            self.cb_id_canoe.addItem(field.name())
        for field in QgsProject.instance().mapLayer(self.cb_gep_layer.currentData()).fields():
            self.cb_id_gep.addItem(field.name())

    def _controle_coherence(self) -> None:
        """Vérifie que les couches Canoë, GEP et sortie sont bien distinctes.

        Désactive le bouton OK et affiche un message d'erreur si deux
        combobox pointent vers la même couche.
        """

        # --- Contrôle de cohérence ---
        canoe_layer = self.cb_canoe_layer.currentData()
        gep_layer = self.cb_gep_layer.currentData()
        output_layer = self.cb_output_layer.currentData()
        ids = [
            canoe_layer,
            gep_layer,
            output_layer,
        ]

        if len(set(ids)) != len(ids):

            self.pb_ok.setEnabled(False)
            self.error_label.setText("""
            <html><head/><body><p><span style=" font-style:italic; color:#f70000;">Merci de choisir des couches différentes</span></p></body></html>
            """)
        else:
            self.cb_canoe_layer.setStyleSheet("")
            self.cb_gep_layer.setStyleSheet("")
            self.pb_ok.setEnabled(True)
            self.error_label.setText('')

    def _rb_change(self) -> None:
        """Met à jour le message d'information selon la méthode de fusion choisie."""
        if self.rb_localisation.isChecked():
            self.frame_attr.hide()
        else:
            self.frame_attr.show()

    def _on_ok(self) -> None:
        """Lance le traitement de fusion sélectionné et affiche le résultat.

        Récupère les couches et paramètres choisis dans l'UI, appelle la
        fonction de fusion correspondante (par localisation ou par
        identifiant), puis affiche le message récapitulatif renvoyé avant
        de fermer la boîte de dialogue.
        """

        canoe_layer = QgsProject.instance().mapLayer(self.cb_canoe_layer.currentData())
        gep_layer = QgsProject.instance().mapLayer(self.cb_gep_layer.currentData())
        output_layer = QgsProject.instance().mapLayer(self.cb_output_layer.currentData())

        if self.rb_geom_canoe.isChecked():
            geom_method = 1
        elif self.rb_geom_gep.isChecked():
            geom_method = 2
        else:
            raise ValueError('geom_method non spécifié')

        if not canoe_layer or not gep_layer:
            print(f'canoe layer : {canoe_layer} \ngep layer : {gep_layer}')
            return

        if self.rb_attribut.isChecked():
            msg = post_canoe_to_gep_field_id(canoe_layer=canoe_layer, gep_layer=gep_layer, output_layer=output_layer,
                                             id_canoe_field_name=self.cb_id_canoe.currentText(),
                                             id_gep_field_name=self.cb_id_gep.currentText(), geom_method=geom_method)

        elif self.rb_localisation.isChecked():
            print('rb_localisation')
            msg = post_canoe_to_gep_localisation(canoe_layer=canoe_layer, gep_layer=gep_layer,
                                                 output_layer=output_layer)

        QMessageBox.information(self, "Info", msg)
        self.close()

    def _on_cancel(self) -> None:
        """Ferme la boîte de dialogue sans lancer de traitement."""
        self.close()