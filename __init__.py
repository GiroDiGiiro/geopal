# -*- coding: utf-8 -*-

def classFactory(iface):
    from geopal.geopal_plugin import GeoPalPlugin
    return GeoPalPlugin(iface)

