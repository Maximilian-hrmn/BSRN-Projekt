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
        return # Beenden der Funktion, wenn die Datei nicht gefunden wird  
        
    except toml.TomlDecodeError:
        print("Fehler beim Dekodieren der Konfigurationsdatei.")
        return # Beenden der Funktion, wenn die Datei nicht dekodiert werden kann

    except socket.error as e:
        print(f"Socket-Fehler: {e}")
        return # Beenden der Funktion bei Socket-Fehler
    try:    
         # Discovery Service erstellen und starten
        discovery = DiscoveryService(timeout=5, discovery_port=int(config["peer_port"]))
        print("[MAIN] Suche nach Peers...")
        peers = discovery.discover_peers()
    
    except Exception as e:
        print(f"Fehler beim Starten des Discovery Services: {e}")
        return # Beenden der Funktion, wenn ein Fehler auftritt
    
    try:
        # Server starten
        server = Server("0.0.0.0", int(config["port"]))
        server.start()
        print("[MAIN] Server und Discovery-Responder gestartet")

        # Dann erst nach Peers suchen
        discovery = DiscoveryService(discovery_port=int(config["peer_port"]))
        peers = discovery.discover_peers()
        
        if peers:
            print(f"[MAIN] Gefundene Peers: {peers}")
        else:
            print("[MAIN] Keine Peers gefunden")

        #Abbruch mit Strg+C abfangen
    except KeyboardInterrupt:
        print("\n[MAIN] Server wird beendet.")
        server.close()
       
        #Abbruch falls die Verbindung zum Server nicht hergestellt werden kann
    except Exception as e:
        print(f"Fehler beim Starten des Servers: {e}")

    try:
        client = SLCPClient("peer_ip", "peer_port")
        print("[MAIN] SLCP Client erstellt und bereit.")

        cli = ChatCLI()
        cli.cmdloop()
    except Exception as e:
        print(f"[MAIN] Fehler beim Starten des Clients oder der CLI: {e}")

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n[MAIN] Beendet durch Benutzer.")