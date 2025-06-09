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
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = build_join(config['handle'], config['port'])
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    sock.close()

# Funktion zum Senden einer WHO-Nachricht an den Server
def client_send_who(config):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = build_who()
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    sock.close()

# Funktion zum Senden einer LEAVE-Nachricht an den Server
def client_send_leave(config):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = build_leave(config['handle'])
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    sock.close()

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