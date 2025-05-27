import toml
from server import Server
from client import SLCPClient
from discovery_service import DiscoveryService
from CLI2 import ChatCLI 
import time


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
    
    username = input("Bitte gib deinen Benutzernamen ein: ").strip()
    if not username:
        print("Benutzername darf nicht leer sein.")
        return
    config["handle"] = username
    try:
        with open("config.toml", "w") as f:
            toml.dump(config, f)    
        print(f"[MAIN] Benutzername '{username}' wurde gespeichert.")
    except Exception as e:
        print(f"Fehler beim Schreiben in die config.toml: {e}")
        return

    try:    
        # Discovery Service erstellen und starten
        discovery = DiscoveryService(timeout=5, discovery_port=int(config["discovery_port"]))
        print("[MAIN] Suche nach Peers...")
        peers = discovery.discover_peers()
       # if peers: #Beispiel: Verbindung zum ersten gefunden Peer aufbauen
        #    peer_ip, peer_tcp_port = SLCPClient(peer_ip, peer_tcp_port)
            #Anschließend JOIN, MSG etc. verwenden
    
    except Exception as e:
        print(f"Fehler beim Starten des Discovery Services: {e}")
        return # Beenden der Funktion, wenn ein Fehler auftritt
    
    try:
            import threading
            server = Server("0.0.0.0", int(config["server_port"]))
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()
            time.sleep(1)
    except Exception as e:
            print(f"Fehler beim Starten des Servers: {e}")
            return  # <-- Stoppe, wenn Server nicht startet

    try:
            peers = discovery.discover_peers()
            if peers:
                peer_ip, peer_tcp_port = peers[0]
                client = SLCPClient(peer_ip, peer_tcp_port)
                print("[MAIN] SLCP Client erstellt und bereit.")
            else: 
                print("[MAIN] Keine Peers gefunden. SLCP Client wird ohne Peer gestartet.")
            
            cli = ChatCLI(client)
            cli.cmdloop()
    except Exception as e:
            print(f"[MAIN] Fehler beim Starten des Clients oder der CLI: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MAIN] Beendet durch Benutzer.")