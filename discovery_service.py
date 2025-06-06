# File: discovery_service.py

import socket
import time
from slcp_handler import parse_slcp_line, build_knowusers
import toml
<<<<<<< HEAD

"""
Discovery Service:

- Lauscht per UDP auf config['whoisport'] (z. B. Port 4000) auf Broadcasts.
- Verarbeitet SLCP-Befehle: JOIN, WHO, LEAVE.
- Speichert eine lokale Peerliste mapping handle -> (IP, Port).
- Sendet KNOWUSERS-Antworten per Unicast an anfragenden Peer.
"""

def discovery_loop(config, cli_queue):
    peers = {}  # handle -> (host, port)
    whoisport = config['whoisport']

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", whoisport))

    while True:
        data, addr = sock.recvfrom(65535)
        try:
            line = data.decode('utf-8')
            cmd, args = parse_slcp_line(line)
        except:
            continue

        if cmd == 'JOIN' and len(args) == 2:
            new_handle = args[0]
            new_port = int(args[1])
            peers[new_handle] = (addr[0], new_port)
            # Sende KNOWUSERS an neuen Peer:
            response = build_knowusers(peers)
            sock.sendto(response, (addr[0], new_port))

        elif cmd == 'WHO':
            # Sende KNOWUSERS an Anfragenden zurück
            response = build_knowusers(peers)
            sock.sendto(response, addr)

        elif cmd == 'LEAVE' and len(args) == 1:
            leaving = args[0]
            if leaving in peers:
                del peers[leaving]

        # Wenn Peerliste sich ändert, sende Kopie an CLI
        cli_queue.put(('PEERS', peers.copy()))

if __name__ == '__main__':
    config = toml.load('config.toml')
    from multiprocessing import Queue
    q = Queue()
    discovery_loop(config, q)
=======
from typing import List, Tuple
from typing import Optional

config = toml.load("config.toml")

class DiscoveryService:
    def __init__(self, timeout: int = 10, discovery_port: int = int(config["discovery_port"])):
        self.timeout = timeout
        self.discovery_port = discovery_port
        self.found_peers = []
        
        # Socket für Broadcast konfigurieren
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass  # SO_REUSEPORT nicht auf allen Systemen verfügbar
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(self.timeout)

    def get_broadcast_address(self) -> str:
        """Ermittelt die korrekte Broadcast-Adresse für das Netzwerk"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 1))  # Verbindung zu einem externen Server
                ip = s.getsockname()[0]
                return '.'.join(ip.split('.')[:-1]) + '.255'
        except Exception:
            return '255.255.255.255'  # Fallback auf Standard-Broadcast

    def send_who(self, peer_address: str) -> Optional[str]:
        """
        Sendet eine WHO-Anfrage an einen spezifischen Peer
        
        Args:
            peer_address: IP-Adresse des Peers
            
        Returns:
            Peer-Info als String oder None bei Fehler
        """
        try:
            who_message = b"WHO"
            self.sock.sendto(who_message, (peer_address, self.discovery_port))
            
            data, addr = self.sock.recvfrom(1024)
            if data.startswith(b"WHO_RESPONSE:"):
                peer_info = data.decode('utf-8').split(':', 1)[1]
                print(f"[DISCOVERY] Peer Info von {addr[0]}: {peer_info}")
                return peer_info
                
        except socket.timeout:
            print(f"[DISCOVERY] Keine Antwort von {peer_address} erhalten")
        except Exception as e:
            print(f"[DISCOVERY] Fehler bei WHO-Anfrage: {e}")
        
        return None

    def discover_peers(self) -> List[Tuple[str, int]]:
        """
        Sucht nach verfügbaren Peers im Netzwerk
        
        Returns:
            Liste von gefundenen Peers als (IP, Port) Tupel
        """
        message = b"DISCOVERY_SERVICE"
        found_peers = []
        broadcast_ip = self.get_broadcast_address()

        print(f"[DISCOVERY] Starte Peer-Suche (Timeout: {self.timeout}s, Broadcast: {broadcast_ip})")

        try:
            # Sende Discovery-Nachricht an Broadcast-Adresse
            self.sock.sendto(message, (broadcast_ip, self.discovery_port))
            
            # Warte auf Antworten bis Timeout
            start_time = time.time()
            while (time.time() - start_time) < self.timeout:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    decoded_data = data.decode('utf-8').strip()
                    print(f"[DISCOVERY] Empfangen von {addr[0]}: {decoded_data}")
                    
                    # Erwarteter Response: "DISCOVER_RESPONSE <tcp_port>"
                    parts = decoded_data.split()
                    if parts[0] == "DISCOVER_RESPONSE" and len(parts) >= 2:
                        try:
                            tcp_port = int(parts[1])
                            peer = (addr[0], tcp_port)
                            
                            if peer not in found_peers:
                                found_peers.append(peer)
                                print(f"[DISCOVERY] Peer gefunden: {addr[0]}:{tcp_port}")
                        except ValueError:
                            print(f"[DISCOVERY] Ungültiger Port in Antwort: {parts[1]}")
                except socket.timeout:
                    continue  # Weiter warten bis Gesamt-Timeout
                    
        except KeyboardInterrupt:
            print("\n[DISCOVERY] Suche vom Benutzer abgebrochen")
        except Exception as e:
            print(f"[DISCOVERY] Fehler während der Suche: {e}")
        finally:
            elapsed = time.time() - start_time
            print(f"[DISCOVERY] Suche beendet nach {elapsed:.1f}s. Gefundene Peers: {len(found_peers)}")
            
            # Filtere ungültige Adressen
            valid_peers = []
            my_ip = self._get_own_ip()
            for ip, port in found_peers:
                if ip != my_ip and not ip.startswith('127.') and ip != '0.0.0.0':
                    valid_peers.append((ip, port))
            
            return valid_peers

    def _get_own_ip(self) -> str:
        """Ermittelt die eigene IP-Adresse"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'

    def close(self):
        """Schließt den Socket"""
        if hasattr(self, 'sock') and self.sock:
            self.sock.close()
            print("[DISCOVERY] Socket geschlossen")
>>>>>>> e3e3d87472a639b4ced2beef1075e7f250613fe1
