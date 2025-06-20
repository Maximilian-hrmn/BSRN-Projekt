import tkinter as tk
from tkinter import simpledialog, filedialog
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
        self.entry.bind("<Return>", self._send_message)

    def _join_network(self):
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

    def on_close(self):
        if getattr(self, "joined", False):
            client_send_leave(self.config)
        self.destroy()


def startGui(config, net_to_cli, disc_to_cli, cli_to_net):
    app = ChatGUI(config, net_to_cli, disc_to_cli, cli_to_net)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
