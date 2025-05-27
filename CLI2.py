import cmd  # Importiert das cmd-Modul für die Erstellung einer Command-Line-Interface (CLI)
import tomllib  # Wird benötigt zum Parsen von TOML-Dateien (ab Python 3.11 Standard)
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
