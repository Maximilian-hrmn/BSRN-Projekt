import socket
import threading

class Server:
    
    #Server Kontruktor und Initialisierung mit der Ip und dem Port
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {} 
        self.discovery_thread = None  # Für den Discovery-Responder

    # Server starten Methode
    def start(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(5)
        print(f"[TCP] Server gestartet auf {self.ip}:{self.port}")
        
        # TCP Connection Handler starten
        threading.Thread(target=self.accept_connection).start()
        
        # Discovery Responder in eigenem Thread starten
        self.discovery_thread = threading.Thread(target=start_discovery_responder, args=(self.port,))
        self.discovery_thread.daemon = True  # Thread beendet sich mit Hauptprogramm
        self.discovery_thread.start()
        print("[UDP] Discovery-Responder gestartet")

    # Methode um Verbindungen zu akzeptieren
    def accept_connection(self):
        while True:
            client_socket, client_address = self.socket.accept()
            print(f"[TCP] Verbindung hergestellt mit {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    # Methode um mit dem Client zu kommunizieren
    def handle_client(self, client_socket):
        username = None
        try:
            while True:
                header = client_socket.recv(1024).decode().strip()
                if not header:
                    break

                print(f"[TCP] Header erhalten: {header}")
                parts = header.split(" ")

                if parts[0] == "JOIN" and len(parts) == 2:
                    username = parts[1]
                    self.clients[client_socket] = username
                    print(f"[JOIN] {username} beigetreten.")
                    self.broadcast(f"[SERVER] {username} ist dem Chat beigetreten.", client_socket)

                elif parts[0] == "MSG" and len(parts) >= 3:
                    sender = parts[1]
                    message = " ".join(parts[2:])
                    print(f"[MSG] {sender}: {message}")
                    self.broadcast(f"{sender}: {message}", client_socket)

                elif parts[0] == "IMG" and len(parts) == 3:
                    sender = parts[1]
                    size = int(parts[2])
                    print(f"[IMG] Bild von {sender}, {size} Bytes")
                    image_data = self.recv_exact_bytes(client_socket, size)

                    # Bild speichern (optional)
                    with open(f"empfangenes_bild_{sender}.jpg", "wb") as f:
                        f.write(image_data)
                    print("[IMG] Bild gespeichert.")

                    # Nachricht an andere Clients
                    self.broadcast(f"[SERVER] {sender} hat ein Bild gesendet ({size} Bytes).", client_socket)

                    client_socket.send(b"IMG_RECEIVED")

                elif parts[0] == "LEAVE"and len(parts) == 2:
                    username = parts[1]
                    print(f"[LEAVE] {username} hat den Chat verlassen.")
                    self.broadcast(f"[SERVER] {username} hat den Chat verlassen.", client_socket)
                    break

                else:
                    client_socket.send(b"Unbekannter Befehl")
        except Exception as e:
            print(f"[ERROR] Fehler: {e}")
        finally:
            if client_socket in self.clients:
                left_user = self.clients.pop(client_socket)
                print(f"[DISCONNECT] {left_user} getrennt.")
                self.broadcast(f"[SERVER] {left_user} hat die Verbindung getrennt.", client_socket)
            client_socket.close()

    def broadcast(self, message, sender_socket):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode())
                except:
                    client.close()
                    self.clients.pop(client, None)

    # Diese Methode wird verwendet, um sicherzustellen, dass die gesamte Bilddatei empfangen wird
    def recv_exact_bytes(self, client_socket, total_bytes):
        data = b''
        while len(data) < total_bytes:
            chunk = client_socket.recv(min(4096, total_bytes - len(data)))
            if not chunk:
                raise ConnectionError("Verbindung unterbrochen während Bildübertragung")
            data += chunk
        return data
    # Methode um den Server zu schließen
    def close(self):
        self.socket.close()
        print("[TCP] Server geschlossen")


# UDP-Responder für Discovery
def start_discovery_responder(tcp_port, listen_port=5001):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', listen_port))
    print(f"[UDP] Discovery-Responder läuft auf Port {listen_port}")

    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"DISCOVER_SERVICE":
            print(f"[UDP] DISCOVER von {addr}")
            #Sende Antwort, die den TCP Port mitliefert
            response = f"DISCOVER_RESPONSE:{tcp_port}".encode()
            sock.sendto(response, addr)

