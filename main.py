# File: main.py

import toml
<<<<<<< HEAD
from multiprocessing import Process, Queue
import discovery_service
import server
from cli import ChatCLI

"""
Main Entry Point:

- Lädt config.toml
- Startet im Hintergrund jeweils:
    * Discovery-Service (Process A)
    * Server/Network-Empfang (Process B)
- Anschließend startet CLI (ChatCLI) im Hauptprozess
"""

if __name__ == '__main__':
    config = toml.load('config.toml')

    # IPC-Queues
    cli_to_net = Queue()
    cli_to_disc = Queue()
    net_to_cli = Queue()
    disc_to_cli = Queue()
=======
from server import Server
from client import SLCPClient
from discovery_service import DiscoveryService
from cli import ChatCLI 
import time
import socket

def get_own_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    # TOML-Datei wird geladen und eingebettet und mit try-catch abgefangen
    try:
        config = toml.load("config.toml")
        print("Konfigurationsdatei geladen.")
    except FileNotFoundError: 
        print("Konfigurationsdatei nicht gefunden.")
        return  
    except toml.TomlDecodeError:
        print("Fehler beim Dekodieren der Konfigurationsdatei.")
        return

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
        import threading
        server = Server("0.0.0.0", int(config["server_port"]), int(config["discovery_port"]))
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        time.sleep(1)
    except Exception as e:
        print(f"Fehler beim Starten des Servers: {e}")
        return

    try:
        discovery = DiscoveryService(timeout=10, discovery_port=int(config["discovery_port"]))
        print("[MAIN] Suche nach Peers...")
        peers = discovery.discover_peers()
    except Exception as e:
        print(f"Fehler beim Starten des Discovery Services: {e}")
        return

    try:
        # Eigene IP herausfinden
        my_ip = get_own_ip()
        # Sich selbst aus der Peer-Liste entfernen
        peers = [
            peer for peer in peers 
            if peer[0] != my_ip and 
            not peer[0].startswith('127.') and  # Loopback-Adressen filtern
            peer[0] != '0.0.0.0'  # Unspezifische Adressen filtern
        ]
        print(f"[DEBUG] Gefundene Peers (nach Filter): {peers}")

        if peers:
            peer_ip, peer_tcp_port = peers[0]
            client = SLCPClient(peer_ip, peer_tcp_port)
            print("[MAIN] SLCP Client erstellt und bereit.")
            cli = ChatCLI(client)
            cli.cmdloop()
        else:
            print("[MAIN] Keine Peers gefunden. Beende das Programm.")
        return
    except Exception as e:
        print(f"[MAIN] Fehler beim Starten des Clients oder der CLI: {e}")
>>>>>>> e3e3d87472a639b4ced2beef1075e7f250613fe1

    # Discovery-Service als eigener Process
    disc_proc = Process(target=discovery_service.discovery_loop, args=(config, disc_to_cli))
    disc_proc.daemon = True
    disc_proc.start()

    # Server/Network als eigener Process
    net_proc = Process(target=server.server_loop, args=(config, net_to_cli))
    net_proc.daemon = True
    net_proc.start()

    # CLI im Hauptprozess
    cli = ChatCLI(config, net_to_cli, disc_to_cli)
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer.")
