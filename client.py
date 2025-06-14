# File: client.py

import socket
from slcp_handler import build_join, build_leave, build_who, build_msg, build_img
import os

"""
Client-Funktionen (Network-Sender):

- Broadcast (JOIN/WHO/LEAVE) an config['broadcast']:config['whoisport'].
- Fallback auf localhost nur, wenn die Broadcast-Adresse bereits im
  Loopback-Bereich liegt, um unbeabsichtigtes Selbst-Senden im LAN zu
  vermeiden.
- Unicast (MSG/IMG) an target_host:target_port
"""

def _send_discovery(msg: bytes, config: dict) -> None:
    """Send a discovery message via broadcast.

    Fällt nur dann auf 127.0.0.1 zurück, wenn die konfigurierte
    Broadcast-Adresse selbst im 127.0.0.0/8-Netz liegt. Dadurch wird
    vermieden, dass Peers im LAN versehentlich die localhost-Adresse
    austauschen und Nachrichten an sich selbst schicken.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.sendto(msg, (config['broadcast'], config['whoisport']))
    except OSError as e:
        # Fallback nur bei lokalen Broadcast-Adressen verwenden
        if e.errno == 101 and config['broadcast'].startswith('127.'):
            sock.sendto(msg, ("127.0.0.1", config['whoisport']))
        else:
            raise
    finally:
        sock.close()


# Funktion zum Senden einer JOIN-Nachricht an den Server
def client_send_join(config):
    msg = build_join(config['handle'], config['port'])
    _send_discovery(msg, config)

# Funktion zum Senden einer WHO-Nachricht an den Server
def client_send_who(config):
    msg = build_who()
    _send_discovery(msg, config)

# Funktion zum Senden einer LEAVE-Nachricht an den Server
def client_send_leave(config):
    msg = build_leave(config['handle'])
    _send_discovery(msg, config)

#Funktion zum Senden einer MSG-Nachricht an einen bestimmten Host und Port
def client_send_msg(target_host: str, target_port: int, from_handle: str, text: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = build_msg(from_handle, text)
    sock.sendto(data, (target_host, target_port))
    sock.close()
    
#Funktion zum Senden eines Bildes an einen bestimmten Host und Port
def client_send_img(target_host: str, target_port: int, from_handle: str, img_path: str):
    if not os.path.isfile(img_path):
        return False
    size = os.path.getsize(img_path)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    header = build_img(from_handle, size)
    sock.sendto(header, (target_host, target_port))
    with open(img_path, 'rb') as f:
        data = f.read()
        sock.sendto(data, (target_host, target_port))
    sock.close()
    return True
