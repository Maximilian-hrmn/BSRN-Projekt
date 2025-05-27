import cmd #Importiert das cmd-Modul für die CLI 
import client #Importiert die Client.py Datei, wird benötigt für send und leave 
from discovery_service import DiscoveryService#Importiert die disovery_servive Datei, wird benötigt für die WHO abfrage 
import tomllib #benötigt zum Parsen von TOML-Datein 
from slcp_handler import SLCPHandler  # Importiere SLCPHandler-Klasse
from client import SLCPClient

#Definiert die Klasse die auf cmd basiert (stellt CLI Funktionalität bereit)
class ChatCLI(cmd.Cmd):
    #Begrüßungstext 
    intro = "Willkommen zum P2P Chat! Tippe 'help' oder '?' für Befehle. \n" 
    #Eingabeaufforderung
    prompt = "P2P-Chat: "

    #Konstruktor von der Klasse CLI 
    def __init__(self): 
        #Ruft den Konstuktor der Elternklasse auf (cmd)
        super().__init__() 
        #Lädt die Konfiguartionsdaten aus der Datei (TOML)
        self.config = self.load_config()

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
        
        # #HIER NOCH DIE JOIN NACHRICHT MACHEN!!!!!

        #     # === automatischer JOIN ===
        # bootstrap_ip   = self.config["peer_ip"]      # aus config.toml
        # bootstrap_port = int(self.config["peer_port"])

        # # SLCPClient initialisieren und JOIN senden
        # slcp_client = SLCPClient(bootstrap_ip, bootstrap_port)
        # response = slcp_client.send_message(join_message.strip())

        # print(f"[SLCP] JOIN an {bootstrap_ip}:{bootstrap_port} gesendet.")
        # print(f"[SLCP] Antwort: {response}")
        # # === Ende automatischer JOIN ===

        #Implementation des SLCP Handler 
        try:
            self.slcp_handler = SLCPHandler(handle=self.handle, port=self.port)
            print(f"[SLCP] Handler erstellt für Benutzer '{self.handle}' auf Port {self.port}")
            
            # Sende JOIN-Nachricht beim Start
            join_message = self.slcp_handler.create_join()
            print(f"[SLCP] JOIN-Nachricht bereit: {join_message.strip()}")
            # Hier könntest du die JOIN-Nachricht an entdeckte Peers senden
            
        except ValueError as e:
            print(f"[SLCP] Fehler beim Erstellen des Handlers: {e}")
            raise
                

    #Diese Funktion lädt die Konfiguration aus der TOML-Datei
    def load_config(self):
        #Öffnet die Datei 'config.toml' im Binärmodus zum Lesen
        with open("config.toml", "rb") as f:
            #Lädt den Inhalt als Dictionary mit tomllib
            return tomllib.load(f)
        
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
        "Nachricht senden: msg <Benutzer> <Text>"
        try:
            # Zerlegt den String in zwei Teile: Empfänger und Nachricht
            user, message = arg.split(" ", 1)
            # Schickt die Nachricht mit Hilfe der client.py
            client.send_msg(user, message)
        except ValueError:
            # Falls der Benutzer das Kommando falsch verwendet
            print("Benutzung: msg <Benutzer> <Text>")

    # Diese Methode wird aufgerufen, wenn der Nutzer "leave" eingibt
    def do_leave(self, arg):
        "Den Chat verlassen"
        # Sendet die LEAVE-Nachricht über client.py
        client.send_leave(self.handle)
        print("Verlassen...")
        return True  # Beendet das CLI-Programm

    # Zeigt die aktuelle Konfiguration an
    def do_config(self, arg):
        "Zeige aktuelle Konfiguration"
        for key, value in self.config.items():
            print(f"{key} = {value}")

    # Wenn der Nutzer "exit" eingibt, wird 'leave' aufgerufen und das Programm beendet
    def do_exit(self, arg):
        "Programm beenden"
        return self.do_leave(arg)  
    
    # #Wenn der benutzer "img" einigbt wird ein Bild gesendet 
    # def do_img(self, arg):
    #     "Bild senden: img <Benutzer> <Dateipfad>"
    #     try:
    #         user, filepath = arg.split(" ", 1)
    #         client.send_img(user, filepath)
    #     except ValueError:
    #         print("Benutzung: img <Benutzer> <Dateipfad>")

