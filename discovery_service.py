import socket
import time
import toml
config = toml.load("config.toml")

class DiscoveryService:
    def __init__(self, timeout=10, discovery_port=int(config["discovery_port"])):
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
            
            data, addr = self.sock.recvfrom(4001)
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
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass  # SO_REUSEPORT gibt es nicht auf allen Systemen
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('',self.discovery_port))
        sock.settimeout(self.timeout)

        print(f"Starte Peer-Suche (Timeout: {self.timeout} Sekunden)...")
        
        try:
            # Sende Discovery Nachricht
            sock.sendto(message, ('255.255.255.255', self.discovery_port))
            
            # Warte auf Antworten bis Timeout
            start_time = time.time()
            while (time.time() - start_time) < self.timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    #Erwarteter Response: "DISCOVER_RESPONSE <tcp_port>"
                    parts = data.decode().split()
                    if parts[0] == "DISCOVER_RESPONSE" and len(parts)>= 2:
                        tcp_port =int(parts[1])
                        #Speichere als tuple: (IP, TCP-Port)
                        if (addr[0], tcp_port) not in found_peers:
                            found_peers.append((addr[0], tcp_port))
                            print(f"Peer gefunden: {addr[0]}:{tcp_port}")
                except socket.timeout:
                    # Timeout für einen einzelnen Empfangsversuch
                    break   
        except KeyboardInterrupt:
            print("\nSuche wurde vom Benutzer beendet.")
        finally:
            print(f"\nSuche beendet nach {time.time() - start_time:.1f} Sekunden.")
            sock.close()
            
        return found_peers