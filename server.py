import socket
import threading

# Konstruktor eines Servers, er braucht dafür eine IP-Adresse und einen Port
class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Methode zum starten des Servers. Danach "lauscht" der Server nach Verbindungen
    def start(self):
        self.socket.bind((self.ip, self.port))
        self.socket.listen(5)
        print(f"Server gebunden an {self.ip}:{self.port}")

    # Methode zum akzeptieren von Verbindungen
    def accept_connection(self):
        while True:
            client_socket, client_address = self.socket.accept()
            print(f"Verbindung erfolgreich hergestellt mit {client_address}")
            # Einen neuen Thread starten, um die Kommunikation mit dem Client zu behandeln
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    # Methode zum behandeln der Kommunikation mit dem Client
    def handle_client(self, client_socket):
        try:
            # 1. Zuerst den Header der Nachricht lesen (Bsp.: "IMG alice 1024\n")
            header = client_socket.recv(1024).decode().strip()
            print(f"Empfangener Header: {header}")

            if header.startswith("IMG"):
                parts = header.split(" ")
                if len(parts) != 3:
                    print("Ungültige IMG-Nachricht")
                    return

                sender = parts[1]
                size = int(parts[2])
                print(f"Bild von {sender}, Größe: {size} Bytes")

                # 2. Bilddaten empfangen
                image_data = self.recv_exact_bytes(client_socket, size)

                # 3. Bild speichern (optional)
                with open(f"empfangenes_bild_{sender}.jpg", "wb") as f:
                    f.write(image_data)
                print("Bild gespeichert.")

                # Bestätigungsnachricht an den Client senden
                client_socket.send(b"IMG_RECEIVED")

            else:
                # Andere Nachrichten (JOIN, MSG, etc.)
                print(f"Empfangene Daten: {header}")
                client_socket.send(b"Antwort vom Server")

        except Exception as e:
            print(f"Fehler beim Bearbeiten des Clients: {e}")
        
        finally:
            client_socket.close()
            print("Verbindung zum Client geschlossen.")

    # Methode, um exakt eine bestimmte Anzahl von Bytes zu empfangen
    def recv_exact_bytes(self, client_socket, total_bytes):
        """
        Empfängt exakt total_bytes vom Socket, auch wenn recv in kleinen Stücken kommt.
        """
        data = b''
        while len(data) < total_bytes:
            chunk = client_socket.recv(min(4096, total_bytes - len(data)))
            if not chunk:
                raise ConnectionError("Verbindung unterbrochen während Bildübertragung")
            data += chunk
        return data

    # Methode zum empfangen von Daten
    def recv_data(self, client_socket):
        alleDaten = b''
        while True:
            daten = client_socket.recv(1024)
            if not daten:
                break
            alleDaten += daten
        return alleDaten
    
    # Schließt den Server
    def close(self):
        self.socket.close()
        print("Server geschlossen")

# UDP-Responder für Discovery
def start_discovery_responder(listen_port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', listen_port)) 

    print(f"Discovery-Responder läuft auf UDP-Port {listen_port}")

    while True:
        data, addr = sock.recvfrom(1024)
        if data == b"DISCOVER_SERVICE":
            print(f"Anfrage von {addr} erhalten")
            sock.sendto(b"DISCOVER_RESPONSE", addr)

# Starte den UDP-Discovery-Responder
start_discovery_responder(5000)
