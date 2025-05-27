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
    
    username = input("Bitte gib deinen Benutzernamen ein: ").strip() # Benutzername wird in der .toml-Datei überschrieben 
    if not username:
        print("Benutzername darf nicht leer sein.") # Wenn der Benutzername leer ist, wird die Funktion beendet
        return
    config["handle"] = username # Überschreiben des Benutzernamens in der Konfigurationsdatei
    try:
        with open("config.toml", "w") as f: # Schreiben des Benutzernamens in die .toml-Datei
            toml.dump(config, f)    # Speichern der Konfiguration
        print(f"[MAIN] Benutzername '{username}' wurde gespeichert.") # Bestätigung der Speicherung
    except Exception as e:
        print(f"Fehler beim Schreiben in die config.toml: {e}") # Wenn ein Fehler beim Schreiben auftritt, wird die Funktion beendet
        return

    try:    
        # Discovery Service erstellen und starten
        discovery = DiscoveryService(timeout=5, discovery_port=int(config["discovery_port"]))
        print("[MAIN] Suche nach Peers...")
        peers = discovery.discover_peers()
        if peers: #Beispiel: Verbindung zum ersten gefunden Peer aufbauen
            peer_ip, peer_tcp_port = SLCPClient(peer_ip, peer_tcp_port)
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
            client = SLCPClient(DiscoveryService["found_peers"], int(DiscoveryService["peer_port"]))
            print("[MAIN] SLCP Client erstellt und bereit.")
            cli = ChatCLI(client)
            cli.cmdloop()
    except Exception as e:
            print(f"[MAIN] Fehler beim Starten des Clients oder der CLI: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MAIN] Beendet durch Benutzer.")