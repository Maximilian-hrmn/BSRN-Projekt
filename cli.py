<<<<<<< HEAD
# File: chat_cli.py

import cmd
import threading
import time
import queue
from client import client_send_join, client_send_leave, client_send_who, client_send_msg, client_send_img

class ChatCLI(cmd.Cmd):
    intro = "Willkommen zum Peer-to-Peer Chat. Tippe 'help', um alle Befehle zu sehen."
    prompt = "> "

    def __init__(self, config, net_to_cli_queue, disc_to_cli_queue):
        super().__init__()
        self.config = config
        self.net_to_cli = net_to_cli_queue
        self.disc_to_cli = disc_to_cli_queue
        self.joined = False
        self.peers = {}

        # Thread, um eingehende Nachrichten und Peer-Updates abzuholen
        self._stop_event = threading.Event()
        self._poll_thread = threading.Thread(target=self._poll_queues, daemon=True)
        self._poll_thread.start()

    def _poll_queues(self):
        while not self._stop_event.is_set():
            try:
                msg = self.net_to_cli.get_nowait()
                if msg[0] == 'MSG':
                    print(f"\n[Nachricht von {msg[1]}]: {msg[2]}")
                elif msg[0] == 'IMG':
                    print(f"\n[Bild empfangen von {msg[1]}]: gespeichert als {msg[2]}")
                print(self.prompt, end='', flush=True)
            except queue.Empty:
                pass

            try:
                dmsg = self.disc_to_cli.get_nowait()
                if dmsg[0] == 'PEERS':
                    self.peers = dmsg[1]
            except queue.Empty:
                pass

            time.sleep(0.1)

    def do_join(self, arg):
        """join <username> <port>  –  Tritt dem Netzwerk bei."""
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
        client_send_join(self.config)
        self.joined = True
        print(f"Eingetreten als {handle} auf Port {port}")

    def do_leave(self, arg):
        """leave  –  Verlässt das Netzwerk."""
        if not self.joined:
            print("Du bist nicht eingeloggt.")
            return
        client_send_leave(self.config)
        self.joined = False
        print("Du hast das Netzwerk verlassen.")

    def do_who(self, arg):
        """who  –  Fragt die Peer-Liste ab und zeigt sie an."""
        if not self.joined:
            print("Zuerst 'join', bevor du 'who' ausführst.")
            return
        client_send_who(self.config)
        if not self.peers:
            print("Keine Peers gefunden.")
            return
        print("Bekannte Nutzer:")
        for h, (hhost, hport) in self.peers.items():
            print(f"  {h} @ {hhost}:{hport}")

    def do_msg(self, arg):
        """msg <user> <text>  –  Sendet eine Textnachricht an <user>."""
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

    def do_img(self, arg):
        """img <user> <pfad>  –  Sendet ein Bild an <user>."""
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
        print(self.config)

    def do_set_config(self, arg):
        """set_config <parameter> <wert>  –  Ändert einen Konfigurationsparameter."""
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
        print("Beende CLI…")
        self._stop_event.set()
        return True

    def default(self, line):
        """Fängt unbekannte Befehle ab und zeigt korrekte Syntax."""
        parts = line.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        valid_cmds = {
            'join': "Usage: join <username> <port>",
            'leave': "Usage: leave",
            'who': "Usage: who",
            'msg': "Usage: msg <user> <text>",
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
=======
import cmd  # Importiert das cmd-Modul für die Erstellung einer Command-Line-Interface (CLI)
import tomllib  # Wird benötigt zum Parsen von TOML-Dateien 
from discovery_service import DiscoveryService  # Importiert den DiscoveryService zur Peer-Erkennung
from slcp_handler import SLCPHandler  # Importiert die SLCPHandler-Klasse für Nachrichten-Handling

# Definiert die Klasse, die auf cmd basiert (stellt CLI-Funktionalität bereit)
class ChatCLI(cmd.Cmd):
    # Begrüßungstext beim Starten der CLI
    intro = "Willkommen zum P2P Chat! Tippe 'help' oder '?' für Befehle.\n"
    # Standard-Eingabeaufforderung (wird später überschrieben mit dem Benutzerhandle)
    prompt = "P2P-Chat: "

    # Konstruktor der CLI-Klasse
    def __init__(self, client):
        # Ruft den Konstruktor der Elternklasse (cmd.Cmd) auf
        super().__init__()

        # Lädt die Konfigurationsdaten aus der Datei config.toml
        self.config = self.load_config()
        self.client = client  # Der Client wird von außen übergeben (z. B. aus main.py)

        # Liest Handle (Benutzername) und Port aus der Konfiguration
        self.handle = self.config.get("handle")
        self.port = int(self.config.get("port", 0))  # Falls Port fehlt, wird 0 verwendet

        # Bricht ab, falls wichtige Parameter fehlen
        if not self.handle or not self.port:
            raise ValueError("Fehlende 'handle' oder 'port' Konfiguration.")

        # Setzt den Prompt in der CLI auf den Benutzernamen
        self.prompt = f"[{self.handle}]> "

        # Implementiert den SLCP Handler zum Senden/Empfangen von Nachrichten
        try:
            self.slcp_handler = SLCPHandler(handle=self.handle, port=self.port)
            print(f"[SLCP] Handler erstellt für Benutzer '{self.handle}' auf Port {self.port}")
        except Exception as e:
            print(f"[SLCP] Fehler beim Erstellen des Handlers: {e}")
            raise

    # Diese Methode lädt die Konfiguration aus der TOML-Datei
    def load_config(self):
        try:
            # Öffnet die Datei 'config.toml' im Binärmodus zum Lesen
            with open("config.toml", "rb") as f:
                # Lädt den Inhalt als Dictionary mit tomllib
                return tomllib.load(f)
        except FileNotFoundError:
            print("Konfigurationsdatei 'config.toml' nicht gefunden.")
            return {}
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            return {}

    # Diese Methode wird aufgerufen, wenn der Benutzer 'join' eingibt
    def do_join(self, arg):
        "Mit dem Chat verbinden: join"
        try:
            self.client.send_join(self.handle)
            print("Beitritt gesendet.")
        except Exception as e:
            print(f"Fehler beim Beitritt: {e}")

    # Diese Methode wird aufgerufen, wenn der Benutzer 'who' eingibt
    def do_who(self, arg):
        "Teilnehmer im Netzwerk entdecken: who"
        try:
            discovery_service = DiscoveryService()  # Erstellt einen neuen DiscoveryService
            peers = discovery_service.discover_peers()  # Ruft bekannte Peers ab
            if peers:
                print("Gefundene Peers:")
                for peer in peers:
                    # Fragt WHO-Informationen von jedem Peer ab
                    info = discovery_service.send_who(peer)
                    if info:
                        print(f"  - {peer}: {info}")
                    else:
                        print(f"  - {peer}: Keine Antwort.")
            else:
                print("Keine Peers gefunden.")
        except Exception as e:
            print(f"Fehler bei WHO-Abfrage: {e}")

    # Diese Methode wird aufgerufen, wenn der Nutzer "msg <Text>" eintippt
    def do_msg(self, arg):
        "Nachricht senden: msg <Text>"
        if not arg.strip():
            print("Benutzung: msg <Text>")
            return
        try:
            self.client.send_msg(arg)  # Sendet Nachricht über den Client
        except Exception as e:
            print(f"Fehler beim Senden der Nachricht: {e}")

    # Diese Methode wird aufgerufen, wenn der Nutzer 'leave' eintippt
    def do_leave(self, arg):
        "Den Chat verlassen: leave"
        try:
            self.client.send_leave()  # Sendet LEAVE-Nachricht an andere
            print("Verlassen gesendet.")
            return True  # Beendet die CLI
        except Exception as e:
            print(f"Fehler beim Verlassen: {e}")

    # Zeigt die aktuell geladene Konfiguration aus config.toml an
    def do_config(self, arg):
        "Zeige aktuelle Konfiguration"
        for key, value in self.config.items():
            print(f"{key} = {value}")

    # Erweiterungsmöglichkeit: Bild versenden (auskommentiert)
    # def do_img(self, arg):
    #     "Bild senden: img <Benutzer> <Dateipfad>"
    #     try:
    #         user, filepath = arg.split(" ", 1)
    #         self.client.send_img(user, filepath)
    #     except ValueError:
    #         print("Benutzung: img <Benutzer> <Dateipfad>")
>>>>>>> e3e3d87472a639b4ced2beef1075e7f250613fe1
