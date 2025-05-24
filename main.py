import toml
import socket
from discovery_service import discover_peers
from server import Server
import sys
import threading
from discovery_service import start_discovery_responder
from multiprocessing import Queue

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

    try:
        discover_peers()
        # discovery-service.py starten   
    
    except socket.error as e:
        print(f"Fehler beim Senden der Discovery-Anfrage: {e}")
        return

    
    if __name__ == "__main__":
        try:
            # Server starten
            server = Server("0.0.0.0", 12345)
            server.start()

            # UDP parallel starten
            threading.Thread(target=start_discovery_responder, args=(5000,), daemon=True).start()
        
        except Exception as e:
            print(f"Fehler beim Starten des Servers: {e}")
            return

    try:
        CLI.CLI.start()
        # UI gestartet
    
    except Exception as e:
        print(f"Fehler beim Starten der CLI: {e}")
        return
