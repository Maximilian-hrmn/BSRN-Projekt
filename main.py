# File: main.py

import toml # Importiere die TOML-Bibliothek zum Laden der Konfiguration
from multiprocessing import Process, Queue # Importiere die Multiprocessing-Bibliothek für parallele Prozesse
import discovery_service # Importiere den Discovery-Service
import server # Importiere den Server/Network-Empfang
from cli import ChatCLI # Importiere die ChatCLI-Klasse für die Kommandozeilen-Schnittstelle

"""
Main Entry Point:

- Lädt config.toml
- Startet im Hintergrund jeweils:
    * Discovery-Service (Process A)
    * Server/Network-Empfang (Process B)
- Anschließend startet CLI (ChatCLI) im Hauptprozess
"""

if __name__ == '__main__': # Main Entry Point
    config = toml.load('config.toml') # Lädt Konfiguration aus config.toml
    

    # IPC-Queues
    cli_to_net = Queue() #  CLI sendet an Network
    cli_to_disc = Queue() # CLI sendet an Discovery-Service
    net_to_cli = Queue() # Network sendet an CLI
    disc_to_cli = Queue() # Discovery-Service sendet an CLI

    # Discovery-Service als eigener Process
    disc_proc = Process(target=discovery_service.discovery_loop, args=(config, disc_to_cli)) # Discovery-Service startet und kommuniziert mit CLI
    disc_proc.daemon = True # Daemon-Prozess, wird beendet, wenn Hauptprozess endet
    disc_proc.start() # Startet den Discovery-Service-Prozess

    # Server/Network als eigener Process
    net_proc = Process(target=server.server_loop, args=(config, net_to_cli, cli_to_net)) # Server startet und kommuniziert mit CLI
    net_proc.daemon = True # Daemon-Prozess, wird beendet, wenn Hauptprozess endet
    net_proc.start() # Startet den Server/Network-Prozess

    
    mode = input("Modus wählen: [g] GUI  |  [c] CLI  > ").strip().lower() # Eingabeaufforderung für Moduswahl
    if mode == 'g': # GUI-Modus
        from gui import startGui # Importiere GUI-Funktion
        startGui(config, net_to_cli, disc_to_cli) # Starte GUI mit Konfiguration und IPC-Queues
    else:
        # Fallback zu CLI
        cli = ChatCLI(config, net_to_cli, disc_to_cli, cli_to_net) # Initialisiere CLI mit Konfiguration und IPC-Queues
        try:
            cli.cmdloop() # Starte die Kommandozeilen-Schnittstelle
        except KeyboardInterrupt: # Behandle Tastaturunterbrechung (Strg+C)
            print("\nAbbruch durch Benutzer.") # Behandle Tastaturunterbrechung