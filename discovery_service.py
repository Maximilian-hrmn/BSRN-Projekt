# File: discovery_service.py

import socket
import time
from slcp_handler import parse_slcp_line, build_knowusers
import toml

"""
Discovery Service:

- Lauscht per UDP auf config['whoisport'] (z. B. Port 4000) auf Broadcasts.
- Verarbeitet SLCP-Befehle: JOIN, WHO, LEAVE.
- Speichert eine lokale Peerliste mapping handle -> (IP, Port).
- Sendet KNOWUSERS-Antworten per Unicast an anfragenden Peer.
"""

def discovery_loop(config, cli_queue):
    peers = {}  # handle -> (host, port)
    whoisport = config['whoisport']

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", whoisport))

    while True:
        data, addr = sock.recvfrom(65535)
        try:
            line = data.decode('utf-8')
            cmd, args = parse_slcp_line(line)
        except:
            continue

        if cmd == 'JOIN' and len(args) == 2:
            new_handle = args[0]
            new_port = int(args[1])
            peers[new_handle] = (addr[0], new_port)
            # Sende KNOWUSERS an neuen Peer:
            response = build_knowusers(peers)
            sock.sendto(response, (addr[0], new_port))

        elif cmd == 'WHO':
            # Sende KNOWUSERS an Anfragenden zurück
            response = build_knowusers(peers)
            sock.sendto(response, addr)

        elif cmd == 'LEAVE' and len(args) == 1:
            leaving = args[0]
            if leaving in peers:
                del peers[leaving]

        # Wenn Peerliste sich ändert, sende Kopie an CLI
        cli_queue.put(('PEERS', peers.copy()))

if __name__ == '__main__':
    config = toml.load('config.toml')
    from multiprocessing import Queue
    q = Queue()
    discovery_loop(config, q)