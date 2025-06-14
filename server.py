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
    if not os.path.exists(imagepath):
        os.makedirs(imagepath)

    # Erstelle einen UDP-Socket
    current_port = config['port']
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", current_port))

    while True:
        if cli_to_net_queue is not None:
            try:
                msg = cli_to_net_queue.get_nowait()
                if msg[0] == 'SET_PORT':
                    new_port = int(msg[1])
                    if new_port != current_port:
                        sock.close()
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.bind(("", new_port))
                        current_port = new_port
            except queue.Empty:
                pass

        data, addr = sock.recvfrom(65535)
        try:
            line = data.decode('utf-8', errors='ignore')
            cmd, args = parse_slcp_line(line)
        except:
            continue

        # Verarbeite die empfangene SLCP-Nachricht
        if cmd == 'MSG' and len(args) >= 2:
            from_handle = args[0]
            text = args[1]
            net_to_cli_queue.put(('MSG', from_handle, text))

        # Verarbeite die empfangene Bildnachricht
        elif cmd == 'IMG' and len(args) == 2:
            from_handle = args[0]
            size = int(args[1])
            # Empfange Raw-Binärdaten
            img_data, _ = sock.recvfrom(size)
            filename = f"{from_handle}_{int(time.time())}.jpg"
            filepath = os.path.join(imagepath, filename)
            with open(filepath, 'wb') as f:
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