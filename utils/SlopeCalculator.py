import math

from PyQt5.QtCore import QObject
from qgis.core import QgsPoint
from typing import Tuple

class SlopeCalculator(QObject):
    def __init__(self, p1: QgsPoint|Tuple[float,float,float], p2: QgsPoint|Tuple[float,float,float]):
        super().__init__()

        # Vérification des types
        if not ((isinstance(p1, QgsPoint) or
                 (isinstance(p1, tuple) and len(p1) == 3))):
            raise TypeError(f"p1 doit être un QgsPoint ou un tuple de 3 floats, reçu {type(p1)}")

        if not ((isinstance(p2, QgsPoint) or
                 (isinstance(p2, tuple) and len(p2) == 3))):
            raise TypeError(f"p2 doit être un QgsPoint ou un tuple de 3 floats, reçu {type(p2)}")

        # Extraction des coordonnées
        if isinstance(p1, QgsPoint):
            self.x1, self.y1, self.z1 = p1.x(), p1.y(), p1.z()
        else:  # tuple
            self.x1, self.y1, self.z1 = p1

        if isinstance(p2, QgsPoint):
            self.x2, self.y2, self.z2 = p2.x(), p2.y(), p2.z()
        else:  # tuple
            self.x2, self.y2, self.z2 = p2

    def dz(self):
        return self.z2 - self.z1

    def dh(self):
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        return math.hypot(dx, dy)  # distance horizontale

    def slope_percent(self):
        return (self.dz() / self.dh()) * 100

    def slope_degree(self):
        return math.degrees(math.atan(self.dz() / self.dh()))

    def slope_ratio(self):
        return self.dz() / self.dh()
