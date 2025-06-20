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
- Unicast (MSG/IMG) an target_host:target_port erfolgt jetzt per TCP.
"""

def _send_discovery(msg: bytes, config: dict) -> None:
    """Funktion zum Senden von Discovery-Nachrichten (JOIN, WHO, LEAVE) an den Server."""


    """Send a discovery message via broadcast.

    Fällt nur dann auf 127.0.0.1 zurück, wenn die konfigurierte
    Broadcast-Adresse selbst im 127.0.0.0/8-Netz liegt. Dadurch wird
    vermieden, dass Peers im LAN versehentlich die localhost-Adresse
    austauschen und Nachrichten an sich selbst schicken.
    """
    # Erstelle einen UDP-Socket für den Broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Setze die Socket-Optionen für Wiederverwendbarkeit und Broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        # Sende die Nachricht an die konfigurierte Broadcast-Adresse und den Port
        sock.sendto(msg, (config['broadcast'], config['whoisport']))
    except OSError as e:
        # Fallback nur bei lokalen Broadcast-Adressen verwenden
        if e.errno == 101 and config['broadcast'].startswith('127.'):
            # Sende die Nachricht an localhost, wenn die Broadcast-Adresse im Loopback-Bereich liegt
            sock.sendto(msg, ("127.0.0.1", config['whoisport']))
        else:
            raise
    finally:
        sock.close()

def client_send_join(config):
    """Funktion zum Senden einer JOIN-Nachricht an den Server"""
    # Erstelle eine JOIN-Nachricht mit dem Handle und Port aus der Konfiguration
    msg = build_join(config['handle'], config['port'])
    _send_discovery(msg, config)

def client_send_who(config):
    """Funktion zum Senden einer WHO-Nachricht an den Server"""
    # Erstelle eine WHO-Nachricht, um die Liste der aktiven Clients abzufragen
    msg = build_who()
    _send_discovery(msg, config)

def client_send_leave(config):
    """Funktion zum Senden einer LEAVE-Nachricht an den Server"""
    # Erstelle eine LEAVE-Nachricht mit dem Handle aus der Konfiguration
    msg = build_leave(config['handle'])
    # Sende die LEAVE-Nachricht an den Server
    _send_discovery(msg, config)

def client_send_msg(target_host: str, target_port: int, from_handle: str, text: str):
    """Funktion zum Senden einer MSG-Nachricht an einen bestimmten Host und Port"""
    # Sende eine Textnachricht über TCP.
    with socket.create_connection((target_host, target_port)) as sock:
        # Erstelle die Nachricht im SLCP-Format
        data = build_msg(from_handle, text)
        # Sende die Nachricht an den angegebenen Host und Port
        sock.sendall(data)
    
def client_send_img(target_host: str, target_port: int, from_handle: str, img_path: str):
    """Funktion zum Senden eines Bildes an einen bestimmten Host und Port"""
   # Überprüfe, ob der angegebene Pfad zu einem Bild existiert
    if not os.path.isfile(img_path):
        return False
    size = os.path.getsize(img_path)
    # Überprüfe, ob die Bildgröße größer als 0 ist
    with socket.create_connection((target_host, target_port)) as sock:
        # Sende den Header mit dem Handle und der Größe des Bildes
        header = build_img(from_handle, size)
        # Sende den Header und dann den Bildinhalt
        sock.sendall(header)
        # Öffne das Bild im Binärmodus und sende den Inhalt
        with open(img_path, 'rb') as f:
            # Sende den Bildinhalt über den Socket
            sock.sendall(f.read())
    return True
