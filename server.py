import socket

class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.socket.bind((self.ip, self.port))
        print(f"Server gebunden an {self.ip}:{self.port}")

    def listen(self):
        self.socket.listen()
        print("Server wartet auf Verbindung")
        
    def accept_connection(self):
            client_socket, client_address = self.socket.accept()
            print(f"Verbindung erfolgreich hergestellt mit {client_address}")

    def recv_data(self, client_socket):
        alleDaten = b''
        while True:
            
            daten = client_socket.recv(1024)
            alleDaten += daten
            if not daten:
                break
        return alleDaten
    
    def close(self):
        self.socket.close()
        print("Server geschlossen")
    
