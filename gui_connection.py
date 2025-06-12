import threading
import queue

class GuiBridge:
    """
    Brücke zwischen GUI und Backend (Chat, Discovery, Netzwerk).
    """
    def __init__(self, config, net_to_gui_queue, disc_to_gui_queue):
        self.config = config
        self.net_to_gui = net_to_gui_queue
        self.disc_to_gui = disc_to_gui_queue
        self.peers = {}
        self.chat_history = []
        self._stop_event = threading.Event()
        self._poll_thread = threading.Thread(target=self._poll_queues, daemon=True)
        self._poll_thread.start()

    def _poll_queues(self):
        while not self._stop_event.is_set():
            try:
                msg = self.net_to_gui.get_nowait()
                if msg[0] == 'MSG':
                    self.chat_history.append((msg[1], msg[2]))
                    self.on_new_message(msg[1], msg[2])
                elif msg[0] == 'IMG':
                    self.chat_history.append((msg[1], f"[Bild: {msg[2]}]"))
                    self.on_new_image(msg[1], msg[2])
            except queue.Empty:
                pass

            try:
                dmsg = self.disc_to_gui.get_nowait()
                if dmsg[0] == 'PEERS':
                    self.peers = dmsg[1]
                    self.on_peers_update(self.peers)
            except queue.Empty:
                pass

    # Diese Methoden kannst du in deiner GUI überschreiben/verbinden:
    def on_new_message(self, from_user, text):
        """Wird aufgerufen, wenn eine neue Nachricht empfangen wurde."""
        pass

    def on_new_image(self, from_user, image_path):
        """Wird aufgerufen, wenn ein Bild empfangen wurde."""
        pass

    def on_peers_update(self, peers):
        """Wird aufgerufen, wenn sich die Peerliste ändert."""
        pass

    # Methoden für die GUI-Buttons:
    def send_message(self, to_user, text):
        from client import client_send_msg
        if to_user in self.peers:
            thost, tport = self.peers[to_user]
            client_send_msg(thost, tport, self.config['handle'], text)

    def send_image(self, to_user, image_path):
        from client import client_send_img
        if to_user in self.peers:
            thost, tport = self.peers[to_user]
            client_send_img(thost, tport, self.config['handle'], image_path)

    def join_network(self, handle, port):
        from client import client_send_join
        self.config['handle'] = handle
        self.config['port'] = port
        client_send_join(self.config)

    def leave_network(self):
        from client import client_send_leave
        client_send_leave(self.config)

    def request_peers(self):
        from client import client_send_who
        client_send_who(self.config)

    def stop(self):
        self._stop_event.set()