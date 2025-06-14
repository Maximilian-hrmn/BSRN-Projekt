# File: client.py

import socket
from slcp_handler import build_join, build_leave, build_who, build_msg, build_img
import os

"""
Client-Funktionen (Network-Sender):

Dieses Modul stellt Funktionen bereit, um verschiedene SLCP-Nachrichten (JOIN, WHO, LEAVE, MSG, IMG)
über UDP/TCP zu versenden.

- Broadcast (JOIN/WHO/LEAVE) wird an config['broadcast']:config['whoisport'] gesendet. (UDP)
- Unicast (MSG/IMG) wird direkt an target_host:target_port gesendet. (TCP)
"""

# Funktion zum Senden einer JOIN-Nachricht an alle Clients im Netzwerk
def client_send_join(config):
    # Erstellen eines UDP-Sockets für den Broadcast-Versand
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Aktivieren des Broadcast-Modus auf dem Socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Erstellen der JOIN-Nachricht mit Benutzer-Handle und eigenem Port
    msg = build_join(config['handle'], config['port'])
    # Versenden der JOIN-Nachricht an die Broadcast-Adresse und den konfigurierten Port
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    # Schließen des Sockets nach dem Versand
    sock.close()

# Funktion zum Senden einer WHO-Nachricht (Anfrage nach aktiven Teilnehmern)
def client_send_who(config):
    # Erstellen eines UDP-Sockets für den Broadcast-Versand
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Aktivieren des Broadcast-Modus auf dem Socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Erstellen der WHO-Nachricht zur Abfrage aktiver Benutzer
    msg = build_who()
    # Versenden der WHO-Nachricht an die Broadcast-Adresse und den konfigurierten Port
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    # Schließen des Sockets nach dem Versand
    sock.close()

# Funktion zum Senden einer LEAVE-Nachricht (Verlassen des Netzwerks)
def client_send_leave(config):
    # Erstellen eines UDP-Sockets für den Broadcast-Versand
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Aktivieren des Broadcast-Modus auf dem Socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Erstellen der LEAVE-Nachricht mit dem Handle des Clients
    msg = build_leave(config['handle'])
    # Versenden der LEAVE-Nachricht an die Broadcast-Adresse und den konfigurierten Port
    sock.sendto(msg, (config['broadcast'], config['whoisport']))
    # Schließen des Sockets nach dem Versand
    sock.close()

# Funktion zum Senden einer MSG-Nachricht (Textnachricht) an einen bestimmten Host und Port
def client_send_msg(target_host: str, target_port: int, from_handle: str, text: str):
    # Erstellen eines UDP-Sockets für den direkten Versand (Unicast)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Erstellen der Nachricht im SLCP-Format mit Absender-Handle und Nachrichtentext
    data = build_msg(from_handle, text)
    # Versenden der Nachricht an den Ziel-Host und -Port
    sock.sendto(data, (target_host, target_port))
    # Schließen des Sockets nach dem Versand
    sock.close()

# Funktion zum Senden einer Bilddatei (IMG-Nachricht) an einen bestimmten Host und Port
def client_send_img(target_host: str, target_port: int, from_handle: str, img_path: str):
    # Überprüfen, ob der angegebene Pfad zu einer Datei existiert
    if not os.path.isfile(img_path):
        # Abbruch, wenn die Datei nicht existiert
        return False

    # Ermitteln der Dateigröße in Bytes
    size = os.path.getsize(img_path)

    # Erstellen eines UDP-Sockets für den direkten Versand (Unicast)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Erstellen des SLCP-Headers für das Bild (Absender + Dateigröße)
    header = build_img(from_handle, size)
    # Versenden des Bild-Headers an den Ziel-Host und -Port
    sock.sendto(header, (target_host, target_port))

    # Öffnen der Bilddatei im Binärmodus und Senden der Bilddaten
    with open(img_path, 'rb') as f:
        data = f.read()
        # Versenden der Bilddaten direkt nach dem Header
        sock.sendto(data, (target_host, target_port))

    # Schließen des Sockets nach dem Versand
    sock.close()

    # Rückgabe True bei erfolgreichem Versand
    return True