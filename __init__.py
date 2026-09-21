# -*- coding: utf-8 -*-

def classFactory(iface):
    from gep_sd.gep_plugin import GepSDPlugin
    return GepSDPlugin(iface)

