from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(830, 575)

        # MainWindow
        mainSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        mainSizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(mainSizePolicy)

        # Central Widget
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        centralSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        centralSizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(centralSizePolicy)
        self.centralwidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.centralwidget.setObjectName("centralwidget")

        # Main Layout
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.verticalLayout.setObjectName("verticalLayout")

        # horizontales layout (Chat-Fenster und Liste der Verbindungen)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        # Chat-Fenster
        self.listView = QtWidgets.QListView(self.centralwidget)
        listViewPolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.listView.setSizePolicy(listViewPolicy)
        self.listView.setObjectName("listView")
        self.horizontalLayout_2.addWidget(self.listView)

        # Liste der Verbindungen
        self.listView_2 = QtWidgets.QListView(self.centralwidget)
        listView2Policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.listView_2.setSizePolicy(listView2Policy)
        self.listView_2.setObjectName("listView_2")
        self.horizontalLayout_2.addWidget(self.listView_2)

        self.horizontalLayout_2.setStretch(0, 70)
        self.horizontalLayout_2.setStretch(1, 30)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        # Unteres Layout mit Eingabefeld, Bilder Button und Senden Button
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Eingabefeld
        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        textEditPolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.textEdit.setSizePolicy(textEditPolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.textEdit.setFont(font)
        self.textEdit.setObjectName("textEdit")
        self.horizontalLayout.addWidget(self.textEdit)

        # Bilder Button
        self.toolButton = QtWidgets.QToolButton(self.centralwidget)
        toolButtonPolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolButton.setSizePolicy(toolButtonPolicy)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout.addWidget(self.toolButton)
        self.toolButton.setToolTip("Bild auswählen oder hochladen")

        # Senden Button
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        pushButtonPolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.pushButton.setSizePolicy(pushButtonPolicy)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)

        self.horizontalLayout.setStretch(0, 70)
        self.horizontalLayout.setStretch(1, 10)
        self.horizontalLayout.setStretch(2, 20)

        self.verticalLayout.addLayout(self.horizontalLayout)
        self.pushButton.setToolTip("Nachricht senden")

        # Stretch zwischen layouts
        self.verticalLayout.setStretch(0, 5)  # Top ListViews
        self.verticalLayout.setStretch(1, 1)  # Bottom Controls

        self.verticalLayout_2.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)

        # Status Bar
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setAutoFillBackground(False)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("Messenger", "Messenger"))
        self.toolButton.setText(_translate("MainWindow", "..."))
        self.toolButton.setAccessibleDescription("Klick zum Auswählen eines Bildes")
        self.pushButton.setText(_translate("MainWindow", "Senden"))
        self.pushButton.setAccessibleDescription("Klick zum Senden der Nachricht")


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
