import socket
import os

class SLCPClient:
    #Kontruktor für den Client
    def __init__(self, peer_ip, peer_port):
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.s = None
        self.handle = None

    #Methode zum verbinden
    def send_join(self, handle):
        self.handle = handle  # Handle speichern für spätere Nachrichten
        response = self.send_message(f"JOIN {handle}")
        if response:
            print(f"[Antwort vom Peer]: {response}")
        else:
            print("[Info] JOIN gesendet (keine Antwort erhalten)")

    #Methode zum verbinden mit dem Peer
    def send_msg(self, text):
        # Sende die Nachricht im Format: MSG <handle> <text>
        if not self.handle:
            print("[Fehler] Kein Handle gesetzt. Bitte zuerst JOIN senden.")
            return
        response = self.send_message(f"MSG {self.handle} {text}")
        if response:
            print(f"[Antwort vom Peer]: {response}")
        else:
            print("[Info] Nachricht gesendet (keine Antwort erhalten)")

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
            
    #Methode zum verlassen des Clients
    def send_leave(self):
        if not self.handle:
            print("[Fehler] Kein Handle gesetzt. Bitte zuerst JOIN senden.")
            return
        response = self.send_message(f"LEAVE {self.handle}")
        print("[Info] LEAVE gesendet.")
        self.close()


        
    #Hilfsmethode 
    def connect(self):
        if self.s is None:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.peer_ip, self.peer_port))

    def send_message(self, message):
        try:
            self.connect()
            self.s.sendall((message + "\n").encode("utf-8"))
            response = self.s.recv(1024).decode("utf-8").strip()
            return response
        except Exception as e:
            print(f"[Fehler beim Senden]: {e}")
            return None

    def close(self):
        if self.s:
            self.s.close()
            self.s = None