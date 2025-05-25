import socket
import threading
import time
import json
from typing import Dict, List, Callable, Optional, Tuple
from slcp_protocol import SLCPHandler


class NetworkCommunicator:
    """
    Netzwerk-Kommunikationsklasse für das SLCP P2P-Netzwerk.
    Verwaltet sowohl UDP- als auch TCP-Verbindungen und verwendet den SLCP Handler
    für Protokoll-Formatierung und -Parsing.
    """
    
    def __init__(self, handle: str, port: int, host: str = '0.0.0.0'):
        """
        Initialisiert den Netzwerk-Kommunikator.
        
        Args:
            handle: Benutzername im Netzwerk
            port: Port für eingehende Verbindungen
            host: Host-Adresse (Standard: alle Interfaces)
        """
        # SLCP Handler für Protokoll-Verarbeitung
        self.slcp = SLCPHandler(handle, port)
        
        # Netzwerk-Konfiguration
        self.host = host
        self.port = port
        self.handle = handle
        
        # Peer-Verwaltung: {handle: {'ip': str, 'port': int, 'last_seen': float}}
        self.peers: Dict[str, Dict] = {}
        
        # Socket-Verwaltung
        self.tcp_server_socket: Optional[socket.socket] = None
        self.udp_socket: Optional[socket.socket] = None
        
        # Thread-Verwaltung
        self.running = False
        self.server_thread: Optional[threading.Thread] = None
        self.udp_listener_thread: Optional[threading.Thread] = None
        
        # Callback-Funktionen für verschiedene Ereignisse
        self.message_callbacks: List[Callable] = []
        self.peer_join_callbacks: List[Callable] = []
        self.peer_leave_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # Lock für Thread-sichere Operationen
        self.peers_lock = threading.Lock()
    
    def start(self) -> bool:
        """
        Startet die Netzwerk-Kommunikation (TCP-Server und UDP-Listener).
        
        Returns:
            True bei erfolgreichem Start, False bei Fehlern
        """
        try:
            # Starte TCP-Server für eingehende Verbindungen
            self._start_tcp_server()
            
            # Starte UDP-Socket für Discovery und Broadcast
            self._start_udp_listener()
            
            self.running = True
            print(f"Netzwerk-Kommunikation gestartet auf {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Starten der Netzwerk-Kommunikation: {e}")
            self._trigger_error_callbacks(f"Start-Fehler: {e}")
            return False
    
    def stop(self):
        """
        Stoppt alle Netzwerk-Operationen und schließt Sockets.
        """
        print("Stoppe Netzwerk-Kommunikation...")
        self.running = False
        
        # Sende LEAVE-Nachricht an alle bekannten Peers
        self._broadcast_leave()
        
        # Schließe Sockets
        if self.tcp_server_socket:
            self.tcp_server_socket.close()
        if self.udp_socket:
            self.udp_socket.close()
        
        # Warte auf Thread-Beendigung
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)
        if self.udp_listener_thread and self.udp_listener_thread.is_alive():
            self.udp_listener_thread.join(timeout=2)
        
        print("Netzwerk-Kommunikation gestoppt")
    
    # --- TCP-Server für eingehende Verbindungen ---
    def _start_tcp_server(self):
        """
        Startet den TCP-Server für eingehende Peer-Verbindungen.
        """
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server_socket.bind((self.host, self.port))
        self.tcp_server_socket.listen(10)  # Bis zu 10 wartende Verbindungen
        
        # Starte Server-Thread
        self.server_thread = threading.Thread(target=self._tcp_server_loop, daemon=True)
        self.server_thread.start()
    
    def _tcp_server_loop(self):
        """
        Hauptschleife des TCP-Servers. Akzeptiert eingehende Verbindungen.
        """
        while self.running:
            try:
                # Setze Timeout für accept(), damit wir regelmäßig prüfen können, ob wir noch laufen sollen
                self.tcp_server_socket.settimeout(1.0)
                client_socket, client_address = self.tcp_server_socket.accept()
                
                # Starte Thread für jeden Client
                client_thread = threading.Thread(
                    target=self._handle_tcp_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                # Timeout ist normal - prüfe einfach weiter
                continue
            except Exception as e:
                if self.running:  # Nur loggen, wenn wir noch laufen (nicht beim Shutdown)
                    print(f"Fehler im TCP-Server: {e}")
                    self._trigger_error_callbacks(f"TCP-Server Fehler: {e}")
    
    def _handle_tcp_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """
        Verarbeitet Nachrichten von einem TCP-Client.
        
        Args:
            client_socket: Socket der Client-Verbindung
            client_address: Adresse des Clients (IP, Port)
        """
        try:
            while self.running:
                # Empfange Daten vom Client
                data = client_socket.recv(4096)
                if not data:
                    break  # Client hat Verbindung geschlossen
                
                # Dekodiere Nachricht
                message = data.decode('utf-8').strip()
                if not message:
                    continue
                
                # Verwende SLCP Handler zum Parsen der Nachricht
                parsed_message = self.slcp.parse_message(message)
                
                # Verarbeite die geparste Nachricht
                self._process_parsed_message(parsed_message, client_address[0])
                
        except Exception as e:
            print(f"Fehler bei TCP-Client {client_address}: {e}")
            self._trigger_error_callbacks(f"TCP-Client Fehler: {e}")
        finally:
            client_socket.close()
    
    # --- UDP für Discovery und Broadcast ---
    def _start_udp_listener(self):
        """
        Startet den UDP-Listener für Discovery-Nachrichten.
        """
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Für Broadcast-Empfang
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind((self.host, self.port + 1))  # UDP auf Port+1
        
        # Starte UDP-Listener-Thread
        self.udp_listener_thread = threading.Thread(target=self._udp_listener_loop, daemon=True)
        self.udp_listener_thread.start()
    
    def _udp_listener_loop(self):
        """
        Hauptschleife des UDP-Listeners für Discovery-Nachrichten.
        """
        while self.running:
            try:
                # Setze Timeout für Empfang
                self.udp_socket.settimeout(1.0)
                data, address = self.udp_socket.recvfrom(1024)
                
                # Dekodiere und parse Nachricht
                message = data.decode('utf-8').strip()
                parsed_message = self.slcp.parse_message(message)
                
                # Verarbeite Discovery-Nachrichten
                self._process_parsed_message(parsed_message, address[0])
                
            except socket.timeout:
                # Timeout ist normal - prüfe einfach weiter
                continue
            except Exception as e:
                if self.running:
                    print(f"Fehler im UDP-Listener: {e}")
                    self._trigger_error_callbacks(f"UDP-Listener Fehler: {e}")
    
    # --- Nachrichtenverarbeitung ---
    def _process_parsed_message(self, parsed_message: Dict, sender_ip: str):
        """
        Verarbeitet eine geparste SLCP-Nachricht basierend auf ihrem Typ.
        
        Args:
            parsed_message: Von SLCP Handler geparste Nachricht
            sender_ip: IP-Adresse des Senders
        """
        if parsed_message["command"] == "ERROR":
            print(f"Parsing-Fehler: {parsed_message['error']}")
            return
        
        command = parsed_message["command"]
        
        if command == "JOIN":
            # Ein neuer Peer möchte dem Netzwerk beitreten
            handle = parsed_message["handle"]
            port = parsed_message["port"]
            
            # Registriere Peer
            with self.peers_lock:
                self.peers[handle] = {
                    'ip': sender_ip,
                    'port': port,
                    'last_seen': time.time()
                }
            
            print(f"Peer {handle} ist dem Netzwerk beigetreten ({sender_ip}:{port})")
            self._trigger_peer_join_callbacks(handle, sender_ip, port)
            
            # Antworte mit IAM-Nachricht
            self._send_iam_to_peer(sender_ip, port)
        
        elif command == "LEAVE":
            # Ein Peer verlässt das Netzwerk
            handle = parsed_message["handle"]
            
            with self.peers_lock:
                if handle in self.peers:
                    del self.peers[handle]
            
            print(f"Peer {handle} hat das Netzwerk verlassen")
            self._trigger_peer_leave_callbacks(handle)
        
        elif command == "MSG":
            # Textnachricht empfangen
            sender_handle = parsed_message["handle"]
            message_text = parsed_message["text"]
            
            print(f"Nachricht von {sender_handle}: {message_text}")
            self._trigger_message_callbacks(sender_handle, message_text)
        
        elif command == "IAM":
            # Peer stellt sich vor
            handle = parsed_message["handle"]
            ip = parsed_message["ip"]
            port = parsed_message["port"]
            
            with self.peers_lock:
                self.peers[handle] = {
                    'ip': ip,
                    'port': port,
                    'last_seen': time.time()
                }
            
            print(f"Peer {handle} registriert: {ip}:{port}")
        
        elif command == "WHOIS":
            # Jemand fragt nach Informationen über einen Peer
            target_handle = parsed_message["handle"]
            # In einer vollständigen Implementierung würde hier eine Antwort gesendet
            print(f"WHOIS-Anfrage für {target_handle}")
        
        elif command == "IMG":
            # Bildübertragung (vereinfacht)
            sender_handle = parsed_message["handle"]
            image_size = parsed_message["size"]
            print(f"Bildübertragung von {sender_handle}, Größe: {image_size} Bytes")
    
    # --- Ausgehende Nachrichten ---
    def send_message(self, target_handle: str, message: str) -> bool:
        """
        Sendet eine Textnachricht an einen bestimmten Peer.
        
        Args:
            target_handle: Handle des Ziel-Peers
            message: Zu sendende Nachricht
            
        Returns:
            True bei erfolgreichem Versand, False bei Fehlern
        """
        # Finde Peer-Informationen
        with self.peers_lock:
            if target_handle not in self.peers:
                print(f"Peer {target_handle} nicht gefunden")
                return False
            
            peer_info = self.peers[target_handle]
        
        # Erstelle SLCP-Nachricht
        slcp_message = self.slcp.create_msg(target_handle, message)
        
        # Sende über TCP
        return self._send_tcp_message(peer_info['ip'], peer_info['port'], slcp_message)
    
    def join_network(self, discovery_ip: str = '255.255.255.255', discovery_port: int = None) -> bool:
        """
        Tritt dem Netzwerk bei, indem eine JOIN-Nachricht gesendet wird.
        
        Args:
            discovery_ip: IP für Discovery (Standard: Broadcast)
            discovery_port: Port für Discovery (Standard: unser UDP-Port)
            
        Returns:
            True bei erfolgreichem Beitritt
        """
        if discovery_port is None:
            discovery_port = self.port + 1
        
        # Erstelle JOIN-Nachricht
        join_message = self.slcp.create_join()
        
        # Sende als UDP-Broadcast
        return self._send_udp_message(discovery_ip, discovery_port, join_message)
    
    def leave_network(self):
        """
        Verlässt das Netzwerk durch Senden einer LEAVE-Nachricht an alle Peers.
        """
        self._broadcast_leave()
    
    def _send_tcp_message(self, ip: str, port: int, message: str) -> bool:
        """
        Sendet eine Nachricht über TCP an einen spezifischen Peer.
        
        Args:
            ip: Ziel-IP
            port: Ziel-Port
            message: Zu sendende Nachricht
            
        Returns:
            True bei Erfolg, False bei Fehlern
        """
        try:
            # Erstelle TCP-Verbindung
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.settimeout(5.0)  # 5 Sekunden Timeout
            tcp_socket.connect((ip, port))
            
            # Sende Nachricht
            tcp_socket.send(message.encode('utf-8'))
            tcp_socket.close()
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Senden der TCP-Nachricht an {ip}:{port}: {e}")
            self._trigger_error_callbacks(f"TCP-Send Fehler: {e}")
            return False
    
    def _send_udp_message(self, ip: str, port: int, message: str) -> bool:
        """
        Sendet eine Nachricht über UDP.
        
        Args:
            ip: Ziel-IP
            port: Ziel-Port
            message: Zu sendende Nachricht
            
        Returns:
            True bei Erfolg, False bei Fehlern
        """
        try:
            # Erstelle temporären UDP-Socket für Senden
            udp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_send_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Sende Nachricht
            udp_send_socket.sendto(message.encode('utf-8'), (ip, port))
            udp_send_socket.close()
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Senden der UDP-Nachricht an {ip}:{port}: {e}")
            self._trigger_error_callbacks(f"UDP-Send Fehler: {e}")
            return False
    
    def _send_iam_to_peer(self, peer_ip: str, peer_port: int):
        """
        Sendet eine IAM-Nachricht an einen Peer als Antwort auf JOIN.
        
        Args:
            peer_ip: IP des Peers
            peer_port: Port des Peers
        """
        # Ermittle eigene externe IP (vereinfacht)
        try:
            # Erstelle temporäre Verbindung, um eigene IP zu ermitteln
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            own_ip = temp_socket.getsockname()[0]
            temp_socket.close()
        except:
            own_ip = "127.0.0.1"  # Fallback
        
        # Erstelle und sende IAM-Nachricht
        iam_message = self.slcp.create_iam(own_ip)
        self._send_tcp_message(peer_ip, peer_port, iam_message)
    
    def _broadcast_leave(self):
        """
        Sendet LEAVE-Nachricht an alle bekannten Peers.
        """
        leave_message = self.slcp.create_leave()
        
        with self.peers_lock:
            for handle, peer_info in self.peers.items():
                self._send_tcp_message(peer_info['ip'], peer_info['port'], leave_message)
    
    # --- Callback-Verwaltung ---
    def add_message_callback(self, callback: Callable[[str, str], None]):
        """Fügt Callback für empfangene Nachrichten hinzu."""
        self.message_callbacks.append(callback)
    
    def add_peer_join_callback(self, callback: Callable[[str, str, int], None]):
        """Fügt Callback für neue Peers hinzu."""
        self.peer_join_callbacks.append(callback)
    
    def add_peer_leave_callback(self, callback: Callable[[str], None]):
        """Fügt Callback für verlassende Peers hinzu."""
        self.peer_leave_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]):
        """Fügt Callback für Fehler hinzu."""
        self.error_callbacks.append(callback)
    
    def _trigger_message_callbacks(self, sender: str, message: str):
        """Löst alle Message-Callbacks aus."""
        for callback in self.message_callbacks:
            try:
                callback(sender, message)
            except Exception as e:
                print(f"Fehler in Message-Callback: {e}")
    
    def _trigger_peer_join_callbacks(self, handle: str, ip: str, port: int):
        """Löst alle Peer-Join-Callbacks aus."""
        for callback in self.peer_join_callbacks:
            try:
                callback(handle, ip, port)
            except Exception as e:
                print(f"Fehler in Peer-Join-Callback: {e}")
    
    def _trigger_peer_leave_callbacks(self, handle: str):
        """Löst alle Peer-Leave-Callbacks aus."""
        for callback in self.peer_leave_callbacks:
            try:
                callback(handle)
            except Exception as e:
                print(f"Fehler in Peer-Leave-Callback: {e}")
    
    def _trigger_error_callbacks(self, error_message: str):
        """Löst alle Error-Callbacks aus."""
        for callback in self.error_callbacks:
            try:
                callback(error_message)
            except Exception as e:
                print(f"Fehler in Error-Callback: {e}")
    
    # --- Hilfsmethoden ---
    def get_peers(self) -> Dict[str, Dict]:
        """
        Gibt eine Kopie der aktuellen Peer-Liste zurück.
        
        Returns:
            Dictionary mit Peer-Informationen
        """
        with self.peers_lock:
            return self.peers.copy()
    
    def is_running(self) -> bool:
        """
        Überprüft, ob die Netzwerk-Kommunikation läuft.
        
        Returns:
            True wenn aktiv, False wenn gestoppt
        """
        return self.running