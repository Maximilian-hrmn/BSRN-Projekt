import toml
import socket
from server import Server
from client import SLCPClient
import threading
from discovery_service import discover_peers

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
        # Discovery Service starten
        discover_peers(config["peer_ip"], config["peer_port"])
    
    except Exception as e:
        print(f"Fehler beim Starten des Discovery Services: {e}")
        return
    
try:
    # Server starten
    server = Server("0.0.0.0", 12345)
    server.start()

except KeyboardInterrupt:
    print("\n[MAIN] Server wird beendet.")
    server.close()

except Exception as e:
    print(f"Fehler beim Starten des Servers: {e}")

try:
    client = SLCPClient("peer_ip", "peer_port")
    print("[MAIN] SLCP Client erstellt und bereit.")
except Exception as e:
    print(f"[MAIN] Fehler beim Starten des Clients: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MAIN] Beendet durch Benutzer.")