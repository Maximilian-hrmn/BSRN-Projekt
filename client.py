import socket

class SLCPClient:

#Konstruktor des Clients
    def __init__(self, peer_ip, peer_port):
        self.peer_ip = peer_ip
        self.peer_port = peer_port
#Methode zum Senden von Nachrichten
    def send_message(self, message):
        try:
            # 1. Socket erstellen
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # 2. Verbindung zum Peer aufbauen
                s.connect((self.peer_ip, self.peer_port))

                # 3. Nachricht senden (als Byte-String mit Zeilenende)
                s.sendall((message + '\n').encode('utf-8'))

                # 4. Antwort empfangen
                response = s.recv(1024).decode('utf-8').strip()

                return response

        except Exception as e:
            print(f"[Fehler] Verbindung zu {self.peer_ip}:{self.peer_port} fehlgeschlagen:", e)
            return None
