from typing import List

from qgis.core import QgsProject, QgsLayerTreeGroup


def move_layers_to_group(
        layer_names: List[str],
        group_name: str,
        create_if_missing: bool = False,
) -> QgsLayerTreeGroup:
    """
    Déplace une ou plusieurs couches déjà chargées dans le projet vers un groupe
    du layer tree QGIS.

    Si le groupe cible n'existe pas encore dans l'arbre des couches, il est soit
    créé automatiquement, soit une erreur est levée, selon la valeur de
    `create_if_missing`.

    Les couches introuvables (nom absent du projet) ou dont le noeud n'est pas
    trouvé dans l'arbre sont ignorées avec un message d'avertissement ; elles
    n'interrompent pas le traitement des couches suivantes.

    :param layer_names: Liste des noms de couches à déplacer (tels que retournés
        par `QgsProject.instance().mapLayersByName()`). Si plusieurs couches du
        projet partagent le même nom, seule la première trouvée est déplacée.
    :type layer_names: List[str]

    :param group_name: Nom du groupe cible dans le layer tree. Recherché à la
        racine du projet via `QgsLayerTree.findGroup()`.
    :type group_name: str

    :param create_if_missing: Si False (par défaut), lève une `ValueError` lorsque le groupe est absent. Si True, crée le groupe s'il n'existe
        pas encore
    :type create_if_missing: bool

    :raises ValueError: Si `create_if_missing` est False et que le groupe
        `group_name` n'existe pas dans le layer tree.

    :return: Le noeud de groupe (existant ou nouvellement créé) dans lequel les
        couches ont été déplacées.
    :rtype: QgsLayerTreeGroup

    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    # Récupérer ou créer le groupe s'il n'existe pas déjà
    group = root.findGroup(group_name)
    if group is None:
        if not create_if_missing:
            raise ValueError(
                f"Le groupe '{group_name}' n'existe pas."
            )
        group = root.addGroup(group_name)

    for name in layer_names:
        layers = project.mapLayersByName(name)
        if not layers:
            print(f"Couche introuvable : {name}")
            continue

        layer = layers[0]
        layer_node = root.findLayer(layer.id())
        if layer_node is None:
            print(f"Noeud introuvable dans le layer tree pour : {name}")
            continue

        clone = layer_node.clone()
        group.addChildNode(clone)
        root.removeChildNode(layer_node)

    return group
