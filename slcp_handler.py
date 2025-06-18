# File: slcp_handler.py

"""
SLCP (Simple LAN Chat Protocol) Handler

Bietet Funktionen, um SLCP-Text-Befehle (JOIN, LEAVE, WHO, KNOWUSERS, MSG, IMG)
aufzubauen und einzeln zu parsen.
Als erstes werden Methoden erstellt, die Nachrichten im SLCP-Format formatieren. 
Die letzte Methode `parse_slcp_line` parst eine einzelne SLCP-Zeile in Befehl und Argumente.


Ein normaler String ist nicht bereit für den Transport im Netzwerk und muss daher in Bytes umgewandelt werden.
Netzwerke wie UDP  und TCP nehmen nur Bytes entgegen und können keine Textobjekte verarbeiten, daher müssen alle Nachrichten in Bytes umgewandelt werden.
Das umwandeln der Strings in Bytes erfolgt mit der `.encode`-Methode, die einen String in Bytes umwandelt und dabei eine Kodierung angibt, in diesem Fall 'utf-8'.
Jede Methode hat als Rückgabewert das finale Format der SLCP Nachricht als Bytes. 
"""

def build_join(handle: str, port: int) -> bytes:    # Da .encode ein Byte Objekt erzeugt wird hier der Rückgabetyp als bytes angegeben.
    """Erzeugt eine JOIN-Nachricht."""
    return f"JOIN {handle} {port}\n".encode('utf-8')

def build_leave(handle: str) -> bytes:
    """Erzeugt eine LEAVE-Nachricht."""
    return f"LEAVE {handle}\n".encode('utf-8')  # Das f am Rückgabewert steht für 'formated String' und ermöglicht es, Variablen direkt in den String einzufügen.

def build_who() -> bytes:
    """Erzeugt eine WHO-Nachricht."""
    return b"WHO\n"  # Das b vor dem String kennzeichnet, dass es sich um Bytes handelt. Hier werden keine Variablen eingefügt, daher ist kein f notwendig.

"""
Aus einer Datenstruktur (Dictionary) wird ein formatierter String erzeugt, der dann per Netzwerk versendet wird. 
Die Methode greift auf die Liste der bekannten Peers (Also die Teilnehmer im Netzwerk) zu und formatiert in das Format: handle:host:port
Das Format des Dictonary hängt davon ab, wie die Methode instanziert wird und wird nicht im SLCP Handler bestimmt. 
Die for-Schleife durchläuft jeden key (Also h für handle) und jeder value ist das Tupel bestehend aus host und port.
Peers.items() representiert hierbei alle Schlüsselwerte-Paare des Dictionaries.
"""

def build_knowusers(peers: dict) -> bytes:
    """
    Erzeugt eine KNOWUSERS-Antwort mit allen (handle:host:port)-Paaren,
    kommagetrennt.
    """
    parts = []                                      # Initialisiert eine leere Liste, in der die formatierten Strings gespeichert werden.
    for h, (host, port) in peers.items():
        parts.append(f"{h}:{host}:{port}")          # Fügt der Liste einen formatierten String hinzu, der das handle, den host und den port enthält.
    payload = ",".join(parts)                       # Verbindet alle formatierten Strings in der Liste mit einem Komma.
    return f"KNOWUSERS {payload}\n".encode('utf-8') # Hier wird wieder das f für 'formated String' verwendet, um den finalen String zu erstellen, der dann in Bytes umgewandelt wird.

def build_msg(from_handle: str, text: str) -> bytes:
    """Erzeugt eine MSG-Nachricht."""
    return f"MSG {from_handle} {text}\n".encode('utf-8')

def build_img(from_handle: str, size: int) -> bytes:
    """Erzeugt eine IMG-Header-Nachricht mit angegebener Größe."""
    return f"IMG {from_handle} {size}\n".encode('utf-8')

"""
Die Parse Methode nimmt eine einzelne SLCP-Zeile als String entgegen und zerlegt sie in den Befehl (cmd) und die Argumente (args_list).
Ziel ist es empfangene SLCP Nachrichten verständlich für die Anwendung zu machen, indem sie in Befehl und Argumente zerlegt werden.

"""

def parse_slcp_line(line: str):
    """
    Parst eine einzelne SLCP-Zeile in (cmd, args_list).
    Rückgabe: (Befehl, Liste der Argumente als Strings).
    """
    tokens = line.strip().split(' ', 2)              # Entfernt führende und nachgestellte Leerzeichen oder Zeilenumbrüche und trennt die Zeile an maximal zwei Leerzeichen, sodass am Ende maximal 3 Teile entstehen
    cmd = tokens[0]                          # Der Befehl ist das erste Element der Liste 
    args = tokens[1:] if len(tokens) > 1 else []     # Hier wird geprüft ob die Nachricht mehr als ein Element hat, wenn ja, wird alles außer dem ersten Element als Argumente genommen, ansonsten ist die Liste leer.
    return cmd, args                  # Ausgabe des Tupels, Beispiel der Ausgabe: "JOIN", ["Alice", "5000"]