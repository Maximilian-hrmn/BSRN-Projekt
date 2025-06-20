"""
Zunächst werden alle notwendigen Module importiert 
PyQt5 richtet das grafische User Interface ein mit QtCore, QtGui und QtWidgets
sys beinhaltet Funktionen und Variablen, die mit dem Interpreter selbst zu tun haben
queue richtet eine Warteschlange für die Kommunikation zwischen Prozessen ein
time wird für Zeitmessungen verwendet, um Inaktivität zu erkennen
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QInputDialog, QFileDialog
import sys
import queue
import time

# Hier werden alle relevanten Module des client importiert
from client import (
    client_send_join,
    client_send_leave,
    client_send_msg,
    client_send_img,
    client_send_who,
)

# Hier wird das Timeoutlimit festgelegt 
AWAY_TIMEOUT = 30

# Die Klasse Ui_MainWindow ist die Hauptklasse für das GUI, die von QMainWindow erbt
# Sie initialisiert die Konfiguration, die IPC-Queues und startet die notwendigen Prozesse
class Ui_MainWindow(QtWidgets.QMainWindow):
    #Konstruktor der Klasse, der die Konfiguration und IPC-Queues initialisiert
    def __init__(self, config, net_to_cli, disc_to_cli, cli_to_net):
        super().__init__()
        self.config = config # Speichert die Konfiguration, die aus der config.toml geladen wurde
        self.net_to_cli = net_to_cli 
        self.disc_to_cli = disc_to_cli # Beschreibt die Queue, die Nachrichten vom Discovery-Service empfängt
        self.cli_to_net = cli_to_net # Beschreibt die Queue, die Nachrichten an das Netzwerk sendet
        self.peers = {} # Dictonary, das die Peers im Netzwerk speichert
        self.last_activity = time.time()
        self.joined = False
        self.userInfoAbfrage()
        self.setupUi()
        self._setup_models()
        self._start_timers()
        self._join_network()

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
        self.centralwidget.setLayoutDirection(QtCore.Qt.LeftToRight)# type: ignore[attr-defined]
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

    def _setup_models(self):
        self.chat_model = QtGui.QStandardItemModel(self.listView)
        self.listView.setModel(self.chat_model)
        self.peer_model = QtGui.QStandardItemModel(self.listView_2)
        self.listView_2.setModel(self.peer_model)

        self.pushButton.clicked.connect(self._send_message)
        self.toolButton.clicked.connect(self.open_image_dialog)

    def _start_timers(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._poll_queues)
        self.timer.start(100)

    def _join_network(self):
        handle = self.config.get("user", {}).get("name")
        port = self.config.get("network", {}).get("port")
        if handle and port:
            self.config["handle"] = handle
            self.config["port"] = port
            if self.cli_to_net:
                self.cli_to_net.put(("SET_PORT", port))
            client_send_join(self.config)
            self.joined = True
            client_send_who(self.config)

    def _poll_queues(self):
        now = time.time()
        while True:
            try:
                msg = self.net_to_cli.get_nowait()
            except queue.Empty:
                break
            if msg[0] == "MSG":
                from_handle = msg[1]
                text = msg[2]
                if now - self.last_activity > AWAY_TIMEOUT and self.joined:
                    auto_msg = self.config.get("autoreply")
                    if auto_msg and from_handle in self.peers:
                        thost, tport = self.peers[from_handle]
                        client_send_msg(thost, tport, self.config["handle"], auto_msg)
                item = QtGui.QStandardItem(f"{from_handle}: {text}")
                self.chat_model.appendRow(item)
            elif msg[0] == "IMG":
                from_handle = msg[1]
                path = msg[2]
                item = QtGui.QStandardItem(f"[Bild von {from_handle}] {path}")
                self.chat_model.appendRow(item)

        while True:
            try:
                dmsg = self.disc_to_cli.get_nowait()
            except queue.Empty:
                break
            if dmsg[0] == "PEERS":
                self.peers = dmsg[1]
                self._update_peer_model()

    def _update_peer_model(self):
        self.peer_model.clear()
        for h in sorted(self.peers.keys()):
            self.peer_model.appendRow(QtGui.QStandardItem(h))

    def _send_message(self):
        self.last_activity = time.time()
        text = self.textEdit.toPlainText().strip()
        if not text:
            return
        indexes = self.listView_2.selectedIndexes()
        if not indexes:
            return
        handle = indexes[0].data()
        if handle in self.peers:
            host, port = self.peers[handle]
            client_send_msg(host, port, self.config["handle"], text)
            item = QtGui.QStandardItem(f"[Du -> {handle}] {text}")
            self.chat_model.appendRow(item)
        self.textEdit.clear()

    def closeEvent(self, event): # type: ignore
        if self.joined:
            client_send_leave(self.config)
        super().closeEvent(event)

    def open_image_dialog(self):
        indexes = self.listView_2.selectedIndexes()
        if not indexes:
            return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Bild auswählen",
            "",
            "Bilder (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if filename:
            handle = indexes[0].data()
            if handle in self.peers:
                host, port = self.peers[handle]
                if client_send_img(host, port, self.config["handle"], filename):
                    item = QtGui.QStandardItem(
                        f"[Du -> {handle}] Bild gesendet: {filename}"
                    )
                    self.chat_model.appendRow(item)
            # Hier könntest du die Datei laden, versenden oder anzeigen etc.