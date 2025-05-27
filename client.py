import socket
import os

class SLCPClient:
    #Kontruktor für den Client
    def __init__(self, peer_ip, peer_port):
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.s = None

    #Methode zum verbinden
    def connect(self):
        if self.s is None:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.peer_ip, self.peer_port))

    #methode zu schließen
    def close(self):
        if self.s:
            self.s.close()
            self.s = None

    #Methode zum senden von Nachrichten
    def send_message(self, message):
        try:
            self.connect()
            self.s.sendall((message + '\n').encode('utf-8'))
            response = self.s.recv(1024).decode('utf-8').strip()
            return response
        except Exception as e:
            print(f"[Fehler] Verbindung zu {self.peer_ip}:{self.peer_port} fehlgeschlagen:", e)
            return None

    #Methode zum senden von Bildern
    def send_image(self, empfänger, bildpfad):
        try:
            self.connect()
            bildname = os.path.basename(bildpfad)
            bildgröße = os.path.getsize(bildpfad)
            with open(bildpfad, 'rb') as f:
                bilddaten = f.read()
            header = f"IMG {empfänger} {bildname} {bildgröße}\n"
            self.s.sendall(header.encode('utf-8'))
            self.s.sendall(bilddaten)
            response = self.s.recv(1024).decode('utf-8').strip()
            print(f"[Antwort vom Peer]: {response}")
        except Exception as e:
            print(f"[Fehler beim Bildversand]: {e}")

# ========== HIER KOMMEN DIE FUNKTIONEN, die CLI aufruft ==========

PEER_IP = "127.0.0.1"
PEER_PORT = 5000
client = SLCPClient(PEER_IP, PEER_PORT)

def send_join(handle):
    response = client.send_message(f"JOIN {handle}")
    if response:
        print(f"[Antwort vom Peer]: {response}")
    else:
        print("[Info] JOIN gesendet (keine Antwort erhalten)")

def send_msg(empfänger, text):
    response = client.send_message(f"MSG {empfänger} {text}")
    if response:
        print(f"[Antwort vom Peer]: {response}")
    else:
        print("[Info] Nachricht gesendet (keine Antwort erhalten)")

def send_leave(handle):
    response = client.send_message(f"LEAVE {handle}")
    print("[Info] LEAVE gesendet.")
    client.close()