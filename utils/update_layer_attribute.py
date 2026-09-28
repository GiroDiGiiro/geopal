from qgis.core import QgsFeatureRequest, edit


def update_layer_attributes(layer, updates, **kwargs) -> bool:
    """
    Met à jour les attributs des entités d'une couche vectorielle QGIS.

    Parameters
    ----------
    layer : QgsVectorLayer
        Couche vectorielle dont les attributs doivent être mis à jour.

    updates : dict
        Définit les valeurs à appliquer. Trois formats sont acceptés :

        - ``{"champ": valeur}``
            Applique une valeur identique à toutes les entités concernées.

        - ``{"champ": fonction}``
            Calcule la valeur pour chaque entité à partir de la fonction fournie.
            La fonction reçoit l'entité en argument, par exemple :
            ``{"champ": lambda f: f["autre_champ"]}``.

        - ``{fid: {"champ": valeur, "champ2": valeur2}}``
            Applique des valeurs spécifiques aux entités identifiées par leur
            ``fid``.

    **kwargs
        Options de mise à jour.

        selected_only : bool, optional
            Si ``True``, limite la mise à jour aux entités sélectionnées.
            Par défaut : ``False``.

    Returns
    -------
    bool
        ``True`` si la mise à jour a réussi, sinon ``False``.
    """
    selected_only = kwargs.get("selected_only", False)

    print(f'Mise à jour des attributs de {layer.name()}')
    if not updates:
        print(f'Aucune updates pour la couche {layer.name()}')
        return False
    fids = [f.id() for f in (layer.selectedFeatures() if selected_only else layer.getFeatures())]
    fields = layer.fields()

    #  Cas 1 : {"champ": valeur }
    if all(isinstance(k, str) and not callable(v) for k, v in updates.items()):
        print('Cas {"champ": valeur }')
        changes = {}
        for fid in fids:
            attr = {}
            for field, value in updates.items():
                idx = fields.indexFromName(field)
                attr[idx] = value
            changes[fid] = attr

        print(f' layer : {layer.name()} -> updates : {changes}')

    #  Cas 2 : {"champ": fonction(feature) }
    elif all(isinstance(k, str) and callable(v) for k, v in updates.items()):
        print('Cas {"champ": fonction(feature) }')
        changes = {}
        for fid in fids:
            feat = layer.getFeature(fid)
            attr = {}
            for field, value in updates.items():
                idx = fields.indexFromName(field)
                attr[idx] = value(feat)
            changes[fid] = attr

        print(f'updates : {changes}')

    #  Cas 3 : {fid: {"champ": valeur, "champ2": valeur2}}
    elif all(isinstance(k, int) and isinstance(v, dict) for k, v in updates.items()):
        print('Cas fid: {"champ": valeur, "champ2": valeur2}}')
        changes = {}
        for fid, change in updates.items():
            attr = {}
            for field, value in change.items():
                idx = fields.indexFromName(field)
                attr[idx] = value
            changes[fid] = attr

        print(f'updates : {changes}')

    else:
        raise ValueError(
            "Format d’updates invalide : clés doivent être des noms de champs ou des FIDs avec dictionnaires d’attributs.")

    layer.dataProvider().changeAttributeValues(changes)
    layer.triggerRepaint()
    layer.commitChanges()
    print(f"{len(fids)} entités mises à jour avec succès.")
    return True
