# Importiert das sys-Modul für Systemfunktionen wie Programmabbruch
import sys
# Importiert die Queue-Klasse für Interprozesskommunikation
from multiprocessing import Queue

class CLIInterface:
    """
    Implementiert die Kommandozeilen-Schnittstelle (CLI) für den Chat-Client.
    Verantwortlich für:
    - Entgegennahme von Benutzereingaben
    - Darstellung von Nachrichten
    - Kommunikation mit dem Netzwerkprozess über eine Queue
    """

    def __init__(self, config: dict, message_queue: Queue):
        """
        Initialisiert die CLI-Komponente.
        
        Args:
            config: Dictionary mit Konfiguration aus der TOML-Datei
            message_queue: Kommunikationskanal zum Netzwerkprozess
        """
        self.config = config  # Speichert Konfiguration (Benutzername, Ports etc.)
        self.message_queue = message_queue  # IPC-Warteschlange für Nachrichten

    def start(self):
        """Startet die CLI und Haupt-Eingabeschleife."""
        # Begrüßungsnachricht mit konfiguriertem Benutzernamen
        print(f"Willkommen, {self.config['handle']}! Tippe '/help' für Befehle.")
        
        # Startet Hintergrund-Thread für Nachrichtenempfang
        self._start_receiver_thread()
        
        # Haupt-Eingabeschleife (läuft bis zum Programmende)
        while True:
            try:
                # Liest Benutzereingabe von der Kommandozeile
                user_input = input("> ")
                # Verarbeitet die Eingabe
                self._process_input(user_input)
            except KeyboardInterrupt:
                # Fängt Strg+C ab und beendet das Programm sauber
                print("\n[⚠] Programm wird beendet...")
                sys.exit(0)

    def process_input(self, input_str: str):
        """
        Zentrale Steuerung für Benutzereingaben.
        Entscheidet, welcher Befehl ausgeführt wird.
        
        Args:
            input_str: Roheingabe des Benutzers (z.B. "/msg Bob Hallo")
        """
        # Extrahiert den Basisbefehl (erstes Wort der Eingabe)
        command = input_str.split()[0].lower() if input_str else ""
        
        # Verteilt die Verarbeitung an spezialisierte Methoden
        if command == "/msg":
            self._handle_msg(input_str)
        elif command == "/img":
            self._handle_img(input_str)
        elif command == "/who":
            self._handle_who()
        elif command == "/leave":
            self._handle_leave()
        elif command == "/help":
            self._show_help()
        else:
            print("Unbekannter Befehl. Tippe '/help' für Hilfe.")

    def _handle_msg(self, input_str: str):
        """Verarbeitet Textnachrichten-Befehle im Format '/msg <Handle> <Text>'"""
        try:
            # Zerlegt die Eingabe in Bestandteile
            # _ ignoriert das erste Element ("/msg")
            # handle: Empfänger-Name
            # *text: Rest der Nachricht (kann Leerzeichen enthalten)
            _, handle, *text = input_str.split(" ", 2)
            
            # Erstellt SLCP-konforme Nachricht
            msg = f"MSG {handle} {' '.join(text)}"
            
            # Sendet Nachricht an Netzwerkprozess über die Queue
            self.message_queue.put(msg)
            print(f"[✔] Nachricht an {handle} gesendet.")
            
        except ValueError:
            # Fehlerbehandlung bei falscher Parameteranzahl
            print("[✘] Format: /msg <Handle> <Text>")

    def _handle_img(self, input_str: str):
        """Platzhalter für Bildversand (aktuell nicht implementiert)"""
        try:
            # Extrahiert Parameter (Implementierung folgt später)
            _, handle, img_path = input_str.split(" ", 2)
            print(f"[✘] Bildversand noch nicht implementiert. (Pfad: {img_path})")
            
        except ValueError:
            print("[✘] Format: /img <Handle> <Bildpfad>")

    def handle_who(self):
        """Fordert die aktuelle Teilnehmerliste an"""
        # Sendet WHO-Befehl an Netzwerkprozess
        self.message_queue.put("WHO")
        print("[⌛] WHO-Anfrage gesendet.")

    def handle_leave(self):
        """Beendet das Programm und sendet Leave-Benachrichtigung"""
        # Informiert Netzwerkprozess über das Verlassen
        self.message_queue.put("LEAVE")
        # Beendet das Programm mit Exit-Code 0 (erfolgreich)
        print("[⚠] Verlasse den Chat...")
        sys.exit(0)

    def _show_help(self):
        """Zeigt alle verfügbaren Befehle an"""
        help_text = """
Befehle:
  /msg <Handle> <Text>   – Textnachricht senden
  /img <Handle> <Pfad>   – Bild senden (.png/.jpg)
  /who                   – Aktive Teilnehmer anzeigen
  /leave                 – Chat verlassen
  /help                  – Diese Hilfe anzeigen
"""
        print(help_text)

    def start_receiver_thread(self):
        """
        Startet einen Hintergrund-Thread für den Nachrichtenempfang.
        Der Thread läuft parallel zur Eingabeschleife.
        """
        import threading
        
        def message_listener():
            """
            Kontinuierlicher Nachrichtenempfang.
            Wartet auf Nachrichten in der Queue und zeigt sie an.
            """
            while True:
                # Prüft auf neue Nachrichten
                if not self.message_queue.empty():
                    # Holt Nachricht aus der Queue
                    msg = self.message_queue.get()
                    # Formatierte Ausgabe mit Zeilenumbruch vor der Nachricht
                    print(f"\n[NEUE NACHRICHT] {msg}")
        
        # Erstellt und startet Daemon-Thread
        # daemon=True: Thread wird automatisch beendet, wenn Hauptprogramm endet
        threading.Thread(
            target=message_listener,  # Auszuführende Funktion
            daemon=True
        ).start()