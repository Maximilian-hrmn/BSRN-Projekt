import cmd  # Importiert das cmd-Modul für die CLI
import client  # Importiert die Client.py Datei, wird benötigt für send und leave
from discovery_service import DiscoveryService  # Importiert die discovery_service Datei, wird benötigt für die WHO-Abfrage
import tomllib  # benötigt zum Parsen von TOML-Dateien
from slcp_handler import SLCPHandler  # Importiere SLCPHandler-Klasse
from client import SLCPClient  # SLCPClient zum Senden von JOIN verwenden

class ChatCLI(cmd.Cmd):
    intro = "Willkommen zum P2P Chat! Tippe 'help' oder '?' für Befehle. \n"
    prompt = "P2P-Chat: "

    def __init__(self):
        super().__init__()
        self.config = self.load_config()

        if "handle" not in self.config:
            raise ValueError("Fehlender 'handle' in config.toml")
        if "port" not in self.config:
            raise ValueError("Fehlender 'port' in config.toml")

        self.handle = self.config["handle"]
        self.port = int(self.config["port"])
        self.prompt = f"[{self.handle}]> "

        # # === automatischer JOIN ===
        # # Erzeuge JOIN-Nachricht mit SLCPHandler
        # self.slcp_handler = SLCPHandler(handle=self.handle, port=self.port)
        # join_message = self.slcp_handler.create_join()

        # # Lese Bootstrap-Peer aus der Konfiguration
        # bootstrap_ip = self.config["peer_ip"]
        # bootstrap_port = int(self.config["peer_port"])

        # # Sende JOIN an den Bootstrap-Peer
        # slcp_client = SLCPClient(bootstrap_ip, bootstrap_port)
        # response = slcp_client.send_message(join_message.strip())
        # print(f"[SLCP] JOIN an {bootstrap_ip}:{bootstrap_port} gesendet.")
        # print(f"[SLCP] Antwort: {response}")
        # # === Ende automatischer JOIN ===

    def load_config(self):
        with open("config.toml", "rb") as f:
            return tomllib.load(f)

    def do_who(self, arg):
        """Teilnehmer im Netzwerk entdecken"""
        discovery_service = DiscoveryService()
        peers = discovery_service.discover_peers()
        if peers:
            print("Gefundene Peers:")
            for peer in peers:
                info = discovery_service.send_who(peer)
                if info:
                    print(f"  - {peer}: {info}")
        else:
            print("Keine Peers gefunden.")

    def do_msg(self, arg):
        "Nachricht senden: msg <Benutzer> <Text>"
        try:
            user, message = arg.split(" ", 1)
            client.send_msg(user, message)
        except ValueError:
            print("Benutzung: msg <Benutzer> <Text>")

    def do_leave(self, arg):
        "Den Chat verlassen"
        client.send_leave(self.handle)
        print("Verlassen...")
        return True

    def do_config(self, arg):
        "Zeige aktuelle Konfiguration"
        for key, value in self.config.items():
            print(f"{key} = {value}")

    def do_exit(self, arg):
        "Programm beenden"
        return self.do_leave(arg)
