"""
Task QGIS qui, pour des couches point / ligne / polygone, déduit et écrit
le nom de rue (via un WFS de tronçons de route) et le code INSEE de la
commune (via un WFS de communes) sur chaque entité.
"""

from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import pyqtSignal
from qgis.core import (
    QgsProject,
    QgsTask,
    QgsVectorLayer,
    QgsFeature,
    QgsFeatureRequest,
    QgsRectangle,
    QgsSpatialIndex,
    QgsPointXY,
    QgsGeometry,
)

from gep_sd.utils.get_layers_extend import get_layers_extent
from gep_sd.utils.load_wfs import load_wfs_layer
from gep_sd.utils.update_layer_attribute import update_layer_attributes



class GetStreetAndTownTask(QgsTask):
    """
    Task QGIS (exécutée en arrière-plan) qui calcule, pour des couches
    point / ligne / polygone, le nom de rue le plus proche et le code
    INSEE de la commune d'appartenance, puis met à jour les attributs
    des couches en conséquence.

    Le traitement se déroule en deux temps :

    1. ``run()`` (thread secondaire) : charge les WFS, construit les
       dictionnaires de features et les index spatiaux, puis calcule
       les valeurs à écrire pour chaque couche. Aucune écriture sur les
       couches n'est faite ici (accès aux couches non thread-safe).
    2. ``finished()`` (thread principal) : applique les mises à jour
       calculées via ``update_layer_attributes``.

    Signals
    -------
    log(str, str)
        Émis pour journaliser un message. Premier argument : niveau
        (``"info"``, ``"warning"``, ``"error"``, ``"success"``, ``"debug"``).
        Second argument : message.
    progress(int)
        Émis avec une valeur de 0 à 100 représentant l'avancement de
        l'étape en cours (une même étape peut donc réémettre plusieurs
        fois une progression 0 → 100 : une fois par fonction de calcul).

    """

    log = pyqtSignal(str, str)
    progress = pyqtSignal(int)
    subprogress = pyqtSignal(int)

    def __init__(
        self,
        point_layer: QgsVectorLayer,
        line_layer: QgsVectorLayer,
        polygon_layer: QgsVectorLayer,
        field_name_rue: str,
        field_name_rue2: str,
        field_name_commune: str,
        url_rue: str,
        url_commune: str,
    ) -> None:
        """
        :param point_layer: Couche de points à enrichir.
        :param line_layer: Couche de lignes à enrichir.
        :param polygon_layer: Couche de polygones à enrichir.
        :param field_name_rue: Nom du champ où écrire la rue la plus proche.
        :param field_name_rue2: Nom du champ où écrire la seconde rue
            (extrémité de ligne uniquement, si différente de la première).
        :param field_name_commune: Nom du champ où écrire le code INSEE.
        :param url_rue: URL du service WFS des tronçons de route.
        :param url_commune: URL du service WFS des communes.
        """
        super().__init__("Recherche rue et commune", QgsTask.CanCancel)
        self.point_layer = point_layer
        self.line_layer = line_layer
        self.polygon_layer = polygon_layer
        self.field_name_rue = field_name_rue
        self.field_name_rue2 = field_name_rue2
        self.field_name_commune = field_name_commune
        self.url_rue = url_rue
        self.url_commune = url_commune

    # ---------- outils ----------
    def _emit_progress(self, current: int, total: int) -> None:
        """
        Émet ``progress`` avec un pourcentage entre 0 et 100.

        :param current: Nombre d'éléments déjà traités (1-indexé).
        :param total: Nombre total d'éléments à traiter.
        """
        if total <= 0:
            return
        self.progress.emit(int((current / total) * 100))

    def _emit_subprogress(self, current: int, total: int) -> None:
        """
        Émet ``progress`` avec un pourcentage entre 0 et 100.

        :param current: Nombre d'éléments déjà traités (1-indexé).
        :param total: Nombre total d'éléments à traiter.
        """
        if total <= 0:
            return
        self.subprogress.emit(int((current / total) * 100))

    # ---------- chargement ----------
    def load_wfs(self, uri: str, layer_name: str, add_to_legend: bool = False) -> Optional[QgsVectorLayer]:
        """
        Charge une couche WFS et journalise le résultat.

        :param uri: URI de connexion WFS.
        :param layer_name: Nom donné à la couche chargée.
        :param add_to_legend: Si ``True``, ajoute la couche à la légende.
        :return: La couche chargée, ou ``None`` en cas d'échec.
        """
        self.log.emit("info", f"Chargement de la couche wfs {layer_name}")
        layer = load_wfs_layer(uri, layer_name, add_to_legend)
        if layer is None:
            self.log.emit("error", f"Echec du chargement de la couche {layer_name}")
            return None
        self.log.emit(
            "success",
            f"Chargement de la couche wfs {layer_name} réussi "
            f"({'affichée' if add_to_legend else 'non affichée'})",
        )
        return layer

    # ---------- préparation des données ----------
    def build_features_dict(
        self, layer: QgsVectorLayer, extent: Optional[QgsRectangle] = None
    ) -> Optional[Dict[int, QgsFeature]]:
        """
        Construit un dictionnaire ``{fid: QgsFeature}`` pour une couche,
        en émettant la progression au fil des entités traitées.

        :param layer: Couche source.
        :param extent: Emprise optionnelle pour filtrer les entités.
        :return: Le dictionnaire des entités, ou ``None`` si vide/annulé.
        """
        self.log.emit("info", f"Construction du dictionnaire des features de {layer.name()}")
        request = QgsFeatureRequest()
        if extent:
            request.setFilterRect(extent)

        self.log.emit("info", f"Construction des features de {layer.name()}")

        features_list = list(layer.getFeatures(request))

        total = len(features_list)


        if total == 0:
            self.log.emit("error", f"Échec du dictionnaire des features de {layer.name()}")
            return None

        features: Dict[int, QgsFeature] = {}
        for i, feature in enumerate(features_list, start=1):
            if self.isCanceled():
                return None
            features[feature.id()] = feature
            self._emit_progress(i, total)

        self.log.emit("success", f"Dictionnaire des features de {layer.name()} construit")

        return features

    def build_spatial_index(
        self, layer: QgsVectorLayer, extent: Optional[QgsRectangle] = None
    ) -> Optional[QgsSpatialIndex]:
        """
        Construit un index spatial pour une couche, en émettant la
        progression au fil des entités indexées.

        :param layer: Couche source.
        :param extent: Emprise optionnelle pour filtrer les entités.
        :return: L'index spatial, ou ``None`` si vide/annulé.
        """
        self.log.emit("info", f"Création de l'index spatial de {layer.name()}")
        request = QgsFeatureRequest()
        if extent:
            request.setFilterRect(extent)

        features_list = list(layer.getFeatures(request))
        total = len(features_list)
        if total == 0:
            self.log.emit("error", f"Échec de la création de l'index spatial de {layer.name()}")
            return None

        spatial_index = QgsSpatialIndex()
        for i, feature in enumerate(features_list, start=1):
            if self.isCanceled():
                return None
            spatial_index.addFeature(feature)
            self._emit_progress(i, total)

        self.log.emit("success", f"Index spatial de {layer.name()} construit")
        return spatial_index

    # ---------- rues ----------
    def get_rue_name(self, point: QgsPointXY, features: List[QgsFeature]) -> str:
        """
        Retourne le nom de rue de l'entité de ``features`` la plus proche
        de ``point`` (champ ``nom_collaboratif_gauche``).

        :param point: Point de référence.
        :param features: Candidats (tronçons de route) parmi lesquels chercher.
        :return: Le nom de rue trouvé, ou ``""`` si aucun candidat valable.
        """
        f_by_distance = sorted(
            features, key=lambda f: f.geometry().distance(QgsGeometry.fromPointXY(point))
        )
        for f in f_by_distance:
            nom = f["nom_collaboratif_gauche"]
            if nom:
                return nom.strip()
        return ""

    def rue_point_layer(
        self,
        features_dict: Dict[int, QgsFeature],
        spatial_index: QgsSpatialIndex,
        rue_by_id: Dict[int, QgsFeature],
    ) -> Dict[int, Dict[str, str]]:
        """
        Calcule le nom de rue le plus proche pour chaque point.

        :param features_dict: Entités de la couche de points, par fid.
        :param spatial_index: Index spatial des tronçons de route.
        :param rue_by_id: Dictionnaire des tronçons de route, par fid.
        :return: ``{fid: {champ_rue: nom}}``.
        """
        result: Dict[int, Dict[str, str]] = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue
            result_ids = spatial_index.nearestNeighbor(geom.asPoint(), 10)
            result_feats = [rue_by_id[result_id] for result_id in result_ids]
            result[idx] = {self.field_name_rue: self.get_rue_name(geom.asPoint(), result_feats)}
            self._emit_progress(i, total)

        return result

    def rue_line_layer(
        self,
        features_dict: Dict[int, QgsFeature],
        spatial_index: QgsSpatialIndex,
        rue_by_id: Dict[int, QgsFeature],
    ) -> Dict[int, Dict[str, str]]:
        """
        Calcule le nom de rue à chaque extrémité de chaque ligne (second
        champ rempli uniquement si l'extrémité diffère du départ).

        :param features_dict: Entités de la couche de lignes, par fid.
        :param spatial_index: Index spatial des tronçons de route.
        :param rue_by_id: Dictionnaire des tronçons de route, par fid.
        :return: ``{fid: {champ_rue: nom, [champ_rue2: nom]}}``.
        """
        result: Dict[int, Dict[str, str]] = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue

            line = geom.constGet()
            vertices = list(line.vertices())
            if len(vertices) < 2:
                self.log.emit("warning", f"Feature {idx} a moins de 2 vertices, ignorée")
                self._emit_progress(i, total)
                continue

            start_point = QgsPointXY(vertices[0].x(), vertices[0].y())
            end_point = QgsPointXY(vertices[-1].x(), vertices[-1].y())

            start_ids = spatial_index.nearestNeighbor(start_point, 10)
            end_ids = spatial_index.nearestNeighbor(end_point, 10)

            start_feats = [rue_by_id[result_id] for result_id in start_ids]
            end_feats = [rue_by_id[result_id] for result_id in end_ids]

            nom_start = self.get_rue_name(start_point, start_feats)
            nom_end = self.get_rue_name(end_point, end_feats)

            result[idx] = {self.field_name_rue: nom_start}
            if nom_end and nom_end != nom_start:
                result[idx][self.field_name_rue2] = nom_end

            self._emit_progress(i, total)

        return result

    def rue_polygon_layer(
        self,
        features_dict: Dict[int, QgsFeature],
        spatial_index: QgsSpatialIndex,
        rue_by_id: Dict[int, QgsFeature],
    ) -> Dict[int, Dict[str, str]]:
        """
        Calcule le nom de rue le plus proche du centroïde de chaque polygone.

        :param features_dict: Entités de la couche de polygones, par fid.
        :param spatial_index: Index spatial des tronçons de route.
        :param rue_by_id: Dictionnaire des tronçons de route, par fid.
        :return: ``{fid: {champ_rue: nom}}``.
        """
        result: Dict[int, Dict[str, str]] = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue
            centroid = geom.centroid()
            result_ids = spatial_index.nearestNeighbor(centroid.asPoint(), 10)
            result_feats = [rue_by_id[result_id] for result_id in result_ids]
            result[idx] = {self.field_name_rue: self.get_rue_name(centroid.asPoint(), result_feats)}
            self._emit_progress(i, total)

        return result

    # ---------- communes ----------
    def commune_point_layer(
        self,
        features_dict: Dict[int, QgsFeature],
        spatial_index: QgsSpatialIndex,
        communes_by_id: Dict[int, QgsFeature],
    ) -> Dict[int, Dict[str, str]]:
        """
        Détermine la commune contenant chaque point.

        :param features_dict: Entités de la couche de points, par fid.
        :param spatial_index: Index spatial des communes.
        :param communes_by_id: Dictionnaire des communes, par fid.
        :return: ``{fid: {champ_commune: code_insee}}``.
        """
        result: Dict[int, Dict[str, str]] = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue

            candidates_ids = spatial_index.intersects(geom.boundingBox())
            if not candidates_ids:
                self.log.emit("warning", f"La feature {idx} n'intersecte aucune commune")
                self._emit_progress(i, total)
                continue

            # La bounding box ne suffit pas : on vérifie le confinement réel,
            # avec repli sur le premier candidat si aucun ne contient le point
            # (point exactement sur une frontière, imprécision numérique...).
            best_insee = None
            for cand_id in candidates_ids:
                commune_geom = communes_by_id[cand_id].geometry()
                if commune_geom.contains(geom):
                    best_insee = communes_by_id[cand_id]["code_insee"]
                    break
            if best_insee is None:
                best_insee = communes_by_id[candidates_ids[0]]["code_insee"]

            result[idx] = {self.field_name_commune: best_insee}
            self._emit_progress(i, total)

        return result

    def commune_line_layer(
        self,
        features_dict: Dict[int, QgsFeature],
        spatial_index: QgsSpatialIndex,
        communes_by_id: Dict[int, QgsFeature],
    ) -> Dict[int, Dict[str, str]]:
        """
        Détermine, pour chaque ligne, la commune avec laquelle elle
        partage la plus grande longueur d'intersection.

        :param features_dict: Entités de la couche de lignes, par fid.
        :param spatial_index: Index spatial des communes.
        :param communes_by_id: Dictionnaire des communes, par fid.
        :return: ``{fid: {champ_commune: code_insee}}``.
        """
        result: Dict[int, Dict[str, str]] = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue

            candidates_ids = spatial_index.intersects(geom.boundingBox())
            if not candidates_ids:
                self.log.emit("warning", f"La feature {idx} n'intersecte aucune commune")
                self._emit_progress(i, total)
                continue

            best_insee = None
            if len(candidates_ids) == 1:
                best_insee = communes_by_id[candidates_ids[0]]["code_insee"]
            else:
                best_length = 0.0
                for cand_id in candidates_ids:
                    commune_geom = communes_by_id[cand_id].geometry()
                    intersection = geom.intersection(commune_geom)
                    if intersection.isEmpty():
                        continue
                    length = intersection.length()
                    if length > best_length:
                        best_length = length
                        best_insee = communes_by_id[cand_id]["code_insee"]

            if best_insee:
                result[idx] = {self.field_name_commune: best_insee}

            self._emit_progress(i, total)

        return result

    def commune_polygon_layer(
        self,
        features_dict: Dict[int, QgsFeature],
        spatial_index: QgsSpatialIndex,
        communes_by_id: Dict[int, QgsFeature],
    ) -> Dict[int, Dict[str, str]]:
        """
        Détermine, pour chaque polygone, la commune avec laquelle il
        partage la plus grande surface d'intersection.

        :param features_dict: Entités de la couche de polygones, par fid.
        :param spatial_index: Index spatial des communes.
        :param communes_by_id: Dictionnaire des communes, par fid.
        :return: ``{fid: {champ_commune: code_insee}}``.
        """
        result: Dict[int, Dict[str, str]] = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue

            candidates_ids = spatial_index.intersects(geom.boundingBox())
            if not candidates_ids:
                self.log.emit("warning", f"La feature {idx} n'intersecte aucune commune")
                self._emit_progress(i, total)
                continue

            best_insee = None
            if len(candidates_ids) == 1:
                best_insee = communes_by_id[candidates_ids[0]]["code_insee"]
            else:
                best_area = 0.0
                for cand_id in candidates_ids:
                    commune_geom = communes_by_id[cand_id].geometry()
                    intersection = geom.intersection(commune_geom)
                    if intersection.isEmpty():
                        continue
                    area = intersection.area()
                    if area > best_area:
                        best_area = area
                        best_insee = communes_by_id[cand_id]["code_insee"]

            if best_insee:
                result[idx] = {self.field_name_commune: best_insee}

            self._emit_progress(i, total)

        return result

    # ---------- cycle de vie QgsTask ----------
    def run(self) -> bool:
        """
        Exécuté dans un thread secondaire par le gestionnaire de tâches
        QGIS : charge les WFS, construit les dictionnaires/index et
        calcule les mises à jour à appliquer. N'écrit rien sur les
        couches (voir :meth:`finished`).

        :return: ``True`` si les mises à jour ont été calculées avec
            succès, ``False`` en cas d'échec ou d'annulation.
        """
        self.result_commune_point: Dict[int, Dict[str, str]] = {}
        self.result_commune_line: Dict[int, Dict[str, str]] = {}
        self.result_commune_polygon: Dict[int, Dict[str, str]] = {}
        self.result_rue_point: Dict[int, Dict[str, str]] = {}
        self.result_rue_line: Dict[int, Dict[str, str]] = {}
        self.result_rue_polygon: Dict[int, Dict[str, str]] = {}
        uri_commune = (
            "pageSize='5000' "
            "pagingEnabled='enabled' "
            "preferCoordinatesForWfsT11='false' "
            "restrictToRequestBBOX='1' "
            "srsname='EPSG:2154' "
            "typename='LIMITES_ADMINISTRATIVES_EXPRESS.LATEST:commune' "
            f"url='{self.url_commune}' "
            "version='auto'"
        )
        uri_rue = (
            "pageSize='5000' "
            "pagingEnabled='enabled' "
            "preferCoordinatesForWfsT11='false' "
            "restrictToRequestBBOX='1' "
            "srsname='EPSG:2154' "
            "typename='BDTOPO_V3:troncon_de_route' "
            f"url='{self.url_rue}' "
            "version='auto'"
        )

        self.layer_commune = self.load_wfs(uri_commune, "commune", False)
        self._emit_subprogress(1,16)
        self.layer_rue = self.load_wfs(uri_rue, "rue", False)
        self._emit_subprogress(2, 16)
        if self.layer_commune is None or self.layer_rue is None:
            self.log.emit("error", "Impossible de charger les couches WFS, traitement annulé")
            return False

        point_features_dict = self.build_features_dict(self.point_layer)
        self._emit_subprogress(3, 16)
        line_features_dict = self.build_features_dict(self.line_layer)
        self._emit_subprogress(4, 16)
        polygon_features_dict = self.build_features_dict(self.polygon_layer)
        self._emit_subprogress(5, 16)
        if self.isCanceled():
            return False

        extent = get_layers_extent([self.point_layer, self.line_layer, self.polygon_layer])
        self._emit_subprogress(6, 16)

        commune_features_dict = self.build_features_dict(self.layer_commune, extent)
        self._emit_subprogress(7, 16)
        rue_features_dict = self.build_features_dict(self.layer_rue, extent)
        self._emit_subprogress(8, 16)
        if commune_features_dict is None or rue_features_dict is None:
            self.log.emit("error", "Aucune feature commune/rue dans l'emprise, traitement annulé")
            return False

        commune_spatial_index = self.build_spatial_index(self.layer_commune, extent)
        self._emit_subprogress(9, 16)
        rue_spatial_index = self.build_spatial_index(self.layer_rue, extent)
        self._emit_subprogress(10, 16)
        if commune_spatial_index is None or rue_spatial_index is None or self.isCanceled():
            return False

        self.result_commune_point = self.commune_point_layer(
            point_features_dict or {}, commune_spatial_index, commune_features_dict
        )
        self._emit_subprogress(11, 16)
        self.result_commune_line = self.commune_line_layer(
            line_features_dict or {}, commune_spatial_index, commune_features_dict
        )
        self._emit_subprogress(12, 16)
        self.result_commune_polygon = self.commune_polygon_layer(
            polygon_features_dict or {}, commune_spatial_index, commune_features_dict
        )
        self._emit_subprogress(13, 16)

        self.result_rue_point = self.rue_point_layer(point_features_dict or {}, rue_spatial_index, rue_features_dict)
        self._emit_subprogress(14, 16)
        self.result_rue_line = self.rue_line_layer(line_features_dict or {}, rue_spatial_index, rue_features_dict)
        self._emit_subprogress(15, 16)
        self.result_rue_polygon = self.rue_polygon_layer(
            polygon_features_dict or {}, rue_spatial_index, rue_features_dict
        )
        self._emit_subprogress(16, 16)

        return True

    def finished(self, result: bool) -> None:
        """
        Exécuté dans le thread principal une fois :meth:`run` terminé :
        applique les mises à jour calculées (stockées sur ``self`` par
        :meth:`run`) sur les couches concernées.

        :param result: Le booléen retourné par :meth:`run` (``True`` en
            cas de succès, ``False`` en cas d'échec/annulation).
        """
        if not result:
            self.log.emit("error", "Traitement échoué ou annulé, aucune mise à jour appliquée")
            return

        update_layer_attributes(self.point_layer, self.result_commune_point)
        update_layer_attributes(self.point_layer, self.result_rue_point)
        update_layer_attributes(self.line_layer, self.result_commune_line)
        update_layer_attributes(self.line_layer, self.result_rue_line)
        update_layer_attributes(self.polygon_layer, self.result_commune_polygon)
        update_layer_attributes(self.polygon_layer, self.result_rue_polygon)

        QgsProject.instance().removeMapLayers([self.layer_rue, self.layer_commune])


        self.log.emit("success", "Traitement terminé")
