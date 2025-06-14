# File: server.py

import socket
import os
import time
from slcp_handler import parse_slcp_line

"""
Server-Prozess (Network-Empfang):

- Lauscht per UDP-Unicast auf config['port'] auf eingehende SLCP-Nachrichten (MSG, IMG).
- Bei MSG: Gibt Nachricht über IPC an CLI weiter.
- Bei IMG: Liest erst Header (IMG <handle> <size>), dann erwartet es in separatem recvfrom() den Raw-JPEG-Binärstrom der Länge <size>.
  Speichert empfangenes Bild unter imagepath/<handle>_<timestamp>.jpg und meldet der CLI den Pfad.

"""

#Funktion namens `server_loop`, die den Serverprozess implementiert.
import queue

def server_loop(config, net_to_cli_queue, cli_to_net_queue=None):

    # Stelle sicher, dass der imagepath existiert
    imagepath = config['imagepath']
    # Überprüfe, ob der imagepath existiert, und erstelle ihn, falls nicht
    if not os.path.exists(imagepath):
        os.makedirs(imagepath)

    # Erstelle einen UDP-Socket
    current_port = config['port']
    # Erstelle einen UDP-Socket und binde ihn an den aktuellen Port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Setze die Option SO_REUSEADDR, um den Port wiederverwenden zu können
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Binde den Socket an die Adresse und den aktuellen Port
    sock.bind(("", current_port))

    while True:
        # Überprüfe, ob eine neue Portänderung angefordert wurde
        if cli_to_net_queue is not None:
            try:
                # Versuche, eine Nachricht aus der cli_to_net_queue zu lesen
                msg = cli_to_net_queue.get_nowait()
                # Wenn die Nachricht 'SET_PORT' ist, ändere den Port
                if msg[0] == 'SET_PORT':
                    # Extrahiere den neuen Port aus der Nachricht
                    new_port = int(msg[1]) 
                    # Wenn der neue Port sich vom aktuellen Port unterscheidet, ändere den Socket
                    if new_port != current_port:
                        sock.close()
                        # Erstelle einen neuen Socket und binde ihn an den neuen Port
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        # Setze die Option SO_REUSEADDR, um den Port wiederverwenden zu können
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        # Binde den neuen Socket an die Adresse und den neuen Port
                        sock.bind(("", new_port))
                        print(f"Port changed to {new_port}")
                        current_port = new_port
            except queue.Empty:
                pass
        # Empfange Daten vom Socket
        data, addr = sock.recvfrom(65535)
        # Wenn keine Daten empfangen wurden, überspringe die Verarbeitung
        try:
            line = data.decode('utf-8', errors='ignore')
            cmd, args = parse_slcp_line(line)
        except:
            continue

        # Verarbeite die empfangene SLCP-Nachricht
        if cmd == 'MSG' and len(args) >= 2:
            # Wenn die Nachricht ein MSG-Kommando ist, extrahiere den Absender und den Text
            from_handle = args[0]
            # Extrahiere den Text der Nachricht, der im zweiten Argument enthalten ist
            text = args[1]
            # Füge die Nachricht in die net_to_cli_queue ein
            net_to_cli_queue.put(('MSG', from_handle, text))

        # Verarbeite die empfangene Bildnachricht
        elif cmd == 'IMG' and len(args) == 2:
            # Wenn die Nachricht ein IMG-Kommando ist, extrahiere den Absender und die Größe des Bildes
            from_handle = args[0]
            # Extrahiere die Größe des Bildes, die im zweiten Argument enthalten ist
            size = int(args[1])
            # Empfange Raw-Binärdaten
            img_data, _ = sock.recvfrom(size)
            # Wenn die empfangenen Daten nicht der erwarteten Größe entsprechen, überspringe die Verarbeitung
            filename = f"{from_handle}_{int(time.time())}.jpg"
            # Erstelle den vollständigen Dateipfad für das Bild
            filepath = os.path.join(imagepath, filename)
            # Speichere die empfangenen Bilddaten in der Datei
            with open(filepath, 'wb') as f:
            # Öffne die Datei im Binärmodus und schreibe die empfangenen Bilddaten hinein
                f.write(img_data)
            net_to_cli_queue.put(('IMG', from_handle, filepath))

"""
Test Main-Funktion zum Testen des Servers

if __name__ == '__main__':
    config = toml.load('config.toml')
    from multiprocessing import Queue
    q1 = Queue()
    q2 = Queue()
    server_loop(config, q1, q2)
"""