from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QFileDialog
import sys

class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config, net_to_cli, disc_to_cli):
        super().__init__()
        self.config = config
        self.net_to_cli = net_to_cli
        self.disc_to_cli = disc_to_cli
        self.userInfoAbfrage()
        self.setupUi()

    def userInfoAbfrage(self):
        name, ok = QInputDialog.getText(self, "Name", "Bitte gib deinen Namen ein:")
        if ok and name:
            self.config.setdefault("user", {})["name"] = name

        port, ok = QInputDialog.getInt(self, "Port", "Bitte gib deinen Port ein:", value=5000, min=1024, max=65535)
        if ok:
            self.config.setdefault("network", {})["port"] = port

    def setupUi(self):
        self.setObjectName("MainWindow")
        self.resize(830, 575)

        # MainWindow Size Policy
        mainSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        mainSizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(mainSizePolicy)

        # Central Widget
        self.centralwidget = QtWidgets.QWidget(self)
        centralSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        centralSizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(centralSizePolicy)
        self.centralwidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.centralwidget.setObjectName("centralwidget")

        # Layouts
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()

        # Chat-Fenster (links)
        self.listView = QtWidgets.QListView(self.centralwidget)
        self.listView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.listView.setObjectName("listView")
        self.horizontalLayout_2.addWidget(self.listView)

        # Verbindungen (rechts)
        self.listView_2 = QtWidgets.QListView(self.centralwidget)
        self.listView_2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.listView_2.setObjectName("listView_2")
        self.horizontalLayout_2.addWidget(self.listView_2)

        self.horizontalLayout_2.setStretch(0, 69)
        self.horizontalLayout_2.setStretch(1, 30)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        # Untere Leiste (Textfeld, ToolButton, Senden)
        self.horizontalLayout = QtWidgets.QHBoxLayout()

        # Eingabefeld
        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.textEdit.setFont(font)
        self.textEdit.setObjectName("textEdit")
        self.horizontalLayout.addWidget(self.textEdit)

        # Bilder-Button
        self.toolButton = QtWidgets.QToolButton(self.centralwidget)
        self.toolButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolButton.setObjectName("toolButton")
        self.toolButton.setToolTip("Bild auswählen oder hochladen")
        self.toolButton.setText("📷")
        self.toolButton.clicked.connect(self.open_image_dialog)
        self.horizontalLayout.addWidget(self.toolButton)

        # Senden-Button
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setToolTip("Nachricht senden")
        self.pushButton.setText("Senden")
        self.horizontalLayout.addWidget(self.pushButton)

        self.horizontalLayout.setStretch(0, 70)
        self.horizontalLayout.setStretch(1, 10)
        self.horizontalLayout.setStretch(2, 20)

        self.verticalLayout.addLayout(self.horizontalLayout)

        # Stretch setzen
        self.verticalLayout.setStretch(0, 9)
        self.verticalLayout.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.setCentralWidget(self.centralwidget)

        # Statusbar
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.setWindowTitle("Messenger")

    def open_image_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Bild auswählen", "", "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)")
        if filename:
            print("Bild ausgewählt:", filename)
            # Hier könntest du die Datei laden, versenden oder anzeigen etc.

# Startfunktion
def startGui(config, net_to_cli, disc_to_cli):
    app = QtWidgets.QApplication(sys.argv)
    window = Ui_MainWindow(config, net_to_cli, disc_to_cli)
    window.show()
    sys.exit(app.exec_())