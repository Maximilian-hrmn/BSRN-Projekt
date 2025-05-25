import toml
import socket
from server import Server
from client import SLCPClient
from discovery_service import DiscoveryService
from CLI2 import ChatCLI 

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
         # Discovery Service erstellen und starten
        discovery = DiscoveryService(discovery_port=int(config["peer_port"]))
        peers = discovery.discover_peers()
    except Exception as e:
        print(f"Fehler beim Starten des Discovery Services: {e}")
        return
    
try:
    # Server starten
    server = Server("0.0.0.0", 12345)
    server.start()

    #Abbruch mit Strg+C abfangen
except KeyboardInterrupt:
    print("\n[MAIN] Server wird beendet.")
    server.close()
    #Abbruch falls die Verbindung zum Server nicht hergestellt werden kann
except Exception as e:
    print(f"Fehler beim Starten des Servers: {e}")

try:
    # SLCP Client erstellen und verbinden
    client = SLCPClient("peer_ip", "peer_port")
    print("[MAIN] SLCP Client erstellt und bereit.")
except Exception as e:
    print(f"[MAIN] Fehler beim Starten des Clients: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MAIN] Beendet durch Benutzer.")

    try:
        cli = ChatCLI()
        cli.cmdloop()
    except Exception as e:
        print(f"[MAIN] Fehler beim Starten der CLI: {e}")