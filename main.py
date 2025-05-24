import toml
import socket
from server import Server
from client import SLCPClient
import threading
from discovery_service import discover_peers
import CLI

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
    
    except socket.error as e:
        print(f"Fehler beim Senden der Discovery-Anfrage: {e}")
        return
    
    try:    
        # UDP parallel starten
        threading.Thread(target=discover_peers, args=(5000,), daemon=True).start()

    except Exception as e:
        print(f"Fehler beim Starten des Discovery-Dienstes: {e}")
    
    try:
        client = SLCPClient(config["peer_ip"], config["peer_port"])
        print("[MAIN] SLCP Client erstellt und bereit.")
    except Exception as e:
        print(f"[MAIN] Fehler beim Starten des Clients: {e}")

    try:
        # UI gestartet
        CLI.CLI.start()
    except Exception as e:
        print(f"Fehler beim Starten der CLI: {e}")


    try:    
        # Server starten
        server = Server("0.0.0.0", 12345)
        server.start()

        while True:
            pass

    except KeyboardInterrupt:
        print("\n[MAIN] Server wird beendet.")
        server.close()
        return

    except Exception as e:
        print(f"Fehler beim Starten des Servers: {e}")
    return   

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MAIN] Beendet durch Benutzer.")