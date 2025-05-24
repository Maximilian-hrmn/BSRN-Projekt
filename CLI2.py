import cmd #Importiert das cmd-Modul für die CLI 
import client #Importiert die Client.py Datei, wird benötigt für send und leave 
import discovery_service #Importiert die disovery_servive Datei, wird benötigt für die WHO abfrage 
import tomllib #benötigt zum Parsen von TOML-Datein 

#Definiert die Klasse die auf cmd basiert (stellt CLI Funktionalität bereit)
class CLI(cmd.Cmd):
    #Begrüßungstext 
    anfang = "Willkomen zum P2P Chat! Tippe 'help' oder '?' für Befehle. \n" 
    #Eingabeaufforderung
    promt = "P2P-Chat: "

    #Konstruktor von der Klasse CLI 
    def __init__(self): 
        #Ruft den Konstuktor der Elternklasse auf (cmd)
        super().__init__() 
        #Lädt die Konfiguartionsdaten aus der Datei (TOML)
        self.config = self.load_config()

        #Prüft, ob 'handle' in der Konfiguration vorhanden ist – wenn nicht, bricht das Programm mit Fehlermeldung ab
        if "handle" not in self.config:
            raise ValueError("Fehlender 'handle' in config.toml")

        #Prüft, ob 'port' vorhanden ist – andernfalls Abbruch
        if "port" not in self.config:
            raise ValueError("Fehlender 'port' in config.toml")
        #Setz den Prompt auf den Benutzernamen 
        self.prompt = f"[{self.handle}]> "
        
        #HIER NOCH DIE JOIN NACHRICHT MACHEN!!!!!



    #Diese Funktion lädt die Konfiguration aus der TOML-Datei
    def load_config(self):
        #Öffnet die Datei 'config.toml' im Binärmodus zum Lesen
        with open("config.toml", "rb") as f:
            #Lädt den Inhalt als Dictionary mit tomllib
            return tomllib.load(f)
        
    def do_who(self, arg):
        "Teilnehmer im Netzwerk entdecken"
        discovery_service.send_who()  # Ruft eure Funktion aus discovery_service.py auf MUSS MARIUS IN SEINEM CODE MACHEN







#HIER WEITERARBEITEN 

    # Diese Methode wird aufgerufen, wenn der Nutzer "msg <Benutzer> <Text>" eintippt
    def do_msg(self, arg):
        "Nachricht senden: msg <Benutzer> <Text>"
        try:
            # Zerlegt den String in zwei Teile: Empfänger und Nachricht
            user, message = arg.split(" ", 1)
            # Schickt die Nachricht mit Hilfe eurer client.py
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

# Startet das CLI, wenn das Skript direkt ausgeführt wird
if __name__ == '__main__':
    ChatCLI().cmdloop()  # Startet die Eingabeschleife für die Kommandozeile