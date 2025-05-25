"""

Kurzbeschreibung des SLCP Handlers

ABLAUF des Programms in 4 Schritten

1. Initialisierung des Handlers:
 Der Handler wird mit einem Benutzernamen (handle) und einem Port initialisiert, über den die Kommunikation stattfindet.
    
    2. Validierung von Handle und Port:
        Das Programm prüft, ob der Handle ein gültiger String ist und ob der Port im gültigen Bereich (1-65535) liegt.
        Diese Validierung erfolgt direkt bei der Initialisierung, um frühzeitig Fehler zu erkennen.
       
         3. Nachrichtenerstellung:
            Die verschiedenen Methoden (create_join, create_leave, etc.) erstellen formatierte Nachrichten entsprechend dem SLCP-Protokoll,
            die dann über das Netzwerk gesendet werden können.

            4. Nachrichten Parsing:
            Die parse_message Methode erhält einen String und zerlegt diesen in seine Bestandteile.
            Die Methode erhält zunächst einen String wie z.B.: "JOIN alice 8080", dann wird dieser String "bereinigt" (mit .strip()). 
            Anschließend wird der Befhlt der Nachricht identifiziert, durch command = parts[0].upper(), je nach Befehlstyp wird die Nachricht unterschiedlich verarbeitet:
            (.WORK IN PROGRESS.)
            Im Wesentlichen wird eine Textzeile wie "MSG alice "Wie geht's dir?"" in ein strukturiertes 
            Objekt {"command": "MSG", "handle": "alice", "text": "Wie geht's dir?"} umgewandelt, das dann für die weitere Verarbeitung im 
            Programm verwendet werden kann.

                5.Strukturierte Rückgabe der ursprünglichen Nachricht:
                Beispiel: return {"command": "MSG", "handle": "bob", "text": "Hallo!"}

"""

from typing import Dict, List, Union, Optional, Any
import re

"""
Beschreibung der importierten Libraries:
Wir benötigen das typing-Modul, welches über eine vielzahl an (.WORK IN PROGRESS.)

Dict: Wird verwendet, um einen Dictonary Typ zu annotieren, also kennzeichnet z.B zwei Datentypen mit Schlüsseln, so wie eine Hash-Map in Java.

List: Kann Listen von Datentypen erzeugen (Ähnlich wie ArrayLists) 

Union: Ein Wert kann möglicherweise mehrere Datentypen besitzen (Bsp.: Union[str, int]).  Ein Wert kann in diesem Fall entweder ein String oder ein Integer sein.

Optional: Ähnlich wie Union, kann ein Optional[str] den Wert None oder String sein.

Any: Wird verwendet, wenn ein Wert jeden beliebigen Typ annehmen kann. Sollte sparsam benutzt werden.

import re: Importiert das Modul re (Regular Expressions). Dient zur Textverarbeitung und Analyse. Im SLCP Handler wird das Modul für zwei Hauptzwecke benutzt: 
   
     1: Nachrichtenverarbeitung: Besonders bei der MSG-Nachricht (.WORK IN PROGRESS.)

    2: IP-Validierung: In der _is_valid_ip-Methode nutzen wir einen regulären Ausdruck, um zu überprüfen,
     ob eine IP-Adresse dem Format x.x.x.x entspricht, wobei jedes x eine Zahl zwischen 0 und 255 sein sollte.

"""


class SLCPHandler:
    """
    Handler für das SLCP (Simple Line-based Chat Protocol).
    Ermöglicht das Erstellen und Parsen von Nachrichten im SLCP-Format.
    """
    def __init__(self, handle: str, port: int):
        """
        Initialisiert einen neuen SLCP-Handler.
        
        Args:
            handle: Benutzername/Identifikator im Netzwerk
            port: Port, auf dem der Client lauscht
        """
        # Validiere Input, um Fehler frühzeitig zu erkennen
        # Konstruktor

        if not handle or not isinstance(handle, str):
            raise ValueError("Handle muss ein gültiger String sein")
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError("Port muss eine gültige Zahl zwischen 1 und 65535 sein")
            
        self.handle = handle  # Speichere Benutzername
        self.port = port      # Speichere Port

   

   
    # --- 1. Nachrichtenerstellung ---
    # Jede Methode erstellt eine formatierte Nachricht gemäß SLCP-Protokoll
    
    def create_join(self) -> str:
        """
        Erstellt eine JOIN-Nachricht, um dem Netzwerk beizutreten.
        Format: JOIN <handle> <port>
        
        Returns:
            Formatierte JOIN-Nachricht
        """
        return f"JOIN {self.handle} {self.port}\n"

    def create_leave(self) -> str:
        """
        Erstellt eine LEAVE-Nachricht, um das Netzwerk zu verlassen.
        Format: LEAVE <handle>
        
        Returns:
            Formatierte LEAVE-Nachricht
        """
        return f"LEAVE {self.handle}\n"

    def create_msg(self, target_handle: str, message: str) -> str:
        """
        Erstellt eine MSG-Nachricht, um eine Textnachricht an einen Benutzer zu senden.
        Format: MSG <target_handle> "<message>"
        
        Args:
            target_handle: Empfänger der Nachricht
            message: Zu sendende Nachricht
            
        Returns:
            Formatierte MSG-Nachricht
        """
        # Validierung des Nachrichteninhalts
        if not target_handle:
            raise ValueError("Ziel-Handle darf nicht leer sein")
        if not message:
            raise ValueError("Nachricht darf nicht leer sein")
            
        # Escape Quotes in der Nachricht, damit sie korrekt im Protokoll dargestellt werden
        escaped_message = message.replace('"', '\\"')
        return f'MSG {target_handle} "{escaped_message}"\n'

    def create_img(self, target_handle: str, size: int) -> str:
        """
        Erstellt eine IMG-Nachricht, um ein Bild an einen Benutzer zu senden.
        Format: IMG <target_handle> <size>
        
        Args:
            target_handle: Empfänger des Bildes
            size: Größe des Bildes in Bytes
            
        Returns:
            Formatierte IMG-Nachricht
        """
        if not target_handle:
            raise ValueError("Ziel-Handle darf nicht leer sein")
        if not isinstance(size, int) or size <= 0:
            raise ValueError("Größe muss eine positive Zahl sein")
            
        return f"IMG {target_handle} {size}\n"

    def create_whois(self, target_handle: str) -> str:
        """
        Erstellt eine WHOIS-Nachricht, um Informationen über einen Benutzer abzufragen.
        Format: WHOIS <target_handle>
        
        Args:
            target_handle: Benutzer, über den Informationen angefordert werden
            
        Returns:
            Formatierte WHOIS-Nachricht
        """
        if not target_handle:
            raise ValueError("Ziel-Handle darf nicht leer sein")
            
        return f"WHOIS {target_handle}\n"

    def create_iam(self, ip: str) -> str:
        """
        Erstellt eine IAM-Nachricht, um die eigene Identität im Netzwerk bekannt zu geben.
        Format: IAM <handle> <ip> <port>
        
        Args:
            ip: IP-Adresse des Clients
            
        Returns:
            Formatierte IAM-Nachricht
        """
        if not ip or not self._is_valid_ip(ip):
            raise ValueError("Ungültige IP-Adresse")
            
        return f"IAM {self.handle} {ip} {self.port}\n"

   
    # --- 2. Nachricht parsing ---
    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        """
        Parsed eine SLCP-Nachricht und gibt ein Dictionary zurück.
        
        Ausgangslage:
            raw_message: Die zu parsende SLCP-Nachricht
            
        Returns:
            Dictionary mit den geparsten Nachrichtenteilen, strukturiert nach Befehlstyp
        """
        # Prüfe auf leere Nachricht
        if not raw_message:
            return {"command": "ERROR", "error": "Leere Nachricht", "raw": raw_message}
        
        try:
            # Entferne Leerzeichen am Anfang und Ende und das Newline-Zeichen
            clean_message = raw_message.strip()
            
            # Bestimme den Befehl (erstes Wort)
            parts = clean_message.split(" ", 1)
            command = parts[0].upper()  # Konvertiere zu Großbuchstaben für case-insensitive Vergleiche
            
            # Verarbeite jeden Befehlstyp separat
            if command == "JOIN":
                # Format: JOIN handle port
                parts = clean_message.split(" ")
                if len(parts) != 3:
                    return {"command": "ERROR", "error": "Ungültiges JOIN-Format", "raw": raw_message}
                try:
                    # Konvertiere Port zu Integer
                    port = int(parts[2])
                except ValueError:
                    return {"command": "ERROR", "error": "Ungültiger Port", "raw": raw_message}
                return {"command": "JOIN", "handle": parts[1], "port": port}
                
            elif command == "LEAVE":
                # Format: LEAVE handle
                parts = clean_message.split(" ")
                if len(parts) != 2:
                    return {"command": "ERROR", "error": "Ungültiges LEAVE-Format", "raw": raw_message}
                return {"command": "LEAVE", "handle": parts[1]}
                
            elif command == "MSG":
                # Format: MSG handle "message"
                # Verwende Regex, um mit Anführungszeichen umzugehen
                # Diese Regex sucht nach: MSG, gefolgt von Leerzeichen, einem Wort (handle), Leerzeichen
                # und dann einem Text in Anführungszeichen, wobei escaped Anführungszeichen berücksichtigt werden
                match = re.match(r'MSG\s+(\S+)\s+"((?:\\.|[^"\\])*)"', clean_message)
                if not match:
                    return {"command": "ERROR", "error": "Ungültiges MSG-Format", "raw": raw_message}
                    
                handle = match.group(1)  # Erstes Capture-Group ist der Handle

                # Ersetze escaped quotes zurück zu normalen Anführungszeichen
                message = match.group(2).replace('\\"', '"')  # Zweite Capture-Group ist die Nachricht
                return {"command": "MSG", "handle": handle, "text": message}
                
            elif command == "IMG":
                # Format: IMG handle size
                parts = clean_message.split(" ")
                if len(parts) != 3:
                    return {"command": "ERROR", "error": "Ungültiges IMG-Format", "raw": raw_message}
                try:
                    # Konvertiere Größe zu Integer
                    size = int(parts[2])
                except ValueError:
                    return {"command": "ERROR", "error": "Ungültige Größe", "raw": raw_message}
                return {"command": "IMG", "handle": parts[1], "size": size}
                
            elif command == "WHOIS":
                # Format: WHOIS handle
                parts = clean_message.split(" ")
                if len(parts) != 2:
                    return {"command": "ERROR", "error": "Ungültiges WHOIS-Format", "raw": raw_message}
                return {"command": "WHOIS", "handle": parts[1]}
                
            elif command == "IAM":
                # Format: IAM handle ip port
                parts = clean_message.split(" ")
                if len(parts) != 4:
                    return {"command": "ERROR", "error": "Ungültiges IAM-Format", "raw": raw_message}
                # Validiere IP-Adresse
                if not self._is_valid_ip(parts[2]):
                    return {"command": "ERROR", "error": "Ungültige IP-Adresse", "raw": raw_message}
                try:
                    # Konvertiere Port zu Integer
                    port = int(parts[3])
                except ValueError:
                    return {"command": "ERROR", "error": "Ungültiger Port", "raw": raw_message}
                return {"command": "IAM", "handle": parts[1], "ip": parts[2], "port": port}
                
            else:
                # Unbekannter Befehl wird als UNKNOWN zurückgegeben
                return {"command": "UNKNOWN", "raw": raw_message}
                
        except Exception as e:
            # Fange alle anderen Ausnahmen ab und gib sie als Fehler zurück
            return {"command": "ERROR", "error": str(e), "raw": raw_message}
        

        

    def _reconstruct_message(self, parts: List[str]) -> str:
        """
        Hilfsfunktion zur Zusammenführung maskierter Nachrichten.
        Verbindet die Teile der Nachricht wieder zu einem String und entfernt Anführungszeichen.
        
        Args:
            parts: Liste von Teilen der Nachricht
            
        Returns:
            Die rekonstruierte Nachricht
        """
        return " ".join(parts).strip('"')
        
    def _is_valid_ip(self, ip: str) -> bool:
        """
        Überprüft, ob eine IP-Adresse gültig ist.
        
        Args:
            ip: Die zu prüfende IP-Adresse
            
        Returns:
            True, wenn die IP-Adresse gültig ist, sonst False
        """
        # Einfache IPv4-Validierung mit Regex
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip)
        if not match:
            return False
            
        # Überprüfe, ob jeder Teil zwischen 0 und 255 liegt
        for part in match.groups():
            if int(part) < 0 or int(part) > 255:
                return False
                
        return True