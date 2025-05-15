import toml
import socket
from discovery_service import discover_peers
from server import Server
from CLI import CLI

def main():
    # TOML-Datei wird geladen und eingebetet und mit try-catch abgefangen
    try:
        config = toml.load("config.toml")
        print("Konfigurationsdatei geladen.")
        
    except FileNotFoundError: 
        print("Konfigurationsdatei nicht gefunden.")
        return  
        
    except toml.TomlDecodeError:
        print("Fehler beim Dekodieren der Konfigurationsdatei.")
        return
        
    discover_peers()
    # discovery-service.py starten

    Server.server.start()
    # server.py starten

    CLI.CLI.start()
    # UI gestartet






if __name__ == "__main__":
    main()