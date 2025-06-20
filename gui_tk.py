# Hier werden wesendliche Bibilotheken importiert, die für die GUI und Netzwerkkommunikation benötigt werden.
# Die Bibliotheken tkinter, simpledialog und filedialog sind für die GUI-Komponenten zuständig
# Die Bibliothek PIL (Pillow) wird für die Bildverarbeitung verwendet, um Bilder anzuzeigen.
# Die Bibliothek queue wird für die Kommunikation zwischen Prozessen verwendet, um Nachrichten zu senden und empfangen.
# Die Bibliothek time wird für Zeitmessungen verwendet, um Inaktivitätszeiten zu verfolgen
# Die Bibliothek sys wird für Systemoperationen verwendet, z.B. um das Skript zu beenden.
# Die Bibliothek socket wird für die Netzwerkkommunikation verwendet, um Verbindungen zu anderen Peers herzustellen.

import tkinter as tk
from tkinter import simpledialog, filedialog
from PIL import Image, ImageTk
import queue
import time
import sys
import socket

# Aus der Client Klasse werden die relevanten Funktionen importiert, die für die Kommunikation mit dem Netzwerk und anderen Peers zuständig sind. 
from client import ( 
    client_send_join,
    client_send_leave,
    client_send_msg,
    client_send_img,
    client_send_who,
)
# Hier wird die Timeout für die automatische Abwesenheitsnachricht festgelegt (ab 30 Sekunden)
AWAY_TIMEOUT = 30

# Die ChatGUI-Klasse erbt von tk.Tk und stellt die Benutzeroberfläche für den Chat-Client dar.
# Sie verwaltet die Netzwerkkommunikation, die Anzeige von Nachrichten und Bildern sowie die Interaktion in grafischen Oberfläche
class ChatGUI(tk.Tk): 
    def __init__(self, config, net_to_cli, disc_to_cli, cli_to_net): # Initialisierung der Klasse (Konstruktor)
        
        super().__init__() # Super bezeichnet die Elternklasse, von der diese Klasse erbt. In diesem Fall ist es tk.Tk, die Hauptklasse für Tkinter-Anwendungen.
        self.config = config #Ruft die Konfiguration des Chat-Clients ab, die aus der config.toml geladen wurde
        self.net_to_cli = net_to_cli # IPC Queue für Nachrichten vom Netzwerk zum Client
        self.disc_to_cli = disc_to_cli # IPC Queue für Nachrichten vom Discovery-Service zum Client
        self.cli_to_net = cli_to_net # IPC Queue für Nachrichten vom Client zum Netzwerk
        self.peers = {} # Leeres Dictonary für die Peers
        self.last_activity = time.time() # Zeitstempel der letzten Aktivität, um Inaktivität zu verfolgen
        self.joined = False # Hier wird festgelegt, ob der Client einem Netzwerk beigetreten ist oder nicht 
        self._ask_user_info() # Durch den Aufruf der Methode wird der Nutzer nach seinem Namen gefragt und ein freier TCP-Port gewählt
        self._setup_ui() # Alle Bauteile der UI werden hier initialisiert
        self._join_network() # Sobald Nutzername und Port eingegeben wurden wird versucht, dem Netzwerk beizutreten.
        self._poll_queues() # Diese Methode wird regelmäßig aufgerufen, um Nachrichten aus den IPC-Queues zu verarbeiten und die Benutzeroberfläche zu aktualisieren

    def _ask_user_info(self): # Diese Methode fragt den Nutzer nach seinem Namen und wählt automatisch einen freien TCP-Port.
        name = simpledialog.askstring("Name", "Bitte gib deinen Namen ein:", parent=self) #Hier wird der Name abgefragt. parent=self bindet das Dialogfenster an die Hauptanwendung, sodass es im Vordergrund bleibt.
        if name:
            self.config.setdefault("user", {})["name"] = name #Die config wird aktualisiert, indem der Nutzername im Dictonary unter dem Schlüssel "user" gespeichert wird. `setdefault` sorgt dafür, dass das Dictonary existiert, auch wenn es vorher leer war.

        # Automatisch einen freien TCP-Port wählen anstatt den Nutzer zu fragen
        #Durch socket.socket wird ein neues Socket-Objekt erstellt, das für die Netzwerkkommunikation verwendet wird.
        # tmp_sock ist eine Variable, die ein temporäres Socket-Objekt repräsentiert.
        # Mit bind wird das Socket an eine Adresse und einen Port gebunden
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmp_sock.bind(("", 0))
        port = tmp_sock.getsockname()[1]
        tmp_sock.close()
        self.config.setdefault("network", {})["port"] = port

    def _setup_ui(self):
        self.title("Messenger")
        self.geometry("800x600")
        self.configure(bg="#2b2b2b")

        self.images = []

        main_frame = tk.Frame(self, bg="#2b2b2b")
        main_frame.pack(fill="both", expand=True)

        list_frame = tk.Frame(main_frame, bg="#2b2b2b")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        chat_frame = tk.Frame(list_frame, bg="#2b2b2b")
        chat_frame.pack(side="left", fill="both", expand=True)

        self.chat_text = tk.Text(
            chat_frame,
            font=("Helvetica", 11),
            bg="#1e1e1e",
            fg="#dcdcdc",
            wrap="word",
            state="disabled",
        )
        self.chat_text.pack(side="left", fill="both", expand=True)

        peer_frame = tk.Frame(list_frame, bg="#2b2b2b")
        peer_frame.pack(side="right", fill="y")

        self.peer_list = tk.Listbox(
            peer_frame, width=20, font=("Helvetica", 11), bg="#333", fg="#ffffff"
        )
        self.peer_list.pack(side="left", fill="y")

        bottom_frame = tk.Frame(main_frame, bg="#2b2b2b")
        bottom_frame.pack(fill="x", pady=5)

        self.text_entry = tk.Text(
            bottom_frame, height=3, font=("Helvetica", 11), bg="#1e1e1e", fg="#dcdcdc"
        )
        self.text_entry.pack(side="left", fill="both", expand=True)

        self.image_btn = tk.Button(
            bottom_frame,
            text="📷",
            width=4,
            command=self.open_image_dialog,
            bg="#007acc",
            fg="#ffffff",
            activebackground="#005f99",
            relief="flat",
            bd=0,
        )
        self.image_btn.pack(side="left", padx=(5, 0))

        self.send_btn = tk.Button(
            bottom_frame,
            text="Senden",
            width=10,
            command=self._send_message,
            bg="#007acc",
            fg="#ffffff",
            activebackground="#005f99",
            relief="flat",
            bd=0,
        )
        self.send_btn.pack(side="left", padx=5)

        self.text_entry.bind("<Return>", self._send_message_event)
    #
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
                self._append_text(f"{from_handle}: {text}\n")
            elif msg[0] == "IMG":
                from_handle = msg[1]
                path = msg[2]
                self._append_image(from_handle, path)
        while True:
            try:
                dmsg = self.disc_to_cli.get_nowait()
            except queue.Empty:
                break
            if dmsg[0] == "PEERS":
                self.peers = dmsg[1]
                self._update_peer_list()
        self.after(100, self._poll_queues)

    def _update_peer_list(self):
        self.peer_list.delete(0, "end")
        for h in sorted(self.peers.keys()):
            self.peer_list.insert("end", h)

    def _append_text(self, text):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", text)
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def _append_image(self, prefix, path):
        try:
            img = Image.open(path)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.images.append(photo)
            self.chat_text.configure(state="normal")
            if prefix:
                self.chat_text.insert("end", f"{prefix}: ")
            self.chat_text.image_create("end", image=photo)
            self.chat_text.insert("end", "\n")
            self.chat_text.configure(state="disabled")
            self.chat_text.see("end")
        except Exception:
            self._append_text(f"[Bild {prefix}] {path}\n")

    # Diese Methode sendet eine Nachricht, die im Eingabefeld eingegeben wurde.
    def _send_message(self):
        # Aktualisiere die letzte Aktivitätszeit, um Inaktivität zu verfolgen
        self.last_activity = time.time()
        # Lese den Text aus dem Eingabefeld und entferne führende und nachfolgende Leerzeichen
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            return

        # Erlaube die bekannte CLI-Syntax wie "msg <user> <text>" oder
        # "img <user> <pfad>" direkt im Eingabefeld. Weitere Befehle wie
        # "msg all", "who", "leave" und "help" werden ebenfalls interpretiert.
        if text.startswith("msg "):
            # Teile den Text in Teile auf, um den Nutzer und die Nachricht zu extrahieren
            parts = text.split(" ", 2)
            # Wenn genau 3 Teile vorhanden sind, sende die Nachricht an den Nutzer
            if len(parts) == 3:
                # Extrahiere den Nutzer und die Nachricht
                # parts[0] ist "msg", parts[1] ist der Nutzer, parts
                handle, message = parts[1], parts[2]
                # Überprüfe, ob der Nutzer in der Peer-Liste vorhanden ist
                if handle in self.peers:    
                    # Hole die Host- und Port-Informationen des Nutzers
                    host, port = self.peers[handle]
                    try:
                        # Sende die Nachricht an den Nutzer
                        client_send_msg(host, port, self.config["handle"], message)
                        # Füge die Nachricht zum Chat-Fenster hinzu
                        self._append_text(f"[Du -> {handle}] {message}\n")
                    except OSError as e:
                        # Wenn ein Fehler auftritt, füge eine Fehlermeldung zum Chat-Fenster hinzu
                        self._append_text(f"[Fehler] {e}\n")
                else:
                    # Wenn der Nutzer nicht in der Peer-Liste ist, füge eine Fehlermeldung hinzu
                    self._append_text("[Fehler] Unbekannter Nutzer\n")
            else:
                # Wenn die Syntax nicht korrekt ist, füge eine Fehlermeldung hinzu
                self._append_text("[Fehler] Syntax: msg <user> <text>\n")
                # Leere das Eingabefeld
            self.text_entry.delete("1.0", "end")
            return
        
        # Wenn der Text mit "msgall " oder "msg all " beginnt, sende die Nachricht an alle Peers
        if text.startswith("msgall ") or text.startswith("msg all "):
            # Extrahiere die Nachricht, indem der Text nach dem Befehl aufgeteilt wird
            message = text.split(" ", 1)[1].split(" ", 1)[1] if text.startswith("msg all ") else text.split(" ", 1)[1]
            # Fehlermeldung wenn keine anderen Peers vorhanden sind
            if not self.peers:
                self._append_text("[Fehler] Keine anderen Peers\n")
            # Wenn es Peers gibt, sende die Nachricht an alle
            else:
                for h, (host, port) in self.peers.items():
                    try:
                        client_send_msg(host, port, self.config["handle"], message)
                    #Fehlerbehandlung, wenn das Senden der Nachricht fehlschlägt
                    except OSError as e:
                        self._append_text(f"[Fehler] zu {h}: {e}\n")
                self._append_text(f"[Du -> alle] {message}\n")
            # Leere das Eingabefeld
            self.text_entry.delete("1.0", "end")
            return
        

        # Wenn der Text mit "img " beginnt, sende ein Bild an den Nutzer
        # Teile den Text in Teile auf, um den Nutzer und den Pfad zum Bild zu extrahieren
        if text.startswith("img "):
            parts = text.split(" ", 2)
            if len(parts) == 3:
                handle, path = parts[1], parts[2]
                # Überprüfe, ob der Nutzer in der Peer-Liste vorhanden ist
                # Wenn der Nutzer in der Peer-Liste ist, sende das Bild
                # Ansonsten füge eine Fehlermeldung hinzu
                if handle in self.peers:
                    host, port = self.peers[handle]
                    try:
                        if client_send_img(host, port, self.config["handle"], path):
                            self._append_image(f"Du -> {handle}", path)
                        else:
                            self._append_text("[Fehler] Datei nicht gefunden\n")
                    except OSError as e:
                        self._append_text(f"[Fehler] {e}\n")
                else:
                    self._append_text("[Fehler] Unbekannter Nutzer\n")
            else:
                self._append_text("[Fehler] Syntax: img <user> <pfad>\n")
            # Leere das Eingabefeld
            self.text_entry.delete("1.0", "end")
            return

        # Wenn der Text "leave" eingegeben wird, verlasse das Netzwerk
        if text == "leave":
            if self.joined:
                # Sende eine Nachricht an den Server, um das Netzwerk zu verlassen
                client_send_leave(self.config)
                # Setze den Beitrittsstatus auf False und füge eine Nachricht zum Chat-Fenster hinzu
                self.joined = False
                # Aktualisiere die Peer-Liste
                self._append_text("[Info] Netzwerk verlassen\n")
            else:
                # Wenn der Nutzer nicht im Netzwerk ist, füge eine Nachricht zum Chat-Fenster hinzu
                self._append_text("[Info] Nicht im Netzwerk\n")
                # Leere das Eingabefeld
            self.text_entry.delete("1.0", "end")
            return

        # help Funktion, die eine Liste von Befehlen anzeigt
        if text == "help":
            # Zeigt im Textfeld die Liste der verfügbaren Befehle an
            self._append_text(
                "Befehle: msg <user> <text>, msgall <text>, img <user> <pfad>, who, leave, help\n"
            )
            # Leere das Eingabefeld
            self.text_entry.delete("1.0", "end")
            return

        # Ermittelt die aktuell ausgewählte Zeile in der Peer-Liste
        sel = self.peer_list.curselection()
        if not sel:
            # Falls kein Peer ausgewählt wurde, Funktion beenden
            return
        # Holt den Handle (Benutzernamen) des ausgewählten Peers
        handle = self.peer_list.get(sel[0])
        # Prüft, ob der Handle in der bekannten Peerliste existiert
        if handle in self.peers:
            host, port = self.peers[handle]  # IP-Adresse und Port des Peers holen
            try:
                # Sende die Nachricht an den ausgewählten Peer
                client_send_msg(host, port, self.config["handle"], text)
                # Zeige die gesendete Nachricht im Chatfenster an
                self._append_text(f"[Du -> {handle}] {text}\n")
            except OSError as e:
                # Zeige eine Fehlermeldung im Chatfenster an, falls das Senden fehlschlägt
                self._append_text(f"[Fehler] {e}\n")
        # Leere das Texteingabefeld nach dem Senden der Nachricht
        self.text_entry.delete("1.0", "end")

    # Diese Methode wird aufgerufen, wenn der Nutzer die Eingabetaste drückt, um eine Nachricht zu senden.
    def _send_message_event(self, event):
        # Verhindert das automatische Einfügen eines Zeilenumbruchs im Textfeld
        self._send_message()
        return "break"

    # Öffnet einen Dialog zum Auswählen und Senden eines Bildes an den ausgewählten Peer
    def open_image_dialog(self):
        sel = self.peer_list.curselection()
        if not sel:
            # Kein Peer ausgewählt, daher abbrechen
            return
        # Öffnet einen Dateiauswahldialog für Bilddateien
        filename = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )
        if filename:
            # Holt den Handle des ausgewählten Peers
            handle = self.peer_list.get(sel[0])
            if handle in self.peers:
                host, port = self.peers[handle]
                # Versucht, das Bild an den Peer zu senden
                if client_send_img(host, port, self.config["handle"], filename):
                    # Zeigt das gesendete Bild im Chatfenster an
                    self._append_image(f"Du -> {handle}", filename)
                else:
                    # Zeigt eine Fehlermeldung an, falls das Bild nicht gefunden wurde
                    self._append_text("[Fehler] Datei nicht gefunden\n")

    # Wird aufgerufen, wenn das Fenster geschlossen wird
    def on_close(self):
        if self.joined:
            # Sende LEAVE-Nachricht an den Server, wenn der Nutzer beigetreten ist
            client_send_leave(self.config)
        # Schließt das Fenster
        self.destroy()

# Startet die GUI-Anwendung
def startGui(config, net_to_cli, disc_to_cli, cli_to_net):
    app = ChatGUI(config, net_to_cli, disc_to_cli, cli_to_net)
    # Setzt das Verhalten beim Schließen des Fensters
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    # Startet die Haupt-Event-Schleife der GUI
    app.mainloop()