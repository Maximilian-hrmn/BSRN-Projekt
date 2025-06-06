# File: slcp_handler.py

"""
SLCP (Simple LAN Chat Protocol) Handler

Bietet Funktionen, um SLCP-Text-Befehle (JOIN, LEAVE, WHO, KNOWUSERS, MSG, IMG)
aufzubauen und einzeln zu parsen.
"""

def build_join(handle: str, port: int) -> bytes:
    """Erzeugt eine JOIN-Nachricht."""
    return f"JOIN {handle} {port}\n".encode('utf-8')

def build_leave(handle: str) -> bytes:
    """Erzeugt eine LEAVE-Nachricht."""
    return f"LEAVE {handle}\n".encode('utf-8')

def build_who() -> bytes:
    """Erzeugt eine WHO-Nachricht."""
    return b"WHO\n"

def build_knowusers(peers: dict) -> bytes:
    """
    Erzeugt eine KNOWUSERS-Antwort mit allen (handle:host:port)-Paaren,
    kommagetrennt.
    """
    parts = []
    for h, (host, port) in peers.items():
        parts.append(f"{h}:{host}:{port}")
    payload = ",".join(parts)
    return f"KNOWUSERS {payload}\n".encode('utf-8')

def build_msg(from_handle: str, text: str) -> bytes:
    """Erzeugt eine MSG-Nachricht."""
    return f"MSG {from_handle} {text}\n".encode('utf-8')

def build_img(from_handle: str, size: int) -> bytes:
    """Erzeugt eine IMG-Header-Nachricht mit angegebener Größe."""
    return f"IMG {from_handle} {size}\n".encode('utf-8')

def parse_slcp_line(line: str):
    """
    Parst eine einzelne SLCP-Zeile in (cmd, args_list).
    Rückgabe: (Befehl, Liste der Argumente als Strings).
    """
    tokens = line.strip().split(' ', 2)
    cmd = tokens[0]
    args = tokens[1:] if len(tokens) > 1 else []
    return cmd, args
