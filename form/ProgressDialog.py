"""Boîte de dialogue minimale affichant le log et la progression d'une QgsTask."""

from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QTextBrowser
from qgis.core import QgsTask


class ProgressDialog(QDialog):
    """
    Boîte de dialogue minimale de suivi d'une ``QgsTask``.

    Attend deux signaux sur ``task`` :
      - ``log(str, str)`` : ``(niveau, message)``.
      - ``progressUpdated(int)`` : pourcentage 0-100 (peut être émis
        plusieurs fois de 0 à 100, une fois par étape du traitement).
    """

    LEVEL_COLORS = {
        "info": "#222222",
        "warning": "#e67e00",
        "error": "#cc0000",
        "success": "#007a00",
        "debug": "#848484",
    }

    def __init__(self, task: QgsTask, parent=None) -> None:
        """
        :param task: La ``QgsTask`` à suivre.
        :param parent: Widget parent.
        """
        super().__init__(parent)
        self.setWindowTitle("Traitement en cours")

        self.bar = QProgressBar(self)
        self.bar.setRange(0, 100)

        self.tb_logs = QTextBrowser(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tb_logs)
        layout.addWidget(self.bar)

        self.task = task
        self.task.log.connect(self.add_log)
        self.task.progress.connect(self.bar.setValue)
        self.tb_logs.append(f'coucou')

    def add_log(self, level: str, message: str) -> None:
        """
        Ajoute une ligne colorée au journal.

        :param level: ``info`` / ``warning`` / ``error`` / ``success`` / ``debug``.
        :param message: Message à afficher.
        """
        print('add_log')
        color = self.LEVEL_COLORS.get(level, "#222222")
        self.tb_logs.append(f'<span style="color:{color};">[{level.upper()}] {message}</span>')