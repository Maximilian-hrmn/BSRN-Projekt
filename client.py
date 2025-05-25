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

# ========== HIER KOMMEN DIE FUNKTIONEN, die CLI aufruft ==========

# Fester Ziel-Peer (später dynamisch mit WHO!)
PEER_IP = "127.0.0.1"
PEER_PORT = 111

# Diese Funktion wird von CLI.py aufgerufen
def send_msg(empfänger, text):
    message = f"MSG {empfänger} {text}"
    client = SLCPClient(PEER_IP, PEER_PORT)
    response = client.send_message(message)

    if response:
        print(f"[Antwort vom Peer]: {response}")
    else:
        print("[Info] Nachricht gesendet (keine Antwort erhalten)")

# Diese Funktion wird von CLI.py aufgerufen
def send_leave(handle):
    message = f"LEAVE {handle}"
    client = SLCPClient(PEER_IP, PEER_PORT)
    client.send_message(message)
    print("[Info] LEAVE gesendet.")
