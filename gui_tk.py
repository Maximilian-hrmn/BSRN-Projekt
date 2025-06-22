# gui_tk.py

import tkinter as tk
from tkinter import simpledialog, filedialog, font as tkfont, messagebox
from PIL import Image, ImageTk
import queue
import time
import socket
from client import (
    client_send_join,
    client_send_leave,
    client_send_msg,
    client_send_img,
    client_send_who,
)

AWAY_TIMEOUT = 30

"""
@file gui_tk.py
@brief Implementiert eine Chat-GUI mit Tkinter. Behandelt Benutzereingaben,
stellt Nachrichten- und Bildversand/empfang dar, verwaltet die Peer-Liste und bietet Auto-Reply bei Inaktivität.
"""


class ChatGUI(tk.Tk):
    """Die Hauptklasse für die Chat-GUI, die das Tkinter-Fenster verwaltet."""
    def __init__(self, config, net_to_interface, disc_to_interface, interface_to_net):
        super().__init__()
        self.config = config
        self.net_to_interface = net_to_interface
        self.disc_to_interface = disc_to_interface
        self.interface_to_net = interface_to_net
        self.peers = {}
        self.last_activity = time.time()
        self.joined = False
        self.base_width = 800
        self.base_height = 600
        self.scale = 1.0
        self.base_font = tkfont.Font(family="Helvetica", size=11)
        self.image_size_base = 200
        self.image_size = self.image_size_base

        self.bind("<Configure>", self._on_resize)
        self._ask_user_info()
        self._setup_ui()
        self._join_network()
        self._poll_queues()

    def _ask_user_info(self):
        """Fragt den Benutzernamen und Port ab, wenn sie nicht gesetzt sind."""
        name = simpledialog.askstring("Name", "Bitte gib deinen Namen ein:", parent=self)
        if name:
            self.config.setdefault("user", {})["name"] = name

        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmp_sock.bind(("", 0))
        port = tmp_sock.getsockname()[1]
        tmp_sock.close()
        self.config.setdefault("network", {})["port"] = port

    def _setup_ui(self):
        """Initialisiert die Benutzeroberfläche der Chat-GUI."""
        self.title("Messenger")
        self.geometry("800x600")
        self.configure(bg="#2b2b2b")
        self.images = []

        # Main Frame
        main_frame = tk.Frame(self, bg="#2b2b2b")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
        main_frame.columnconfigure(0, weight=1)

        # Upper Frame
        upper_frame = tk.Frame(main_frame, bg="#2b2b2b")
        upper_frame.grid(row=0, column=0, sticky="nsew")
        upper_frame.grid_rowconfigure(0, weight=1)
        upper_frame.grid_columnconfigure(0, weight=8)
        upper_frame.grid_columnconfigure(1, weight=2)

        # Chat Frame
        chat_frame = tk.Frame(upper_frame, bg="#2b2b2b")
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self.chat_text = tk.Text(chat_frame, font=self.base_font, bg="#1e1e1e", fg="#dcdcdc", wrap="word", state="disabled")
        self.chat_text.pack(fill="both", expand=True)

        # Peer List Frame
        peer_frame = tk.Frame(upper_frame, bg="#2b2b2b")
        peer_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        peer_frame.grid_rowconfigure(0, weight=1)
        peer_frame.grid_columnconfigure(0, weight=1)
        self.peer_list = tk.Listbox(peer_frame, width=15, font=self.base_font, bg="#333", fg="#ffffff")
        self.peer_list.grid(row=0, column=0, sticky="nsew")

        # Lower Frame
        lower_frame = tk.Frame(main_frame, bg="#2b2b2b")
        lower_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        lower_frame.columnconfigure(0, weight=70)
        lower_frame.columnconfigure(1, weight=15)
        lower_frame.columnconfigure(2, weight=15)

        # Text Entry
        self.text_entry = tk.Text(lower_frame, height=3, font=self.base_font, bg="#1e1e1e", fg="#dcdcdc")
        self.text_entry.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Image Button
        self.image_btn = tk.Button(lower_frame, text="📷", width=4, command=self.open_image_dialog, bg="#007acc", fg="#ffffff", activebackground="#005f99", relief="flat", bd=0, font=self.base_font)
        self.image_btn.grid(row=0, column=1, sticky="nsew", padx=(0, 5))

        # Send Button
        self.send_btn = tk.Button(lower_frame, text="Senden", width=10, command=self._send_message, bg="#007acc", fg="#ffffff", activebackground="#005f99", relief="flat", bd=0, font=self.base_font)
        self.send_btn.grid(row=0, column=2, sticky="nsew")

        self.text_entry.bind("<Return>", self._send_message_event)
        self.bind("<F1>", lambda e: self._show_help())

    def _join_network(self):
        """Tritt dem Netzwerk bei, wenn der Benutzername und Port gesetzt sind."""
        handle = self.config.get("user", {}).get("name")
        port = self.config.get("network", {}).get("port")
        if handle and port:
            self.config["handle"] = handle
            self.config["port"] = port
            if self.interface_to_net:
                self.interface_to_net.put(("SET_PORT", port))
            client_send_join(self.config)
            self.joined = True
            client_send_who(self.config)

    def _poll_queues(self):
        """Pollt die Nachrichten- und Diskussionswarteschlangen und aktualisiert die GUI."""
        now = time.time()
        while True:
            try:
                msg = self.net_to_interface.get_nowait()
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
                dmsg = self.disc_to_interface.get_nowait()
            except queue.Empty:
                break
            if dmsg[0] == "PEERS":
                self.peers = dmsg[1]
                self._update_peer_list()
        self.after(100, self._poll_queues)

    def _update_peer_list(self):
        """Aktualisiert die Liste der Peers in der GUI."""
        self.peer_list.delete(0, "end")
        for h in sorted(self.peers.keys()):
            self.peer_list.insert("end", h)

    def _append_text(self, text):
        """Fügt Text in den Chat ein, formatiert und skaliert."""
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", text)
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def _append_image(self, prefix, path):
        """Fügt ein Bild in den Chat ein, skaliert es und fügt es hinzu."""
        try:
            img = Image.open(path)
            img.thumbnail((self.image_size, self.image_size))
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

    def _show_help(self):
        """Zeigt eine kurze Hilfestellung analog zur CLI an."""
        help_text = (
            "Verwendung:\n"
            "- Wenn du einen einzelnen Empfänger schreiben möchtest wähle"
            " ihn in der Liste aus und gib eine Nachricht ein.\n"
            "- Wenn du allen schreiben möchtest schreibe msgall vor deine Nachricht.\n"
            "- Mit dem Kamerasymbol Bilder auswählen.\n"
            "- 'help' in das Textfeld schreiben, um diese Hilfe zu sehen."
        )
        messagebox.showinfo("Hilfe", help_text)

    def _send_message(self):
        """Sendet die Nachricht aus dem Textfeld."""
        self.last_activity = time.time()
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            return
        if text.lower() == "help":
            self._show_help()
            self.text_entry.delete("1.0", "end")
            return
        sel = self.peer_list.curselection()
        if not sel:
            self._append_text("[Fehler] Kein Empfänger ausgewählt\n")
            self.text_entry.delete("1.0", "end")
            return
        handle = self.peer_list.get(sel[0])
        if handle in self.peers:
            host, port = self.peers[handle]
            client_send_msg(host, port, self.config["handle"], text)
            self._append_text(f"Du -> {handle}: {text}\n")
        else:
            self._append_text("[Fehler] Unbekannter Peer\n")
        self.text_entry.delete("1.0", "end")

    def _send_message_event(self, event):
        """Sendet die Nachricht bei Drücken der Eingabetaste."""
        self._send_message()
        return "break"

    def _on_resize(self, event):
        """Skaliert die GUI-Elemente bei Größenänderung des Fensters."""
        if event.widget is not self:
            return
        new_scale = min(event.width / self.base_width, event.height / self.base_height)
        if abs(new_scale - self.scale) > 0.05:
            self.scale = new_scale
            self._apply_scaling()

    def _apply_scaling(self):
        """Wendet die Skalierung auf die GUI-Elemente an."""
        size = max(int(11 * self.scale), 8)
        self.base_font.configure(size=size)
        self.image_size = int(self.image_size_base * self.scale)
        if hasattr(self, "peer_list"):
            self.peer_list.configure(font=self.base_font)

    def open_image_dialog(self):
        """Öffnet einen Dialog zum Auswählen eines Bildes und sendet es."""
        sel = self.peer_list.curselection()
        if not sel:
            return
        filename = filedialog.askopenfilename(title="Bild auswählen", filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if filename:
            handle = self.peer_list.get(sel[0])
            if handle in self.peers:
                host, port = self.peers[handle]
                if client_send_img(host, port, self.config["handle"], filename):
                    self._append_image(f"Du -> {handle}", filename)
                else:
                    self._append_text("[Fehler] Datei nicht gefunden\n")

    def on_close(self):
        """Behandelt das Schließen des Fensters."""
        if self.joined:
            client_send_leave(self.config)
        self.destroy()

def startGui(config, net_to_interface, disc_to_interface, interface_to_net):
    """Startet die Chat-GUI."""
    app = ChatGUI(config, net_to_interface, disc_to_interface, interface_to_net)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()