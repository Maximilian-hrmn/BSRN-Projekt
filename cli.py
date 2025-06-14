# impotieret das cmd Modul für die Kommandozeilen-Interface (CLI) und andere benötigte Module
import cmd
# Importiere die benötigten Module für Netzwerkkommunikation und Threading
import threading
# Importiere die Zeit- und Queue-Module für Zeitmanagement und Thread-Synchronisation
import time
import queue
# Importiere die Client-Funktionen für Netzwerkkommunikation
from client import client_send_join, client_send_leave, client_send_who, client_send_msg, client_send_img
# 30 Sekunden Inaktivität, bevor Auto-Reply ausgelöst wird
AWAY_TIMEOUT = 30 

#Main-Klasse für die Kommandozeilen-Schnittstelle des Peer-to-Peer Chats, erbt von cmd.Cmd ab
class ChatCLI(cmd.Cmd):
#autotmatische Begrüßung und Eingabeaufforderung
    intro = "Willkommen zum Peer-to-Peer Chat. Tippe 'help', um alle Befehle zu sehen."
    prompt = "> "
# Konstruktor der ChatCLI-Klasse, initialisiert die Konfiguration und IPC-Queues
    def __init__(self, config, net_to_cli_queue, disc_to_cli_queue, cli_to_net_queue):
        super().__init__()
        self.config = config
        self.net_to_cli = net_to_cli_queue
        self.disc_to_cli = disc_to_cli_queue
        self.cli_to_net = cli_to_net_queue
        self.joined = False
        self.peers = {}

        # Zeitpunkt der letzten Nutzeraktivität (zur Auto-Reply-Erkennung)
        self.last_activity = time.time()

        # Thread, um eingehende Nachrichten und Peer-Updates abzuholen
        self._stop_event = threading.Event()
        self._poll_thread = threading.Thread(target=self._poll_queues, daemon=True)
        self._poll_thread.start()

    def _poll_queues(self):
        while not self._stop_event.is_set():
            now = time.time()

            # 1. Eingehende Chat-Nachrichten abholen
            try:
                msg = self.net_to_cli.get_nowait()
                if msg[0] == 'MSG':
                    from_handle = msg[1]
                    text = msg[2]

                    # Auto-Reply, falls Nutzer länger als AWAY_TIMEOUT “away” ist
                    if now - self.last_activity > AWAY_TIMEOUT and self.joined:
                        # Die Auto-Reply-Nachricht aus der Konfigurationsdatei auslesen
                        # (siehe config.toml: autoreply = "…") :contentReference[oaicite:0]{index=0}
                        auto_msg = self.config.get('autoreply', None)
                        if auto_msg and from_handle in self.peers:
                            thost, tport = self.peers[from_handle]
                            client_send_msg(thost, tport, self.config['handle'], auto_msg)

                    # Ausgabe der eigentlichen Nachricht
                    print(f"\n[Nachricht von {from_handle}]: {text}")

                elif msg[0] == 'IMG':
                    from_handle = msg[1]
                    filepath = msg[2]
                    print(f"\n[Bild empfangen von {from_handle}]: gespeichert als {filepath}")

                # Prompt wieder anzeigen
                print(self.prompt, end='', flush=True)

            except queue.Empty:
                pass

            # 2. Updates der Peer-Liste abholen
            try:
                dmsg = self.disc_to_cli.get_nowait()
                if dmsg[0] == 'PEERS':
                    self.peers = dmsg[1]
            except queue.Empty:
                pass

            time.sleep(0.1)

    # … alle do_*-Methoden setzen self.last_activity zurück (nicht verändert) …

    def do_join(self, arg):
        """join <username> <port>  –  Tritt dem Netzwerk bei."""
        self.last_activity = time.time()
        if self.joined:
            print("Du bist bereits eingeloggt. Zuerst 'leave', bevor du 'join' ausführst.")
            return
        parts = arg.split()
        if len(parts) != 2:
            print("Usage: join <username> <port>")
            return
        handle, port_str = parts
        try:
            port = int(port_str)
        except ValueError:
            print("Port muss eine Zahl sein.")
            return
        self.config['handle'] = handle
        self.config['port'] = port
        if self.cli_to_net:
            self.cli_to_net.put(('SET_PORT', port))
        client_send_join(self.config)
        self.joined = True
        print(f"Eingetreten als {handle} auf Port {port}")

    def do_leave(self, arg):
        """leave  –  Verlässt das Netzwerk."""
        self.last_activity = time.time()
        if not self.joined:
            print("Du bist nicht eingeloggt.")
            return
        client_send_leave(self.config)
        self.joined = False
        print("Du hast das Netzwerk verlassen.")

    def do_who(self, arg):
        """who  –  Fragt die Peer-Liste ab und zeigt sie an."""
        self.last_activity = time.time()
        if not self.joined:
            print("Zuerst 'join', bevor du 'who' ausführst.")
            return
        client_send_who(self.config)
        time.sleep(0.2)
        if not self.peers:
            print("Keine Peers gefunden.")
            return
        print("Bekannte Nutzer:")
        for h, (hhost, hport) in self.peers.items():
            print(f"  {h} @ {hhost}:{hport}")

    def do_msg(self, arg):
        """msg <user> <text>  –  Sendet eine Textnachricht an <user>."""
        self.last_activity = time.time()
        if not self.joined:
            print("Zuerst 'join', bevor du 'msg' ausführst.")
            return
        parts = arg.split(" ", 1)
        if len(parts) != 2:
            print("Usage: msg <user> <text>")
            return
        target, text = parts
        if target in self.peers:
            thost, tport = self.peers[target]
            client_send_msg(thost, tport, self.config['handle'], text)
        else:
            print("Unbekannter Nutzer.")

    def do_msgall(self, arg):
        """msgall <text>  –  Sendet eine Textnachricht an alle aktuell im Chat befindlichen Nutzer."""
        self.last_activity = time.time()
        if not self.joined:
            print("Zuerst 'join', bevor du 'msgall' ausführst.")
            return
        text = arg.strip()
        if not text:
            print("Usage: msgall <text>")
            return
        if not self.peers:
            print("Keine anderen Peers im Chat.")
            return

        for peer_handle, (phost, pport) in self.peers.items():
            try:
                client_send_msg(phost, pport, self.config['handle'], text)
            except Exception as e:
                print(f"Fehler beim Senden an {peer_handle}: {e}")
        print("Nachricht an alle gesendet.")

    def do_img(self, arg):
        """img <user> <pfad>  –  Sendet ein Bild an <user>."""
        self.last_activity = time.time()
        if not self.joined:
            print("Zuerst 'join', bevor du 'img' ausführst.")
            return
        parts = arg.split(" ", 1)
        if len(parts) != 2:
            print("Usage: img <user> <pfad>")
            return
        target, path = parts
        if target in self.peers:
            thost, tport = self.peers[target]
            success = client_send_img(thost, tport, self.config['handle'], path)
            if not success:
                print("Datei nicht gefunden.")
        else:
            print("Unbekannter Nutzer.")

    def do_show_config(self, arg):
        """show_config  –  Zeigt die aktuelle Konfiguration an."""
        self.last_activity = time.time()
        print(self.config)

    def do_set_config(self, arg):
        """set_config <parameter> <wert>  –  Ändert einen Konfigurationsparameter."""
        self.last_activity = time.time()
        parts = arg.split(" ", 1)
        if len(parts) != 2:
            print("Usage: set_config <parameter> <wert>")
            return
        key, val = parts
        if key not in self.config:
            print("Unbekannter Konfigurationsparameter.")
            return
        if isinstance(self.config[key], int):
            try:
                val = int(val)
            except ValueError:
                print("Wert muss eine Zahl sein.")
                return
        self.config[key] = val
        print(f"Konfig {key} = {val}")

    def do_exit(self, arg):
        """exit  –  Beendet CLI und Hintergrund-Thread."""
        self.last_activity = time.time()
        print("Beende CLI…")
        self._stop_event.set()
        return True

    def default(self, line):
        """Fängt unbekannte Befehle ab und zeigt korrekte Syntax."""
        self.last_activity = time.time()
        parts = line.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        valid_cmds = {
            'join': "Usage: join <username> <port>",
            'leave': "Usage: leave",
            'who': "Usage: who",
            'msg': "Usage: msg <user> <text>",
            'msgall': "Usage: msgall <text>",
            'img': "Usage: img <user> <pfad>",
            'show_config': "Usage: show_config",
            'set_config': "Usage: set_config <parameter> <wert>",
            'help': "Usage: help",
            'exit': "Usage: exit"
        }
        if cmd in valid_cmds:
            print(valid_cmds[cmd])
        else:
            print(f"Unbekannter Befehl: '{parts[0]}'. Tippe 'help' für gültige Befehle.")

    def do_help(self, arg):
        return super().do_help(arg)
