import tkinter as tk
from tkinter import simpledialog, filedialog
import queue
import time
import sys

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
        port = simpledialog.askinteger(
            "Port",
            "Bitte gib deinen Port ein:",
            parent=self,
            initialvalue=5000,
            minvalue=1024,
            maxvalue=65535,
        )
        if port:
            self.config.setdefault("network", {})["port"] = port

    def _setup_ui(self):
        self.title("Messenger")
        self.geometry("800x600")

        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        chat_frame = tk.Frame(list_frame)
        chat_frame.pack(side="left", fill="both", expand=True)

        chat_scroll = tk.Scrollbar(chat_frame)
        chat_scroll.pack(side="right", fill="y")

        self.chat_list = tk.Listbox(
            chat_frame, yscrollcommand=chat_scroll.set, font=("Helvetica", 11)
        )
        self.chat_list.pack(side="left", fill="both", expand=True)
        chat_scroll.config(command=self.chat_list.yview)

        peer_frame = tk.Frame(list_frame)
        peer_frame.pack(side="right", fill="y")

        peer_scroll = tk.Scrollbar(peer_frame)
        peer_scroll.pack(side="right", fill="y")

        self.peer_list = tk.Listbox(
            peer_frame, yscrollcommand=peer_scroll.set, width=20, font=("Helvetica", 11)
        )
        self.peer_list.pack(side="left", fill="y")
        peer_scroll.config(command=self.peer_list.yview)

        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=5)

        self.text_entry = tk.Text(bottom_frame, height=3, font=("Helvetica", 11))
        self.text_entry.pack(side="left", fill="both", expand=True)

        self.image_btn = tk.Button(bottom_frame, text="📷", width=4, command=self.open_image_dialog)
        self.image_btn.pack(side="left", padx=(5, 0))

        self.send_btn = tk.Button(bottom_frame, text="Senden", width=10, command=self._send_message)
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
                self.chat_list.insert("end", f"{from_handle}: {text}")
                self.chat_list.yview_moveto(1)
            elif msg[0] == "IMG":
                from_handle = msg[1]
                path = msg[2]
                self.chat_list.insert("end", f"[Bild von {from_handle}] {path}")
                self.chat_list.yview_moveto(1)
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

    def _send_message(self):
        self.last_activity = time.time()
        text = self.text_entry.get("1.0", "end").strip()
        if not text:
            return
        sel = self.peer_list.curselection()
        if not sel:
            return
        handle = self.peer_list.get(sel[0])
        if handle in self.peers:
            host, port = self.peers[handle]
            client_send_msg(host, port, self.config["handle"], text)
            self.chat_list.insert("end", f"[Du -> {handle}] {text}")
            self.chat_list.yview_moveto(1)
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
                    self.chat_list.insert(
                        "end", f"[Du -> {handle}] Bild gesendet: {filename}"
                    )
                    self.chat_list.yview_moveto(1)

    def on_close(self):
        if self.joined:
            client_send_leave(self.config)
        self.destroy()


def startGui(config, net_to_cli, disc_to_cli, cli_to_net):
    app = ChatGUI(config, net_to_cli, disc_to_cli, cli_to_net)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
