import tkinter as tk
from tkinter import simpledialog, filedialog

import socket
import queue
import os
from PIL import Image, ImageTk

from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import queue
import time
import sys
import socket
import queue
import os


from client import (
    client_send_join,
    client_send_leave,
    client_send_msg,
    client_send_img,
    client_send_who,
)


class ChatGUI(tk.Tk):
    def __init__(self, config, net_to_cli, disc_to_cli, cli_to_net):
        super().__init__()
        self.config = config
        self.net_to_cli = net_to_cli
        self.disc_to_cli = disc_to_cli
        self.cli_to_net = cli_to_net
        self.peers = {}
        self.images = []
        self._ask_info()
        self._setup_ui()
        self._join_network()
        self.after(100, self._poll)

    def _ask_info(self):
        name = simpledialog.askstring("Name", "Bitte gib deinen Namen ein:", parent=self)
        if name:
            self.config.setdefault("user", {})["name"] = name
        s = socket.socket(); s.bind(("", 0))
        self.config.setdefault("network", {})["port"] = s.getsockname()[1]
        s.close()

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

        self.chat_text = ScrolledText(
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

        self.geometry("600x400")
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.chat = tk.Text(frame, state="disabled", wrap="word")
        self.chat.pack(side="left", fill="both", expand=True)
        right = tk.Frame(frame)
        right.pack(side="right", fill="y")
        self.peers_box = tk.Listbox(right, width=20)
        self.peers_box.pack(fill="y")
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x")
        self.entry = tk.Entry(btn_frame)
        self.entry.pack(side="left", fill="x", expand=True)
        tk.Button(btn_frame, text="📷", command=self._send_image).pack(side="left")
        tk.Button(btn_frame, text="Senden", command=self._send_message).pack(side="left")
        tk.Button(btn_frame, text="Aktualisieren", command=self._refresh_peers).pack(side="left")

        tk.Button(btn_frame, text="Leave", command=self._leave).pack(side="left")
        tk.Button(btn_frame, text="Join", command=self._join_network).pack(side="left")
        self.entry.bind("<Return>", self._send_message)

        self.entry.bind("<Return>", self._send_message)


    def _join_network(self):
        if getattr(self, "joined", False):
            return
        handle = self.config.get("user", {}).get("name")
        port = self.config.get("network", {}).get("port")
        if handle and port:
            self.config["handle"] = handle
            self.config["port"] = port
            if self.cli_to_net:
                self.cli_to_net.put(("SET_PORT", port))
            client_send_join(self.config)
            client_send_who(self.config)
            self.joined = True

            self._refresh_peers()


    def _poll(self):
        while True:
            try:
                msg = self.net_to_cli.get_nowait()
            except queue.Empty:
                break
            if msg[0] == "MSG":
                self._append_text(f"{msg[1]}: {msg[2]}\n")
            elif msg[0] == "IMG":
                self._append_image(msg[1], msg[2])
        while True:
            try:
                dmsg = self.disc_to_cli.get_nowait()
            except queue.Empty:
                break
            if dmsg[0] == "PEERS":
                self.peers = dmsg[1]
                self._update_peers()
        self.after(100, self._poll)

    def _update_peers(self):
        self.peers_box.delete(0, "end")
        for h in sorted(self.peers):
            self.peers_box.insert("end", h)

    def _append_text(self, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", text)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _append_image(self, prefix, path):
        try:

            img = Image.open(os.path.abspath(path))
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.images.append(photo)
            self.chat.configure(state="normal")
            if prefix:
                self.chat.insert("end", f"{prefix}: ")
            self.chat.image_create("end", image=photo)

            img = tk.PhotoImage(file=os.path.abspath(path))
            # verkleinere große Bilder rudimentär, um das Layout nicht zu sprengen
            m = max(img.width(), img.height())
            if m > 200:
                f = max(m // 200, 1)
                img = img.subsample(f)

            img = tk.PhotoImage(file=path)
            self.images.append(img)
            self.chat.configure(state="normal")
            if prefix:
                self.chat.insert("end", f"{prefix}: ")
            self.chat.image_create("end", image=img)

            self.chat.insert("end", "\n")
            self.chat.configure(state="disabled")
            self.chat.see("end")
        except Exception:
            self._append_text(f"[Bild {prefix}] {path}\n")

    def _send_message(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return "break"
        sel = self.peers_box.curselection()
        if not sel:
            return "break"
        handle = self.peers_box.get(sel[0])
        if handle in self.peers:
            host, port = self.peers[handle]
            client_send_msg(host, port, self.config["handle"], text)
            self._append_text(f"[Du -> {handle}] {text}\n")
        self.entry.delete(0, "end")
        return "break"

    def _send_image(self):
        sel = self.peers_box.curselection()
        if not sel:
            return
        filename = filedialog.askopenfilename(title="Bild auswählen", filetypes=[("Bilder", "*.png *.jpg *.jpeg *.gif")])
        if not filename:
            return
        handle = self.peers_box.get(sel[0])
        if handle in self.peers:
            host, port = self.peers[handle]
            if client_send_img(host, port, self.config["handle"], filename):
                self._append_image(f"Du -> {handle}", filename)

    def _refresh_peers(self):
        client_send_who(self.config)


    def _leave(self):
        if getattr(self, "joined", False):
            client_send_leave(self.config)
            self.joined = False
            self._refresh_peers()


    def on_close(self):
        if getattr(self, "joined", False):
            client_send_leave(self.config)
        self.destroy()


def startGui(config, net_to_cli, disc_to_cli, cli_to_net):

    app = ChatGUI(config, net_to_cli, disc_to_cli, cli_to_net)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

    """
    Startet die Tkinter-basierte GUI für den Chat-Client.
    
    Parameter:
      config       - Konfiguration (z. B. Handle, Ports), aus der nebenbei der Fenstertitel gesetzt wird.
      net_to_cli   - Queue für Nachrichten vom Netzwerk zur GUI.
      disc_to_cli  - Queue für Nachrichten vom Discovery-Service zur GUI.
      cli_to_net   - Queue für Nachrichten, die von der GUI ins Netzwerk gesendet werden.
    """
    # Erstelle das Hauptfenster der GUI.
    root = tk.Tk()
    # Setze den Fenstertitel, z.B. "Chat Client - user_name".
    root.title(f"Chat Client - {config['handle']}")

    # Erstelle einen gescrollten Textbereich, in dem der Chat-Verlauf angezeigt wird.
    # Der 'state' ist auf 'disabled' gesetzt, damit der Benutzer den Text nicht direkt bearbeiten kann.
    chat_display = ScrolledText(root, state='disabled', width=80, height=20)
    chat_display.pack(padx=10, pady=10)

    # Erstelle ein Eingabefeld, über das der Benutzer Nachrichten eintippen kann.
    entry = tk.Entry(root, width=80)
    entry.pack(padx=10, pady=5)
    
    def send_message(event=None):
        """
        Diese Funktion wird aufgerufen, wenn der Benutzer die Eingabetaste drückt.
        
        Sie liest den Text aus dem Eingabefeld, sendet die Nachricht an das Netzwerk
        (zum Beispiel über die Queue 'cli_to_net') und fügt die gesendete Nachricht
        dem Chat-Display hinzu. Anschließend wird das Eingabefeld geleert.
        """
        msg = entry.get().strip()  # Hole den Inhalt des Eingabefelds und entferne unnötige Leerzeichen.
        if msg:
            # Hier könntest du die Nachricht z.B. ins Queue-System einfügen:
            # cli_to_net.put(('MSG', msg))
            #
            # Aktualisiere das Chat-Display mit der eigenen gesendeten Nachricht.
            chat_display.config(state='normal')  # Mache den Textbereich schreibbar, um Text hinzuzufügen.
            chat_display.insert(tk.END, f"Ich: {msg}\n")  # Füge die Nachricht am Ende ein.
            chat_display.config(state='disabled')  # Setze den Textbereich wieder auf 'disabled'.
            chat_display.see(tk.END)  # Scrolle zum Ende, damit die neueste Nachricht sichtbar ist.
            entry.delete(0, tk.END)  # Leere das Eingabefeld.

    # Binde das Drücken der Return-Taste an die Funktion send_message.
    entry.bind('<Return>', send_message)
    
    # Starte die Hauptschleife der GUI, die das Fenster offen hält und auf Ereignisse reagiert.
    root.mainloop()

# Falls diese Datei direkt ausgeführt wird, kann man hier z.B. einen einfachen Test starten:
if __name__ == '__main__':
    import argparse
    import toml
    from multiprocessing import Process, Queue
    import discovery_service
    import server

    parser = argparse.ArgumentParser(description="Start Tk GUI")
    parser.add_argument("--config", default="config.toml", help="Pfad zur Konfig-Datei")
    args = parser.parse_args()

    config = toml.load(args.config)

    cli_to_net = Queue()
    cli_to_disc = Queue()
    net_to_cli = Queue()
    disc_to_cli = Queue()

    disc_proc = Process(target=discovery_service.discovery_loop, args=(config, disc_to_cli))
    disc_proc.daemon = True
    disc_proc.start()

    net_proc = Process(target=server.server_loop, args=(config, net_to_cli, cli_to_net))
    net_proc.daemon = True
    net_proc.start()

    startGui(config, net_to_cli, disc_to_cli, cli_to_net)

    app = ChatGUI(config, net_to_cli, disc_to_cli, cli_to_net)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

