# File: discovery_service.py

import socket
from slcp_handler import parse_slcp_line, build_knowusers
import toml

"""
@file discovery_service.py
@brief Discovery Service:
 - Lauscht per UDP auf dem in der Konfiguration angegebenen Port (config['whoisport'])
 - Verarbeitet SLCP-Befehle: JOIN, WHO, LEAVE und KNOWUSERS.
 - Speichert eine lokale Peerliste, die jedem Handle (Benutzername) eine IP und einen Port zuordnet.
 - Sendet KNOWUSERS-Antworten per Broadcast an alle Peers.
"""

def discovery_loop(config, interface_queue):
    """Funktion namens `discovery_loop`, die den Discovery-Service implementiert."""
    # Erstelle ein leeres Array zum Speichern der bekannten Peers.
    # Jeder Eintrag hat die Form: handle -> (IP-Adresse, Port)
    peers = {} 
    
    # Liest den UDP-Port für Discovery aus der Konfiguration
    whoisport = config['whoisport']

    # Erstellt einen UDP-Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Setze SO_REUSEADDR, damit der Socket sofort wieder genutzt werden kann,
    # falls er kürzlich geschlossen wurde. Zusätzlich SO_REUSEPORT, um mehrere
    # Clients auf dem gleichen Discovery-Port zu erlauben.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    
    # Binde den Socket an alle verfügbaren Netzwerkschnittstellen und den Discovery-Port.
    sock.bind(("", whoisport))

    print(f"[Discovery] Service gestartet auf Port {whoisport}")

    # Loop, der Discovery-Service hört auf eingehende UDP-Nachrichten.
    while True:
        # Empfang der Daten (bis zu 65535 Bytes) sowie der Absenderadresse (IP, Port)
        data, addr = sock.recvfrom(65535)
        
        try:
            # Versucht, die empfangenen Daten als UTF-8-Zeichenkette zu decodieren.
            line = data.decode('utf-8')
            # Parset die Zeichenkette in einen Befehl (cmd) und eine Liste von Argumenten (args).
            cmd, args = parse_slcp_line(line)
        except:
            # Falls ein Fehler bei der Decodierung oder beim Parsen auftritt, ignoriere diese Nachricht.
            continue

        # Verarbeitet den "JOIN"-Befehl
        if cmd == 'JOIN' and len(args) == 2:
            new_handle = args[0]              # Der Benutzername des neuen Peers.
            new_port = int(args[1])           # Der Port, unter dem der neue Peer erreichbar ist.
            # Fügt den neuen Peer in die Peerliste ein, wobei die IP aus der Absenderadresse (addr[0]) stammt.
            peers[new_handle] = (addr[0], new_port)
            # Erstellt eine Antwortnachricht (KNOWUSERS), die alle bekannten Peers enthält.
            response = build_knowusers(peers)
            # Sende die Antwort per Broadcast, damit alle Instanzen aktualisieren
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(response, (config['broadcast'], whoisport))
            # Zusätzlich die Liste direkt an den neuen Peer schicken
            sock.sendto(response, (addr[0], whoisport))

        # Verarbeitet den "WHO"-Befehl
        elif cmd == 'WHO':
            # Erstellt die KNOWUSERS-Antwort mit der aktuellen Peerliste.
            response = build_knowusers(peers)
            # Sendet die Antwort an den anfragenden Peer (Adresse in "addr").
            sock.sendto(response, addr)

        # Verarbeite eine KNOWUSERS-Antwort
        elif cmd == 'KNOWUSERS' and args:
            # args[0] enthält kommagetrennt alle handle:host:port Einträge
            entries = args[0].split(',') if args[0] else []
            for entry in entries:
                try:
                    h, host, port_str = entry.split(':')
                    peers[h] = (host, int(port_str))
                except ValueError:
                    continue

        # Verarbeite den "LEAVE"-Befehl
        elif cmd == 'LEAVE' and len(args) == 1:
            leaving = args[0]   # Der Handle des Peers, der geht.
            # Entferne den Peer aus dem Dictionary, falls er vorhanden ist.
            if leaving in peers:
                del peers[leaving]

        # Informiere die übergeordnete Anwendung (z.B. die CLI) über Änderungen in der Peerliste.
        # Hier wird eine Kopie der aktuellen Peerliste über eine IPC-Queue (cli_queue) verschickt.
        interface_queue.put(('PEERS', peers.copy()))

if __name__ == '__main__':
    """Importiere die Konfigurationsdatei (config.toml) und die SLCP-Handler-Funktionen."""
    # Lädt die Konfigurationsdatei (config.toml)
    config = toml.load('config.toml')
    from multiprocessing import Queue
    # Erstellt eine Queue für die Kommunikation zwischen Discovery-Service und z.B. der CLI.
    q = Queue()
    # Startet die Discovery-Schleife.
    discovery_loop(config, q)