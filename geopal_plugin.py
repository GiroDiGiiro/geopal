# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from geopal.algs.TerrainToBureau import TerrainToBureau
from geopal.form.ui import ressources_rc


# from 'PluginName'.form.ui import ressources_rc

class GeoPalPlugin:
    def __init__(self, iface):
        self.interface = iface

    def initGui(self):
        # Création des actions
        self.action1 = QAction(QIcon(":/img/img/icon.svg"), u"Tablette Vers Bureau", self.interface.mainWindow())
        self.action1.triggered.connect(self.on_click_action1)
        # Ajouter les autres actions ici

        # Création menu du plugin pour ouvrir les dialogs
        self.menu = QMenu(u"Unima - GeoPalPlugin")  # Ajouté Le nom du plugin
        self.menu.setIcon(QIcon(":/img/img/geopal_to_unima.svg"))
        self.menu.addAction(self.action1)
        # Ajouter les autres actions ou sous menu ici
        self.interface.pluginMenu().addMenu(self.menu)

        # Création toolbar du plugin pour ouvrir les dialogs
        self.toolbar = self.interface.addToolBar(u"GeoPalPlugin")  # Ajouté Le nom du plugin
        self.toolbar.setObjectName("Toolbar_GeoPalPlugin")  # Ajouté Le nom du plugin
        self.toolbar.addAction(self.action1)
        # Ajouter les autres actions ici

    def unload(self):
        self.interface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        self.interface.mainWindow().removeToolBar(self.toolbar)


    def on_click_action1(self):
        # dlg = UMainForm(self.interface) # Class à importer
        # dlg.show()
        # result = dlg.exec_()
        # if result:
        #     pass

        TerrainToBureau.run()
