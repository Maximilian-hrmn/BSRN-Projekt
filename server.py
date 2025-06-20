# File: server.py

import socket
import os
import time
from slcp_handler import parse_slcp_line
import queue

"""
@file server.py
@brief Server-Prozess (Network-Empfang):

- Lauscht per TCP auf config['port'] auf eingehende SLCP-Nachrichten (MSG, IMG).
- Bei MSG: Gibt Nachricht über IPC an CLI weiter.
- Bei IMG: Liest erst Header (IMG <handle> <size>), dann liest er anschließend den Raw-JPEG-Binärstrom der Länge <size>.
  Speichert empfangenes Bild unter imagepath/<handle>_<timestamp>.jpg und meldet der CLI den Pfad.

"""

def server_loop(config, net_to_cli_queue, cli_to_net_queue=None):
    """Funktion namens `server_loop`, die den Serverprozess implementiert."""

    #Stelle sicher, dass der imagepath existiert
    imagepath = os.path.abspath(config['imagepath'])
    #Erstelle den Ordner, falls er nicht existiert
    if not os.path.exists(imagepath):
        os.makedirs(imagepath)

    # Setze den aktuellen Port aus der Konfiguration
    current_port = config['port']

    def bind_socket(port):
        """Funktion zum Binden des Sockets an den angegebenen Port"""
        # Erstelle einen TCP/IP-Socket und binde ihn an den angegebenen Port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Setze die Socket-Option
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Binde den Socket an alle verfügbaren Schnittstellen und den angegebenen Port
        s.bind(("", port))
        # Setze den Socket in den Listenmodus
        s.listen()
        return s

    # Binde den Socket an den aktuellen Port
    sock = bind_socket(current_port)
    # Setze eine Timeout für den Socket, um nicht ewig zu blockieren
    sock.settimeout(0.5)

    while True:
        """
        Endlosschleife, um auf eingehende Verbindungen zu warten
        """
        #Überprüfe, ob eine neue Portänderung angefordert wurde
        if cli_to_net_queue is not None:
            try:
                # Versuche, eine Nachricht aus der Queue zu lesen
                msg = cli_to_net_queue.get_nowait()
                # Wenn die Nachricht den Befehl 'SET_PORT' enthält, ändere den Port
                if msg[0] == 'SET_PORT':
                    # Extrahiere den neuen Port aus der Nachricht
                    new_port = int(msg[1])
                    # Wenn der neue Port sich vom aktuellen Port unterscheidet, schließe den alten Socket und binde einen neuen Socket
                    if new_port != current_port:
                        sock.close()
                        # Binde den Socket an den neuen Port
                        sock = bind_socket(new_port)
                        # Setze den Socket-Timeout zurück
                        sock.settimeout(0.5)
                        # Informiere die CLI über die Portänderung
                        current_port = new_port
            except queue.Empty:
                pass

        try:
            # Warte auf eingehende Verbindungen
            conn, _ = sock.accept()
        except socket.timeout:
            continue
        with conn:
            # Lese eine Zeile von der Verbindung
            f = conn.makefile('rb')
            # Lese die Zeile und dekodiere sie
            line = f.readline().decode('utf-8', errors='ignore')
            if not line:
                continue
            try:
                # Versuche, die Zeile zu parsen
                cmd, args = parse_slcp_line(line)
            except Exception:
                continue

            #Verarbeite die empfangene Nachricht basierend auf dem Befehl
            if cmd == 'MSG' and len(args) >= 2:
                # Bei MSG: Leite die Nachricht an die CLI weiter
                from_handle = args[0]
                text = args[1]
                # Füge den Rest der Nachricht (falls vorhanden) zusammen
                net_to_cli_queue.put(('MSG', from_handle, text))

            #Bei IMG: Lese den Header und die Bilddaten
            elif cmd == 'IMG' and len(args) == 2:
                # Lese den Header und die Bilddaten
                from_handle = args[0]
                # Lese die Größe des Bildes
                size = int(args[1])
                # Lese die Bilddaten aus der Verbindung
                img_data = f.read(size)
                # Wenn die Bilddaten nicht die erwartete Größe haben, ignoriere die Nachricht
                filename = f"{from_handle}_{int(time.time())}.jpg"
                # Speichere das Bild im angegebenen Verzeichnis
                filepath = os.path.join(imagepath, filename)
                # Überprüfe, ob die empfangenen Bilddaten die erwartete Größe haben
                with open(filepath, 'wb') as imgf:
                    imgf.write(img_data)
                # Füge den Pfad des gespeicherten Bildes zur Queue hinzu
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