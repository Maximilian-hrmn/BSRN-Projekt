import socket
import time

def discover_peers(timeout=2, discovery_port=5000):
    # Broadcast-UDP-Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    message = b"DISCOVER_SERVICE"
    sock.sendto(message, ('<broadcast>', discovery_port))

    found_peers = []

    print("Sende Discovery-Anfrage...")

    start = time.time()
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data == b"DISCOVER_RESPONSE":
                found_peers.append(addr[0])
                print(f"Peer gefunden: {addr[0]}")
        except socket.timeout:
            break

    sock.close()
    return found_peers

