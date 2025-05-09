import socket
import threading

#Konstruktor eines Servers, er braucht dafür eine IP-Adresse und einen Port
class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Methode zum starten des Servers. Danach "lauscht" der Server nach Verbindungen
    def start(self):
        self.socket.bind((self.ip, self.port))
        self.socket.listen(5)
        print(f"Server gebunden an {self.ip}:{self.port}")

#Methode zum akzeptieren von Verbindungen
    def accept_connection(self):
        while True:
            client_socket, client_address = self.socket.accept()
            print(f"Verbindung erfolgreich hergestellt mit {client_address}")
            # Einen neuen Thread starten, um die Kommunikation mit dem Client zu behandeln
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

#Methode zum behandeln der Kommunikation mit dem Client
    def handle_client(self, client_socket):
        try:
            # Empfange Daten vom Client
            data = self.recv_data(client_socket)
            print(f"Empfangene Daten: {data.decode()}")
            # Sende eine Antwort
            client_socket.send(b"Antwort vom Server")
        finally:
            client_socket.close()
            print("Verbindung zum Client geschlossen.")

#Methode zum empfangen von Daten
    def recv_data(self, client_socket):
        alleDaten = b''
        while True:
            daten = client_socket.recv(1024)
            if not daten:
                break
            alleDaten += daten
        return alleDaten
    
#Schließt den Server
    def close(self):
        self.socket.close()
        print("Server geschlossen")

#UDP-Responder fuer Discovery
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
