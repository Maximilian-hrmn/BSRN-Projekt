from PyQt5 import QtCore, QtGui, QtWidgets
from client import SLCPClient
from GUI import Ui_MainWindow 

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, client, peers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.client = client
        self.peers = peers

        # Nachrichten-Model für Chatfenster
        self.chat_model = QtGui.QStandardItemModel()
        self.ui.listView.setModel(self.chat_model)

        # Peers-Model für rechte Liste
        self.peers_model = QtGui.QStandardItemModel()
        self.ui.listView_2.setModel(self.peers_model)
        self.update_peers_list()

        # Button-Events verbinden
        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.toolButton.clicked.connect(self.select_image)

    def send_message(self):
        text = self.ui.textEdit.toPlainText().strip()
        if text:
            self.client.send_msg(text)
            self.add_message(f"Du: {text}")
            self.ui.textEdit.clear()

    def select_image(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Bild auswählen", "", "Bilder (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            # Hier ggf. Empfänger auswählen, z.B. aus Peerliste
            empfaenger = self.peers[0] if self.peers else "unknown"
            self.client.send_image(empfaenger, file_path)
            self.add_message(f"Du hast ein Bild gesendet: {file_path}")

    def add_message(self, message):
        item = QtGui.QStandardItem(message)
        self.chat_model.appendRow(item)

    def update_peers_list(self):
        self.peers_model.clear()
        for peer in self.peers:
            item = QtGui.QStandardItem(str(peer))
            self.peers_model.appendRow(item)