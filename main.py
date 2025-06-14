import argparse # ArgumentParser für Kommandozeilenargumente
import toml # TOML-Parser für Konfigurationsdateien
from multiprocessing import Process, Queue # Multiprocessing für parallele Prozesse
import discovery_service # Discovery-Service für Peer-Erkennung
import server # Server-Modul für Netzwerkkommunikation
from cli import ChatCLI # CLI-Modul für Kommandozeileninteraktion

"""
Main Entry Point:

- Lädt config.toml
- Startet im Hintergrund jeweils:
    * Discovery-Service (Process A)
    * Server/Network-Empfang (Process B)
- Anschließend startet CLI (ChatCLI) im Hauptprozess
"""
# Main-Block, um das Skript direkt auszuführen
if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description="Start chat client")
    parser.add_argument("--port", type=int, help="UDP port for this client")
    parser.add_argument("--broadcast", help="Broadcast address for discovery")
    parser.add_argument("--whoisport", type=int, help="Port for discovery service")
    args = parser.parse_args()

    config = toml.load('config.toml')
    if args.port is not None:
        config['port'] = args.port
    else:
        config['port'] = 0
    if args.broadcast:
        config['broadcast'] = args.broadcast
    if args.whoisport:
        config['whoisport'] = args.whoisport
    

    # IPC-Queues
    cli_to_net = Queue()
    cli_to_disc = Queue()
    net_to_cli = Queue()
    disc_to_cli = Queue()

    # Discovery-Service als eigener Process
    disc_proc = Process(target=discovery_service.discovery_loop, args=(config, disc_to_cli))
    disc_proc.daemon = True
    disc_proc.start()
    print("Discovery-Service gestartet")

    # Server/Network als eigener Process
    net_proc = Process(target=server.server_loop, args=(config, net_to_cli, cli_to_net))
    net_proc.daemon = True
    net_proc.start()

    
    mode = input("Modus wählen: [g] GUI  |  [c] CLI  > ").strip().lower()
    if mode == 'g':
        from gui import startGui
        startGui(config, net_to_cli, disc_to_cli)
    else:
        # Fallback zu CLI
        cli = ChatCLI(config, net_to_cli, disc_to_cli, cli_to_net)
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nAbbruch durch Benutzer.")
