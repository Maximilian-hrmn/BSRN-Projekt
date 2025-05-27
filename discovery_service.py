import socket
import time

class DiscoveryService:
    def __init__(self, timeout=30, discovery_port=5000):
        # Initialisierung der Klassenvariablen
        self.timeout = timeout
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
        """Sucht nach verfügbaren Peers im Netzwerk für eine bestimmte Zeit"""
        message = b"DISCOVERY_SERVICE"
        found_peers = []
        
        # Socket für Broadcast konfigurieren
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.discovery_port))

        print(f"Starte Peer-Suche (Timeout: {self.timeout} Sekunden)...")
        
        try:
            # Sende Discovery Nachricht
            self.sock.sendto(message, ('255.255.255.255', self.discovery_port))
            
            # Warte auf Antworten bis Timeout
            start_time = time.time()
            while (time.time() - start_time) < self.timeout:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    if data == b"DISCOVER_RESPONSE":
                        if addr[0] not in found_peers:
                            found_peers.append(addr[0])
                            print(f"Peer gefunden: {addr[0]}")
                except socket.timeout:
                    # Timeout für einen einzelnen Empfangsversuch
                    continue
                
        except KeyboardInterrupt:
            print("\nSuche wurde vom Benutzer beendet.")
        finally:
            print(f"\nSuche beendet nach {time.time() - start_time:.1f} Sekunden.")
            self.sock.close()
            
        return found_peers
