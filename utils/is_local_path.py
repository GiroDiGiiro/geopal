from __future__ import annotations

import os
import sys
from pathlib import Path

DRIVE_FIXED: int = 3


def is_local_path(path: str | os.PathLike[str]) -> bool:
    """
    Détermine si un chemin pointe vers un disque dur local fixe.

    Gère deux cas de chemins réseau :
    - lettre mappée sur un partage (ex: "S:\\dossier"), détectée via GetDriveTypeW
    - chemin UNC brut (ex: "\\\\serveur\\partage\\dossier"), détecté directement

    :param path: le chemin d'accès à tester
    :return: True si le chemin est sur un disque local fixe, False sinon
    :raises NotImplementedError: si exécuté sur un OS autre que Windows
    """
    if sys.platform != "win32":
        raise NotImplementedError("Vérification disponible uniquement sous Windows")

    import ctypes  # import local : uniquement nécessaire sous Windows

    path = Path(path)

    if not path.drive:
        return False

    # Un chemin UNC est toujours distant, peu importe ce que renverrait GetDriveTypeW
    if path.drive.startswith("\\\\") or path.drive.startswith("//"):
        return False

    drive_type: int = ctypes.windll.kernel32.GetDriveTypeW(path.drive + "\\")
    return drive_type == DRIVE_FIXED