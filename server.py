# File: server.py

import socket
import os
import time
from slcp_handler import parse_slcp_line

"""
Server-Prozess (Network-Empfang):

- Lauscht per TCP auf config['port'] auf eingehende SLCP-Nachrichten (MSG, IMG).
- Bei MSG: Gibt Nachricht über IPC an CLI weiter.
- Bei IMG: Liest erst Header (IMG <handle> <size>), dann liest er anschließend den Raw-JPEG-Binärstrom der Länge <size>.
  Speichert empfangenes Bild unter imagepath/<handle>_<timestamp>.jpg und meldet der CLI den Pfad.

"""

#Funktion namens `server_loop`, die den Serverprozess implementiert.
import queue

def server_loop(config, net_to_cli_queue, cli_to_net_queue=None):

    # Stelle sicher, dass der imagepath existiert
    imagepath = config['imagepath']
    if not os.path.exists(imagepath):
        os.makedirs(imagepath)

    current_port = config['port']

    def bind_socket(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", port))
        s.listen()
        return s

    sock = bind_socket(current_port)
    sock.settimeout(0.5)

    while True:
        if cli_to_net_queue is not None:
            try:
                msg = cli_to_net_queue.get_nowait()
                if msg[0] == 'SET_PORT':
                    new_port = int(msg[1])
                    if new_port != current_port:
                        sock.close()
                        sock = bind_socket(new_port)
                        sock.settimeout(0.5)
                        current_port = new_port
            except queue.Empty:
                pass

        try:
            conn, _ = sock.accept()
        except socket.timeout:
            continue
        with conn:
            f = conn.makefile('rb')
            line = f.readline().decode('utf-8', errors='ignore')
            if not line:
                continue
            try:
                cmd, args = parse_slcp_line(line)
            except Exception:
                continue

            if cmd == 'MSG' and len(args) >= 2:
                from_handle = args[0]
                text = args[1]
                net_to_cli_queue.put(('MSG', from_handle, text))

            elif cmd == 'IMG' and len(args) == 2:
                from_handle = args[0]
                size = int(args[1])
                img_data = f.read(size)
                filename = f"{from_handle}_{int(time.time())}.jpg"
                filepath = os.path.join(imagepath, filename)
                with open(filepath, 'wb') as imgf:
                    imgf.write(img_data)
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
