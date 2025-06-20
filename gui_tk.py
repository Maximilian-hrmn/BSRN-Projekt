import tkinter as tk
from tkinter import simpledialog, filedialog
from PIL import Image, ImageTk
import queue
import time
import sys
import socket

from client import (
    client_send_join,
    client_send_leave,
    client_send_msg,
    client_send_img,
    client_send_who,
)

AWAY_TIMEOUT = 30


class ChatGUI(tk.Tk):
    def __init__(self, config, net_to_cli, disc_to_cli, cli_to_net):
        super().__init__()
        self.config = config
        self.net_to_cli = net_to_cli
        self.disc_to_cli = disc_to_cli
        self.cli_to_net = cli_to_net
        self.peers = {}
        self.last_activity = time.time()
        self.joined = False
        self._ask_user_info()
        self._setup_ui()
        self._join_network()
        self._poll_queues()

    def _ask_user_info(self):
        name = simpledialog.askstring("Name", "Bitte gib deinen Namen ein:", parent=self)
        if name:
            self.config.setdefault("user", {})["name"] = name

        # Automatisch einen freien TCP-Port wählen anstatt den Nutzer zu fragen
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

    
    def _send_message(self):
        self.last_activity = time.time()
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            return

        # Erlaube die bekannte CLI-Syntax wie "msg <user> <text>" oder
        # "img <user> <pfad>" direkt im Eingabefeld. Weitere Befehle wie
        # "msg all", "who", "leave" und "help" werden ebenfalls interpretiert.
        if text.startswith("msg "):
            parts = text.split(" ", 2)
            if len(parts) == 3:
                handle, message = parts[1], parts[2]
                if handle in self.peers:
                    host, port = self.peers[handle]
                    try:
                        client_send_msg(host, port, self.config["handle"], message)
                        self._append_text(f"[Du -> {handle}] {message}\n")
                    except OSError as e:
                        self._append_text(f"[Fehler] {e}\n")
                else:
                    self._append_text("[Fehler] Unbekannter Nutzer\n")
            else:
                self._append_text("[Fehler] Syntax: msg <user> <text>\n")
            self.text_entry.delete("1.0", "end")
            return

        if text.startswith("msgall ") or text.startswith("msg all "):
            message = text.split(" ", 1)[1].split(" ", 1)[1] if text.startswith("msg all ") else text.split(" ", 1)[1]
            if not self.peers:
                self._append_text("[Fehler] Keine anderen Peers\n")
            else:
                for h, (host, port) in self.peers.items():
                    try:
                        client_send_msg(host, port, self.config["handle"], message)
                    except OSError as e:
                        self._append_text(f"[Fehler] zu {h}: {e}\n")
                self._append_text(f"[Du -> alle] {message}\n")
            self.text_entry.delete("1.0", "end")
            return

        if text.startswith("img "):
            parts = text.split(" ", 2)
            if len(parts) == 3:
                handle, path = parts[1], parts[2]
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
            self.text_entry.delete("1.0", "end")
            return

        if text == "who":
            client_send_who(self.config)
            self.chat_text.configure(state="normal")
            self._append_text("[Info] Peer-Liste angefordert\n")
            self.text_entry.delete("1.0", "end")
            return

        if text == "leave":
            if self.joined:
                client_send_leave(self.config)
                self.joined = False
                self._append_text("[Info] Netzwerk verlassen\n")
            else:
                self._append_text("[Info] Nicht im Netzwerk\n")
            self.text_entry.delete("1.0", "end")
            return

        if text == "help":
            self._append_text(
                "Befehle: msg <user> <text>, msgall <text>, img <user> <pfad>, who, leave, help\n"
            )
            self.text_entry.delete("1.0", "end")
            return

        sel = self.peer_list.curselection()
        if not sel:
            return
        handle = self.peer_list.get(sel[0])
        if handle in self.peers:
            host, port = self.peers[handle]
            try:
                client_send_msg(host, port, self.config["handle"], text)
                self._append_text(f"[Du -> {handle}] {text}\n")
            except OSError as e:
                self._append_text(f"[Fehler] {e}\n")
        self.text_entry.delete("1.0", "end")

    def _send_message_event(self, event):
        self._send_message()
        return "break"

    def open_image_dialog(self):
        sel = self.peer_list.curselection()
        if not sel:
            return
        filename = filedialog.askopenfilename(
            title="Bild auswählen",
            filetypes=[("Bilder", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )
        if filename:
            handle = self.peer_list.get(sel[0])
            if handle in self.peers:
                host, port = self.peers[handle]
                if client_send_img(host, port, self.config["handle"], filename):
                    self._append_image(f"Du -> {handle}", filename)
                else:
                    self._append_text("[Fehler] Datei nicht gefunden\n")

    def on_close(self):
        if self.joined:
            client_send_leave(self.config)
        self.destroy()


def startGui(config, net_to_cli, disc_to_cli, cli_to_net):
    app = ChatGUI(config, net_to_cli, disc_to_cli, cli_to_net)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

