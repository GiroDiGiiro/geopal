# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from geopal.algs.GetAndVerifCanalisastion import GetAndVerifCanalisation
from geopal.algs.TerrainToBureau import TerrainToBureau
from geopal.form.ui import ressources_rc


# from 'PluginName'.form.ui import ressources_rc

class GeoPalPlugin:
    def __init__(self, iface):
        self.interface = iface

    def initGui(self):
        # Création des actions
        self.terrain_to_bureau = QAction(QIcon(":/img/img/icon.svg"), u"Tablette Vers Bureau", self.interface.mainWindow())
        self.terrain_to_bureau.triggered.connect(self.on_click_terrain_to_bureau)
        self.get_and_verif_canalisation = QAction(QIcon(":/img/img/icon.svg"), u"Vérifier les canalisations", self.interface.mainWindow())
        self.get_and_verif_canalisation.triggered.connect(self.on_click_get_and_verif_canalisation)
        # Ajouter les autres actions ici

        # Création menu du plugin pour ouvrir les dialogs
        self.menu = QMenu(u"Unima - GeoPalPlugin")  # Ajouté Le nom du plugin
        self.menu.setIcon(QIcon(":/img/img/geopal_to_unima.svg"))
        self.menu.addAction(self.terrain_to_bureau)
        self.menu.addAction(self.get_and_verif_canalisation)
        # Ajouter les autres actions ou sous menu ici
        self.interface.pluginMenu().addMenu(self.menu)

        # Création toolbar du plugin pour ouvrir les dialogs
        self.toolbar = self.interface.addToolBar(u"GeoPalPlugin")  # Ajouté Le nom du plugin
        self.toolbar.setObjectName("Toolbar_GeoPalPlugin")  # Ajouté Le nom du plugin
        self.toolbar.addAction(self.terrain_to_bureau)
        # Ajouter les autres actions ici

    def unload(self):
        self.interface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        self.interface.mainWindow().removeToolBar(self.toolbar)


    def on_click_terrain_to_bureau(self):
        dlg = TerrainToBureau(self.interface) # Class à importer
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

        
    def on_click_get_and_verif_canalisation(self):
        dlg = GetAndVerifCanalisation(self.interface) # Class à importer
        dlg.show()
        result = dlg.exec_()
        if result:
            pass
