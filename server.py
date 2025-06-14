# File: server.py

import socket
import os
import time
import queue
from slcp_handler import parse_slcp_line

"""
Server-Prozess (Network-Empfang):

- Lauscht per UDP-Unicast auf config['port'] auf eingehende SLCP-Nachrichten (MSG, IMG).
- Bei MSG: Gibt Nachricht über IPC (Interprozess-Kommunikation) an die CLI weiter.
- Bei IMG: Liest zunächst Header (IMG <handle> <size>), dann erwartet es in einem separaten recvfrom()
  den Raw-JPEG-Binärstrom der angegebenen Länge <size>.
  Speichert das empfangene Bild unter imagepath/<handle>_<timestamp>.jpg und übermittelt der CLI den Pfad.
"""

# Funktion namens `server_loop`, die den Serverprozess implementiert.
def server_loop(config, net_to_cli_queue, cli_to_net_queue=None):

    # Stelle sicher, dass das Verzeichnis für empfangene Bilder existiert
    imagepath = config['imagepath']
    # Falls der imagepath noch nicht existiert, wird er erstellt
    if not os.path.exists(imagepath):
        os.makedirs(imagepath)

    # Aktuellen Port aus der Konfiguration übernehmen
    current_port = config['port']

    # Erstellen eines UDP-Sockets
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Setzen der Option SO_REUSEADDR, damit der Port wiederverwendet werden kann
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Binden des Sockets an die IP-Adresse '' (alle Interfaces) und den aktuellen Port
    sock.bind(("", current_port))

    # Endlosschleife zum permanenten Empfangen von Nachrichten
    while True:

        # Prüfen, ob es eine Port-Änderung über die CLI gibt
        if cli_to_net_queue is not None:
            try:
                # Sofortige, nicht blockierende Abfrage der CLI-Nachrichten
                msg = cli_to_net_queue.get_nowait()
                # Wenn die CLI eine Portänderung anfordert ('SET_PORT' mit neuem Port)
                if msg[0] == 'SET_PORT':
                    new_port = int(msg[1])
                    # Nur reagieren, wenn sich der Port tatsächlich geändert hat
                    if new_port != current_port:
                        sock.close()
                        # Neuer Socket wird erstellt und gebunden
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.bind(("", new_port))
                        print(f"Port changed to {new_port}")
                        current_port = new_port
            # Keine Nachricht vorhanden – Queue ist leer
            except queue.Empty:
                pass

        # Empfang von Daten über den UDP-Socket (max. 65535 Bytes)
        data, addr = sock.recvfrom(65535)

        # Versuch, die Nachricht als SLCP-Zeile zu interpretieren
        try:
            line = data.decode('utf-8', errors='ignore')
            cmd, args = parse_slcp_line(line)
        except:
            # Fehlerhafte oder nicht-dekodierbare Nachricht wird ignoriert
            continue

        # Verarbeiten eines Textnachricht-Kommandos (MSG)
        if cmd == 'MSG' and len(args) >= 2:
            # Extrahieren des Absender-Handles
            from_handle = args[0]
            # Extrahieren des eigentlichen Nachrichtentextes
            text = args[1]
            # Weiterleiten der Nachricht an die CLI über die IPC-Queue
            net_to_cli_queue.put(('MSG', from_handle, text))

        # Verarbeiten eines Bild-Kommandos (IMG)
        elif cmd == 'IMG' and len(args) == 2:
            # Extrahieren von Absender und erwarteter Bildgröße
            from_handle = args[0]
            size = int(args[1])

            # Empfang des Bilddatenstroms mit erwarteter Größe
            img_data, _ = sock.recvfrom(size)

            # Erstellen eines einzigartigen Dateinamens basierend auf Handle und Zeitstempel
            filename = f"{from_handle}_{int(time.time())}.jpg"
            filepath = os.path.join(imagepath, filename)

            # Speichern des empfangenen Bildes in die Zieldatei
            with open(filepath, 'wb') as f:
                f.write(img_data)

            # Übermittlung des Bildpfads an die CLI
            net_to_cli_queue.put(('IMG', from_handle, filepath))

"""
Test-Main-Funktion zum Starten des Servers direkt (z.B. zu Debug-Zwecken)

Hinweis: Die Konfiguration wird aus der Datei 'config.toml' geladen,
die IPC-Queues werden lokal erstellt und an server_loop() übergeben.

if __name__ == '__main__':
    config = toml.load('config.toml')
    from multiprocessing import Queue
    q1 = Queue()
    q2 = Queue()
    server_loop(config, q1, q2)
"""