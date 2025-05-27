import cmd #Importiert das cmd-Modul für die CLI 
from discovery_service import DiscoveryService#Importiert die disovery_servive Datei, wird benötigt für die WHO abfrage 
import tomllib #benötigt zum Parsen von TOML-Datein 
from slcp_handler import SLCPHandler  # Importiere SLCPHandler-Klasse

#Definiert die Klasse die auf cmd basiert (stellt CLI Funktionalität bereit)
class ChatCLI(cmd.Cmd):
    #Begrüßungstext 
    intro = "Willkommen zum P2P Chat! Tippe 'help' oder '?' für Befehle. \n" 
    #Eingabeaufforderung
    prompt = "P2P-Chat: "

    #Konstruktor von der Klasse CLI 
    def __init__(self,client): 
        #Ruft den Konstuktor der Elternklasse auf (cmd)
        super().__init__() 
        #Lädt die Konfiguartionsdaten aus der Datei (TOML)
        self.config = self.load_config()
        self.client = client

        #Prüft, ob 'handle' in der Konfiguration vorhanden ist wenn nicht, bricht das Programm mit Fehlermeldung ab
        if "handle" not in self.config:
            raise ValueError("Fehlender 'handle' in config.toml")

        #Prüft, ob 'port' vorhanden ist – andernfalls Abbruch
        if "port" not in self.config:
            raise ValueError("Fehlender 'port' in config.toml")
        #Setz den Prompt auf den Benutzernamen 
        self.handle = self.config["handle"]
        self.port = int(self.config["port"])
        self.prompt = f"[{self.handle}]> "
        
        #Implementation des SLCP Handler 
        try:
            self.slcp_handler = SLCPHandler(handle=self.handle, port=self.port)
            print(f"[SLCP] Handler erstellt für Benutzer '{self.handle}' auf Port {self.port}")    
        except Exception as e:
            print(f"[SLCP] Fehler beim Erstellen des Handlers: {e}")
            raise

    #Diese Funktion lädt die Konfiguration aus der TOML-Datei
    def load_config(self):
        #Öffnet die Datei 'config.toml' im Binärmodus zum Lesen
        with open("config.toml", "rb") as f:
            #Lädt den Inhalt als Dictionary mit tomllib
            return tomllib.load(f)

    def do_join(self, arg):
        "Mit dem Chat verbinden: join"
        if not self.handle:
            print("Kein Handle gesetzt.")
            return
        self.client.send_join(self.handle) 

    def do_who(self, arg):
        """Teilnehmer im Netzwerk entdecken"""
        discovery_service = DiscoveryService()
        peers = discovery_service.discover_peers()
        if peers:
            print("Gefundene Peers:")
            for peer in peers:
                # Korrekter Aufruf von send_who mit nur einem Parameter
                info = discovery_service.send_who(peer)  # peer ist die Adresse
                if info:
                    print(f"  - {peer}: {info}")
        else:
            print("Keine Peers gefunden.")

    # Diese Methode wird aufgerufen, wenn der Nutzer "msg <Benutzer> <Text>" eintippt
    def do_msg(self, arg):
        "Nachricht senden: msg <Text>"
        if not arg.strip():
            print("Benutzung: msg <Text>")
            return
        self.client.send_msg(arg)


    # Diese Methode wird aufgerufen, wenn der Nutzer "leave" eingibt
    def do_leave(self, arg):
        "Den Chat verlassen"
        self.client.send_leave()
        return True

    # Zeigt die aktuelle Konfiguration an
    def do_config(self, arg):
        "Zeige aktuelle Konfiguration"
        for key, value in self.config.items():
            print(f"{key} = {value}") 
    
    # #Wenn der benutzer "img" einigbt wird ein Bild gesendet 
    # def do_img(self, arg):
    #     "Bild senden: img <Benutzer> <Dateipfad>"
    #     try:
    #         user, filepath = arg.split(" ", 1)
    #         client.send_img(user, filepath)
    #     except ValueError:
    #         print("Benutzung: img <Benutzer> <Dateipfad>")

