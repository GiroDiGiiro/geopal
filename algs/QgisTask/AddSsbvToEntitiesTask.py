from typing import Dict, Optional

from PyQt5.QtCore import pyqtSignal
from gep_sd.utils.get_layers_extend import get_layers_extent
from gep_sd.utils.update_layer_attribute import update_layer_attributes
from qgis.core import (
    QgsTask,
    QgsVectorLayer,
    QgsRectangle,
    QgsFeature,
    QgsFeatureRequest,
    QgsSpatialIndex,
)

# Résultat d'attribution pour une couche : {fid_entité: {nom_champ_ssbv: fid_ssbv}}
LayerResult = Dict[int, Dict[str, int]]


class AddSsbvToEntitiesTask(QgsTask):
    """
    Tâche QGIS d'attribution d'un sousbassin versant (ssbv) à chaque entité des
    couches du projet (points, lignes ou polygones).

    Le calcul est fait dans ``run()`` (thread secondaire) ; l'écriture des
    attributs est différée à ``finished()`` (thread principal), seul endroit
    où la modification des couches est sûre.

    Signaux :
        log(niveau, message) : message de journal ("info", "success",
            "warning" ou "error").
        progress(pourcentage) : avancement de l'étape en cours (0-100).
        subprogress(pourcentage) : avancement global, couche par couche (0-100).
    """

    log = pyqtSignal(str, str)
    progress = pyqtSignal(int)
    subprogress = pyqtSignal(int)

    def __init__(
            self,
            ssbv_layer: QgsVectorLayer,
            field_name_ssbv: str,
            info: Dict[QgsVectorLayer, bool],
    ) -> None:
        """
        :param ssbv_layer: Couche de polygones des bassins versants.
        :param field_name_ssbv: Nom du champ à renseigner avec l'id du ssbv.
        :param info: Couches à traiter, avec pour chacune un booléen
            indiquant si seules les entités sélectionnées sont traitées.
        """
        super().__init__("Attribution des bassins versant aux entitées du projets", QgsTask.CanCancel)
        self.ssbv_layer: QgsVectorLayer = ssbv_layer
        self.field_name_ssbv: str = field_name_ssbv
        self.info: Dict[QgsVectorLayer, bool] = info
        # Résultats accumulés par run(), appliqués ensuite par finished()
        self.results: Dict[QgsVectorLayer, LayerResult] = {}

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
        Émet ``subprogress`` avec un pourcentage entre 0 et 100.

        :param current: Nombre d'éléments déjà traités (1-indexé).
        :param total: Nombre total d'éléments à traiter.
        """
        if total <= 0:
            return
        self.subprogress.emit(int((current / total) * 100))

    # ---------- préparation des données ----------
    def build_features_dict(
            self,
            layer: QgsVectorLayer,
            extent: Optional[QgsRectangle] = None,
            selected_only: bool = False,
    ) -> Optional[Dict[int, QgsFeature]]:
        """
        Construit un dictionnaire ``{fid: QgsFeature}`` pour une couche,
        en émettant la progression au fil des entités traitées.

        :param layer: Couche source.
        :param extent: Emprise optionnelle pour filtrer les entités.
        :param selected_only: Ne récupérer que les entités sélectionnées.
        :return: Le dictionnaire des entités, ou ``None`` si vide/annulé.
        """

        # Requête filtrée sur l'emprise si elle est fournie
        request = QgsFeatureRequest()
        if extent:
            request.setFilterRect(extent)

        # Lecture complète en liste pour connaître le total (progression)
        if selected_only:
            features_list = list(layer.getSelectedFeatures(request))
        else:
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


        return features

    def build_spatial_index(
            self,
            layer: QgsVectorLayer,
            extent: Optional[QgsRectangle] = None,
    ) -> Optional[QgsSpatialIndex]:
        """
        Construit un index spatial pour une couche, en émettant la
        progression au fil des entités indexées.

        :param layer: Couche source.
        :param extent: Emprise optionnelle pour filtrer les entités.
        :return: L'index spatial, ou ``None`` si vide/annulé.
        """
        self.log.emit("info", f"Création de l'index spatial de {layer.name()}")

        # Requête filtrée sur l'emprise si elle est fournie
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

    # ---------- intersection ----------
    def ssbv_point_layer(
            self,
            features_dict: Dict[int, QgsFeature],
            spatial_index: QgsSpatialIndex,
            ssbvs_by_id: Dict[int, QgsFeature],
    ) -> LayerResult:
        """
        Détermine la ssbv contenant chaque point.

        :param features_dict: Entités de la couche de points, par fid.
        :param spatial_index: Index spatial des ssbvs.
        :param ssbvs_by_id: Dictionnaire des ssbvs, par fid.
        :return: ``{fid: {champ_ssbv: id}}``.
        """
        result: LayerResult = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result

            # Entité sans géométrie : ignorée
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue

            # Présélection rapide des ssbvs par bounding box
            candidates_ids = spatial_index.intersects(geom.boundingBox())
            if not candidates_ids:
                self.log.emit("warning", f"La feature {idx} n'intersecte aucune ssbv")
                self._emit_progress(i, total)
                continue

            # La bounding box ne suffit pas : on vérifie le confinement réel,
            # avec repli sur le premier candidat si aucun ne contient le point
            # (point exactement sur une frontière, imprécision numérique...).
            best_ssbv: Optional[int] = None
            for cand_id in candidates_ids:
                ssbv_geom = ssbvs_by_id[cand_id].geometry()
                if ssbv_geom.contains(geom):
                    best_ssbv = ssbvs_by_id[cand_id].id()
                    break
            if best_ssbv is None:
                continue

            result[idx] = {self.field_name_ssbv: best_ssbv}
            self._emit_progress(i, total)

        return result

    def ssbv_line_layer(
            self,
            features_dict: Dict[int, QgsFeature],
            spatial_index: QgsSpatialIndex,
            ssbvs_by_id: Dict[int, QgsFeature],
    ) -> LayerResult:
        """
        Détermine, pour chaque ligne, la ssbv avec laquelle elle
        partage la plus grande longueur d'intersection.

        :param features_dict: Entités de la couche de lignes, par fid.
        :param spatial_index: Index spatial des ssbvs.
        :param ssbvs_by_id: Dictionnaire des ssbvs, par fid.
        :return: ``{fid: {champ_ssbv: id}}``.
        """
        result: LayerResult = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result

            # Entité sans géométrie : ignorée
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue

            # Présélection rapide des ssbvs par bounding box
            candidates_ids = spatial_index.intersects(geom.boundingBox())
            if not candidates_ids:
                self.log.emit("warning", f"La feature {idx} n'intersecte aucune ssbv")
                self._emit_progress(i, total)
                continue

            # On retient la ssbv dont l'intersection avec la ligne est la plus longue
            best_ssbv: Optional[int] = None
            best_length = 0.0
            for cand_id in candidates_ids:
                ssbv_geom = ssbvs_by_id[cand_id].geometry()
                intersection = geom.intersection(ssbv_geom)
                if intersection.isEmpty():
                    continue
                length = intersection.length()
                if length > best_length:
                    best_length = length
                    best_ssbv = ssbvs_by_id[cand_id].id()

            if best_ssbv is not None:
                result[idx] = {self.field_name_ssbv: best_ssbv}

            self._emit_progress(i, total)

        return result

    def ssbv_polygon_layer(
            self,
            features_dict: Dict[int, QgsFeature],
            spatial_index: QgsSpatialIndex,
            ssbvs_by_id: Dict[int, QgsFeature],
    ) -> LayerResult:
        """
        Détermine, pour chaque polygone, la ssbv avec laquelle il
        partage la plus grande surface d'intersection.

        :param features_dict: Entités de la couche de polygones, par fid.
        :param spatial_index: Index spatial des ssbvs.
        :param ssbvs_by_id: Dictionnaire des ssbvs, par fid.
        :return: ``{fid: {champ_ssbv: id}}``.
        """
        result: LayerResult = {}
        total = len(features_dict)
        for i, (idx, f) in enumerate(features_dict.items(), start=1):
            if self.isCanceled():
                return result

            # Entité sans géométrie : ignorée
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                self.log.emit("warning", f"La feature {idx} n'a pas de géométrie")
                self._emit_progress(i, total)
                continue

            # Présélection rapide des ssbvs par bounding box
            candidates_ids = spatial_index.intersects(geom.boundingBox())
            if not candidates_ids:
                self.log.emit("warning", f"La feature {idx} n'intersecte aucune ssbv")
                self._emit_progress(i, total)
                continue

            # On retient la ssbv dont l'intersection avec le polygone est la plus grande
            best_ssbv: Optional[int] = None
            best_area = 0.0
            for cand_id in candidates_ids:
                ssbv_geom = ssbvs_by_id[cand_id].geometry()
                intersection = geom.intersection(ssbv_geom)
                if intersection.isEmpty():
                    continue
                area = intersection.area()
                if area > best_area:
                    best_area = area
                    best_ssbv = ssbvs_by_id[cand_id].id()

            if best_ssbv is not None:
                result[idx] = {self.field_name_ssbv: best_ssbv}

            self._emit_progress(i, total)

        return result

    # ---------- exécution ----------
    def run(self) -> bool:
        """
        Calcule l'attribution des ssbvs pour chaque couche (thread secondaire).

        Les résultats sont stockés dans ``self.results`` ; aucune couche
        n'est modifiée ici.

        :return: ``True`` si le traitement est allé au bout, sinon ``False``
            (échec ou annulation).
        """
        # Emprise commune de toutes les couches à traiter
        layer_list = self.info.keys()
        extent: Optional[QgsRectangle] = get_layers_extent(layer_list)

        # Index spatial et dictionnaire des ssbvs, utilisés pour toutes les couches
        ssbv_spatial_index = self.build_spatial_index(self.ssbv_layer, extent)
        if ssbv_spatial_index is None or self.isCanceled():
            return False

        ssbvs_by_id = self.build_features_dict(self.ssbv_layer)
        if ssbvs_by_id is None:
            self.log.emit("error", "Aucune feature sousbassin versant dans l'emprise, traitement annulé")
            return False

        total = len(self.info)
        for i, (layer, selected_only) in enumerate(self.info.items(), start=1):
            self.log.emit("info",f"Début du traitement de {layer.name()}")
            features_dict = self.build_features_dict(layer, selected_only=selected_only)
            if features_dict is None:
                self.log.emit("warning",
                              f"aucunes entitées séléctionnées pour {layer.name()}")
                continue

            # Choix de la méthode selon le type de géométrie (0 = point, 1 = ligne, 2 = polygone)
            if layer.geometryType() == 0:
                layer_result = self.ssbv_point_layer(features_dict, ssbv_spatial_index, ssbvs_by_id)
            elif layer.geometryType() == 1:
                layer_result = self.ssbv_line_layer(features_dict, ssbv_spatial_index, ssbvs_by_id)
            elif layer.geometryType() == 2:
                layer_result = self.ssbv_polygon_layer(features_dict, ssbv_spatial_index, ssbvs_by_id)
            else:
                self.log.emit("warning",
                              f"la couche {layer.name()} ne possède pas de géométrie compatible au traitement")
                continue

            self.results[layer] = layer_result or {}

            self._emit_subprogress(i, total)

            if self.isCanceled():
                return False

        return True

    def finished(self, result: bool) -> None:
        """
        Appelée par QGIS dans le thread principal à la fin de ``run()``.

        Applique les attributs calculés aux couches si le traitement a réussi.

        :param result: Valeur retournée par ``run()``.
        """
        if not result:
            self.log.emit("error", "Traitement échoué ou annulé, aucune mise à jour appliquée")
            return

        # Écriture des attributs (sûre ici car on est dans le thread principal)
        for layer, layer_result in self.results.items():
            update_layer_attributes(layer, layer_result)

        self.log.emit("success", "Traitement terminé")