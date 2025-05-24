import socket
import time

def discover_peers(timeout=2, discovery_port=5000):
    # Erstellt einen UDP-Socket für Broadcast-Nachrichten
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Aktiviert die Broadcast-Option für den Socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Setzt ein Timeout für den Socket (wie lange auf Antworten gewartet wird)
    sock.settimeout(timeout)

    # Die Nachricht, die an alle gesendet wird, um nach Peers zu suchen
    message = b"DISCOVERY_SERVICE"
    # Sendet die Broadcast-Nachricht an das Netzwerk auf dem angegebenen Port
    sock.sendto(message, ('<broadcast>', discovery_port))

    found_peers = []  # Liste für gefundene Peers

    print("Sende Discovery-Anfrage...")

    start = time.time()  # Startzeit für die Suche
    while True:
        try:
            # Wartet auf eine Antwort von einem Peer
            data, addr = sock.recvfrom(1024)
            # Prüft, ob die Antwort die erwartete Nachricht ist
            if data == b"DISCOVER_RESPONSE":
                found_peers.append(addr[0])  # Fügt die IP-Adresse des Peers zur Liste hinzu
                print(f"Peer gefunden: {addr[0]}")
        except socket.timeout: 
            # Wenn das Timeout erreicht ist, wird die Suche beendet
            print("Discovery-Zeitüberschreitung.")
            break

    sock.close()  # Schließt den Socket
    return found_peers  # Gibt die Liste der gefundenen Peers zurück

