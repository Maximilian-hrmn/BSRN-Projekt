import socket
import time

class DiscoveryService:
    def __init__(self, discovery_port=5000):
        # Initialisierung der Klassenvariablen
        self.discovery_port = discovery_port
        self.found_peers = []
        
        # Socket erstellen und konfigurieren
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(self.timeout)

    def send_who(self, peer_address):
        """Sendet eine WHO-Anfrage an einen spezifischen Peer"""
        try:
            who_message = b"WHO"
            self.sock.sendto(who_message, (peer_address, self.discovery_port))
            
            data, addr = self.sock.recvfrom(1024)
            if data.startswith(b"WHO_RESPONSE:"):
                peer_info = data.decode('utf-8').split(':')[1]
                print(f"Peer Info von {addr[0]}: {peer_info}")
                return peer_info
                
        except socket.timeout:
            print(f"Keine Antwort von {peer_address} erhalten")
        except Exception as e:
            print(f"Fehler beim Senden der WHO-Anfrage: {e}")
    
        return None

    def discover_peers(self):
        """Sucht nach verfügbaren Peers im Netzwerk"""
        # Die Nachricht, die an alle gesendet wird, um nach Peers zu suchen
        message = b"DISCOVERY_SERVICE"
        found_peers = []  # Liste für gefundene Peers

        print("Sende Discovery-Anfrage...")

        # Sende Discovery Nachricht
        self.sock.sendto(message, ('<broadcast>', self.discovery_port))

        start = time.time()  # Startzeit für die Suche
        
        while True:
            try:
                # Wartet auf eine Antwort von einem Peer
                data, addr = self.sock.recvfrom(1024)
                # Prüft, ob die Antwort die erwartete Nachricht ist
                if data == b"DISCOVER_RESPONSE":
                    if addr[0] not in found_peers:
                        found_peers.append(addr[0])  # Fügt die IP-Adresse des Peers zur Liste hinzu
                        print(f"Peer gefunden: {addr[0]}")
            except socket.timeout: 
                # Wenn das Timeout erreicht ist, wird die Suche beendet
                print("Discovery-Zeitüberschreitung.")
                break

        self.sock.close()  # Schließt den Socket
        return found_peers  # Gibt die Liste der gefundenen Peers zurück

