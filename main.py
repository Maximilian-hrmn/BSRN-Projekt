# File: main.py

import argparse # ArgumentParser für Kommandozeilenargumente
import toml # Zum Laden der Konfigurationsdatei
from multiprocessing import Process, Queue # Multiprocessing für parallele Prozesse
import discovery_service # Discovery-Service für Peer-Erkennung
import server # Server-Modul für Netzwerkkommunikation
from cli import ChatCLI # CLI-Modul für Kommandozeileninteraktion

"""
@file main.py
@brief Main Entry Point:

- Lädt config.toml
- Startet im Hintergrund jeweils:
    * Discovery-Service (Process A)
    * Server/Network-Empfang (Process B)
- Anschließend startet CLI (ChatCLI) oder GUI (je nach Eingabe) im Hauptprozess
"""

if __name__ == '__main__': # main.py wird direkt ausgeführt
    """Main-Block, um das Skript direkt auszuführen"""
    parser = argparse.ArgumentParser(description="Start chat client") # Initialisiert Kommandozeilenparser für Port und Broadcast-Optionen
    parser.add_argument("--port", type=int, help="UDP port for this client") # Port für den Client
    parser.add_argument("--broadcast", help="Broadcast address for discovery") # Broadcast-Adresse für Discovery
    parser.add_argument("--whoisport", type=int, help="Port for discovery service") # Port für den Discovery-Service
    args = parser.parse_args() # Argumente parsen

    config = toml.load('config.toml') # Konfiguration aus config.toml laden
    if args.port is not None: # Wenn ein Port angegeben wurde, diesen verwenden
        config['port'] = args.port # Port in der Konfiguration setzen
    else: # Wenn kein Port angegeben wurde, auf 0 setzen
        config['port'] = 0 # 0 bedeutet, dass der OS einen freien Port wählen soll
    if args.broadcast: # Wenn eine Broadcast-Adresse angegeben wurde
        config['broadcast'] = args.broadcast # Broadcast-Adresse in der Konfiguration setzen
    if args.whoisport: # Wenn ein Port für den Discovery-Service angegeben wurde
        config['whoisport'] = args.whoisport # Port für den Discovery-Service in der Konfiguration setzen
    

    """IPC-Queues (für Prozesskommunikation zwischen CLI, Server und Discovery)"""
    interface_to_net = Queue() # Queue für Kommunikation von CLI zu Netzwerk
    interface_to_disc = Queue() # Queue für Kommunikation von CLI zu Discovery
    net_to_interface = Queue() # Queue für Kommunikation von Netzwerk zu CLI
    disc_to_interface = Queue() # Queue für Kommunikation von Discovery zu CLI
    
    
    disc_proc = Process(target=discovery_service.discovery_loop, args=(config, disc_to_interface)) # Discovery-Service starten
    disc_proc.daemon = True # Daemon-Prozess, der im Hintergrund läuft
    disc_proc.start() # Discovery-Service starten
    print("Discovery-Service gestartet") # Ausgabe, dass der Discovery-Service gestartet wurde

    """Server/Network als eigener Process"""
    net_proc = Process(target=server.server_loop, args=(config, net_to_interface, interface_to_net)) # Netzwerk-Server starten
    net_proc.daemon = True # Daemon-Prozess, der im Hintergrund läuft
    net_proc.start() # Netzwerk-Server starten

    
    mode = input("Modus wählen: [g] GUI  |  [c] CLI  > ").strip().lower() # Eingabe für den Modus (GUI oder CLI)
    if mode == 'g': # Wenn GUI-Modus gewählt wurde
        from gui_tk import startGui  # Tkinter-basierte GUI importieren
        startGui(config, net_to_interface, disc_to_interface, interface_to_net)  # GUI starten
    else: # Standardmäßig CLI-Modus
        # Fallback zu CLI
        cli = ChatCLI(config, net_to_interface, disc_to_interface, interface_to_net) # CLI-Instanz erstellen
        try: # CLI starten
            cli.cmdloop() # Kommandozeilen-Loop starten
        except KeyboardInterrupt: # Abfangen von KeyboardInterrupt (Strg+C)
            print("\nAbbruch durch Benutzer.") #  Ausgabe, dass der Prozess abgebrochen wurde