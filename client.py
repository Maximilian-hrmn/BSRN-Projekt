# File: client.py

import socket
from slcp_handler import build_join, build_leave, build_who, build_msg, build_img
import os

"""
Client-Funktionen (Network-Sender):

- Broadcast (JOIN/WHO/LEAVE) an config['broadcast']:config['whoisport']
- Unicast (MSG/IMG) an target_host:target_port
"""

# Funktion zum Senden einer JOIN-Nachricht an den Server
def client_send_join(config):
    # Erstellen eines UDP-Sockets für den Broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Setzen der Socket-Optionen für Broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Erstellen der JOIN-Nachricht mit dem Handle und Port aus der Konfiguration
    msg = build_join(config['handle'], config['port'])
    # Senden der JOIN-Nachricht an die Broadcast-Adresse und den konfigurierten Port
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    sock.close()

# Funktion zum Senden einer WHO-Nachricht an den Server
def client_send_who(config):
    # Erstellen eines UDP-Sockets für den Broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Setzen der Socket-Optionen für Broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Erstellen der WHO-Nachricht
    msg = build_who()
    # Senden der WHO-Nachricht an die Broadcast-Adresse und den konfigurierten Port
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    sock.close()

# Funktion zum Senden einer LEAVE-Nachricht an den Server
def client_send_leave(config):
    # Erstellen eines UDP-Sockets für den Broadcast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Setzen der Socket-Optionen für Broadcast
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Erstellen der LEAVE-Nachricht mit dem Handle aus der Konfiguration
    msg = build_leave(config['handle'])
    # Senden der LEAVE-Nachricht an die Broadcast-Adresse und den konfigurierten Port
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    sock.close()

#Funktion zum Senden einer MSG-Nachricht an einen bestimmten Host und Port
def client_send_msg(target_host: str, target_port: int, from_handle: str, text: str):
    # Überprüfen, ob der Text leer ist
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Wenn der Text leer ist, wird eine leere Nachricht gesendet
    data = build_msg(from_handle, text)
    # Senden der Nachricht an den angegebenen Host und Port
    sock.sendto(data, (target_host, target_port))
    sock.close()
    
#Funktion zum Senden eines Bildes an einen bestimmten Host und Port
def client_send_img(target_host: str, target_port: int, from_handle: str, img_path: str):
    # Überprüfen, ob der angegebene Pfad zu einer Bilddatei existiert
    if not os.path.isfile(img_path):
        return False
    # Überprüfen, ob die Datei eine Bilddatei ist
    size = os.path.getsize(img_path)
    # Erstellen eines UDP-Sockets für den Unicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Setzen der Socket-Optionen für Unicast
    header = build_img(from_handle, size)
    # Senden des Headers mit dem Handle und der Dateigröße an den angegebenen Host und Port
    sock.sendto(header, (target_host, target_port))
    # Öffnen der Bilddatei im Binärmodus und Senden des Inhalts
    with open(img_path, 'rb') as f:
        data = f.read()
        sock.sendto(data, (target_host, target_port))
    sock.close()
    return True