# impotieret das cmd Modul für die Kommandozeilen-Interface (CLI) und andere benötigte Module
import cmd
# Importiere die benötigten Module für Netzwerkkommunikation und Threading
import threading
# Importiere die Zeit- und Queue-Module für Zeitmanagement und Thread-Synchronisation
import time
import queue
# Importiere die Client-Funktionen für Netzwerkkommunikation
from client import client_send_join, client_send_leave, client_send_who, client_send_msg, client_send_img
# 30 Sekunden Inaktivität, bevor Auto-Reply ausgelöst wird
AWAY_TIMEOUT = 30 

#Main-Klasse für die Kommandozeilen-Schnittstelle des Peer-to-Peer Chats, erbt von cmd.Cmd ab
class ChatCLI(cmd.Cmd):
#autotmatische Begrüßung und Eingabeaufforderung
    intro = "Willkommen zum Peer-to-Peer Chat. Tippe 'help', um alle Befehle zu sehen."
    prompt = "> "
# Konstruktor der ChatCLI-Klasse, initialisiert die Konfiguration und IPC-Queues
    def __init__(self, config, net_to_cli_queue, disc_to_cli_queue, cli_to_net_queue):
        super().__init__()
        self.config = config
        self.net_to_cli = net_to_cli_queue
        self.disc_to_cli = disc_to_cli_queue
        self.cli_to_net = cli_to_net_queue
        self.joined = False
        self.peers = {}

        # Zeitpunkt der letzten Nutzeraktivität (zur Auto-Reply-Erkennung)
        self.last_activity = time.time()

        # Thread, um eingehende Nachrichten und Peer-Updates abzuholen
        self._stop_event = threading.Event()
        self._poll_thread = threading.Thread(target=self._poll_queues, daemon=True)
        self._poll_thread.start()

    def _poll_queues(self): # Polling-Thread, der Nachrichten und Peer-Updates abholt
        while not self._stop_event.is_set(): # Polling-Schleife 
            now = time.time() # Aktueller Zeitpunkt

            # 1. Eingehende Chat-Nachrichten abholen
            try:
                msg = self.net_to_cli.get_nowait() # Abfrage der Nachrichten-Queue
                if msg[0] == 'MSG': # Nachricht empfangen
                    from_handle = msg[1] # Absender der Nachricht
                    text = msg[2] # Text der Nachricht

                    # Auto-Reply, falls Nutzer länger als AWAY_TIMEOUT “away” ist
                    if now - self.last_activity > AWAY_TIMEOUT and self.joined:
                        # Hole Auto-Reply-Nachricht aus der geladenen Konfiguration (siehe config.toml: autoreply = "...")
                        auto_msg = self.config.get('autoreply', None) # Auto-Reply-Nachricht aus der Konfiguration
                        if auto_msg and from_handle in self.peers: # Nur senden, wenn der Absender bekannt ist
                            thost, tport = self.peers[from_handle] # Hole Host und Port des Absenders
                            client_send_msg(thost, tport, self.config['handle'], auto_msg) # Sende Auto-Reply-Nachricht

                    # Ausgabe der eigentlichen Nachricht
                    print(f"\n[Nachricht von {from_handle}]: {text}")

                elif msg[0] == 'IMG': # Bild empfangen
                    from_handle = msg[1] # Absender des Bildes
                    filepath = msg[2] # Dateipfad, wo das Bild gespeichert wurde
                    print(f"\n[Bild empfangen von {from_handle}]: gespeichert als {filepath}") # Ausgabe des Dateipfads

                # Prompt erneut anzeigen, damit Benutzer nach eingehender Nachricht weiterschreiben kann
                print(self.prompt, end='', flush=True) 

            except queue.Empty:
                pass # Weiter mit der nächsten Iteration

            # 2. Updates der Peer-Liste abholen
            try:
                dmsg = self.disc_to_cli.get_nowait() # Abfrage der Discovery-Service-Queue
                if dmsg[0] == 'PEERS': # Peer-Update empfangen
                    self.peers = dmsg[1] # Aktualisiere die Peer-Liste
            except queue.Empty: # Keine neuen Peer-Updates
                pass # Weiter mit der nächsten Iteration

            time.sleep(0.1) # Kurze Pause, um CPU-Last zu reduzieren

    # … alle do_*-Methoden setzen self.last_activity zurück (nicht verändert) …

    def do_join(self, arg): # Befehl zum Beitreten des Netzwerks
        """join <username> <port>  –  Tritt dem Netzwerk bei.""" # Dokumentation des Befehls
        self.last_activity = time.time() # Zeitpunkt der letzten Aktivität aktualisieren
        if self.joined: # Überprüfen, ob der Nutzer bereits eingeloggt ist
            print("Du bist bereits eingeloggt. Zuerst 'leave', bevor du 'join' ausführst.") # Fehlermeldung, bei bereits bestehender Verbindung
            return # Wenn der Nutzer bereits eingeloggt ist, wird eine Fehlermeldung ausgegeben und die Methode beendet
        parts = arg.split() # Teile den Eingabe-String in Teile auf 
        if len(parts) != 2: # Überprüfen, ob genau 2 Teile vorhanden sind (Benutzername und Port)
            print("Usage: join <username> <port>")  # Fehlermeldung, wenn die Eingabe nicht korrekt ist
            return # Wenn die Eingabe nicht korrekt ist, wird eine Fehlermeldung ausgegeben und die Methode beendet
        handle, port_str = parts # Teile die Eingabe in Benutzername und Port auf
        try: # Versuche, den Port in eine Ganzzahl umzuwandeln
            port = int(port_str) # Port in Ganzzahl umwandeln
        except ValueError: # Wenn die Umwandlung fehlschlägt
            print("Port muss eine Zahl sein.") # Fehlermeldung, wenn der Port keine Zahl ist
            return # Wenn der Port keine Zahl ist, wird eine Fehlermeldung ausgegeben und die Methode beendet
        self.config['handle'] = handle # Speichert den Benutzernamen, damit er in zukünfitgen Nachrichten verwendet werden kann
        self.config['port'] = port # Setze den Port in der Konfiguration
        if self.cli_to_net: # Wenn die Queue für CLI zu Network existiert
            self.cli_to_net.put(('SET_PORT', port)) # Sende den Port an den Network-Prozess
        client_send_join(self.config) # Informiert das Netzwerk über den neuen Teilnehmer (per JOIN-Nachricht)
        self.joined = True # Setze den Beitrittsstatus auf True
        print(f"Eingetreten als {handle} auf Port {port}") # Ausgabe der Bestätigung, dass der Nutzer dem Netzwerk beigetreten ist

    def do_leave(self, arg): # Befehl zum Verlassen des Netzwerks
        """leave  –  Verlässt das Netzwerk.""" # Dokumentation des Befehls
        self.last_activity = time.time() # Zeitpunkt der letzten Aktivität aktualisieren
        if not self.joined: # Überprüfen, ob der Nutzer eingeloggt ist
            print("Du bist nicht eingeloggt.") # Fehlermeldung, wenn der Nutzer nicht eingeloggt ist
            return # Wenn der Nutzer nicht eingeloggt ist, wird eine Fehlermeldung ausgegeben und die Methode beendet
        client_send_leave(self.config) # Sende eine Abmeldung an alle Peers, damit sie diesen Benutzer aus ihrer Liste entfernen
        self.joined = False # Setze den Beitrittsstatus auf False
        print("Du hast das Netzwerk verlassen.") # Ausgabe der Bestätigung, dass der Nutzer das Netzwerk verlassen hat

    def do_who(self, arg): # Befehl zum Abfragen der Peer-Liste
        """who  –  Fragt die Peer-Liste ab und zeigt sie an.""" # Dokumentation des Befehls
        self.last_activity = time.time() # Zeitpunkt der letzten Aktivität aktualisieren
        if not self.joined: # Überprüfen, ob der Nutzer eingeloggt ist
            print("Zuerst 'join', bevor du 'who' ausführst.") # Fehlermeldung, wenn der Nutzer nicht eingeloggt ist
            return # Wenn der Nutzer nicht eingeloggt ist, wird eine Fehlermeldung ausgegeben und die Methode beendet
        client_send_who(self.config) # Fordert andere Teilnehmer im Netzwerk auf, sich vorzustellen (Antwort: 'iam')
        time.sleep(0.2) # Warten, bis Rückmeldung (iam) eingetroffen sind
        if not self.peers: # Überprüfen, ob die Peer-Liste leer ist
            print("Keine Peers gefunden.") # Fehlermeldung, wenn keine Peers gefunden wurden
            return # Wenn keine Peers gefunden wurden, wird eine Fehlermeldung ausgegeben und die Methode beendet
        print("Bekannte Nutzer:") # Ausgabe der bekannten Nutzer
        for h, (hhost, hport) in self.peers.items(): # Iteriere über die Peer-Liste
            print(f"  {h} @ {hhost}:{hport}") # Ausgabe jedes Nutzers mit Host und Port

    def do_msg(self, arg): # Befehl zum Senden einer Nachricht an einen bestimmten Nutzer
        """msg <user> <text>  –  Sendet eine Textnachricht an <user>.""" # Dokumentation des Befehls
        self.last_activity = time.time() # Verhindert Auto-Reply, wenn der Nutzer aktiv ist
        if not self.joined: # Überprüfen, ob der Nutzer bereits dem Chat beigetreten ist
            print("Zuerst 'join', bevor du 'msg' ausführst.") # Fehlermeldung, wenn der Nutzer nicht eingeloggt ist
            return # Wenn der Nutzer nicht eingeloggt ist, wird eine Fehlermeldung ausgegeben und die Methode beendet
        parts = arg.split(" ", 1) # Zerlegt die Eingabe in Zielnutzer und Nachricht
        if len(parts) != 2: # Überprüfen, ob genau zwei Teile vorhanden sind
            print("Usage: msg <user> <text>") # Fehlermeldung, wenn die Eingabe nicht korrekt ist
            return # Wenn die Eingabe nicht korrekt ist, wird eine Fehlermeldung ausgegeben und die Methode beendet
        target, text = parts # Teile die Eingabe in Zielnutzer und Text auf
        if target in self.peers: # Nachricht nur senden, wenn Zielnutzer bekannt ist
            thost, tport = self.peers[target] # Hole die Host- und Port-Informationen des Zielnutzers
            client_send_msg(thost, tport, self.config['handle'], text) # Sende die Nachricht an IP/Port des Zielnutzers
        else: # Wenn der Zielnutzer nicht in der Peer-Liste ist
            print("Unbekannter Nutzer.") # Fehlermeldung, wenn der Zielnutzer nicht bekannt ist

    # Die do_msgall-Methode sendet eine Nachricht an alle Peers im Chat
    def do_msgall(self, arg):
        # Text der gezeigt wird wenn man nur msggall eingibt -> zeigt die Syntax an
        """msgall <text>  –  Sendet eine Textnachricht an alle aktuell im Chat befindlichen Nutzer."""
        # Aktualisiert den Zeitpunkt der letzten Aktivität
        self.last_activity = time.time()
        # Überprüft, ob der Nutzer bereits dem Chat beigetreten ist
        if not self.joined:
            print("Zuerst 'join', bevor du 'msgall' ausführst.")
            return
        # Überprüft, ob der Text angegeben wurde
        text = arg.strip()
        # Wenn kein Text angegeben wurde, wird die korrekte Syntax angezeigt
        if not text:
            print("Usage: msgall <text>")
            return
        # Überprüft, ob es andere Peers im Chat gibt
        if not self.peers:
            print("Keine anderen Peers im Chat.")
            return
        
        
        for peer_handle, (phost, pport) in self.peers.items():
            try:
                client_send_msg(phost, pport, self.config['handle'], text)
            except Exception as e:
                print(f"Fehler beim Senden an {peer_handle}: {e}")
        print("Nachricht an alle gesendet.")

    # Die do_img-Methode sendet ein Bild an einen bestimmten Nutzer
    def do_img(self, arg):
        # Die Syntax für den Befehl, wenn nur "img" eingegeben wird
        """img <user> <pfad>  –  Sendet ein Bild an <user>."""
        # Aktualisiert den Zeitpunkt der letzten Aktivität
        self.last_activity = time.time()
        # Überprüft, ob der Nutzer bereits dem Chat beigetreten ist
        if not self.joined:
            print("Zuerst 'join', bevor du 'img' ausführst.")
            return
        # Überprüft, ob der Argument-String leer ist
        parts = arg.split(" ", 1)
        # Wenn nicht genau zwei Teile vorhanden sind, wird die korrekte Syntax angezeigt
        if len(parts) != 2:
            print("Usage: img <user> <pfad>")
            return
        # Extrahiert den Zielnutzer und den Pfad zur Bilddatei
        target, path = parts
        # Überprüft, ob der Zielnutzer in der Peer-Liste vorhanden ist
        if target in self.peers:
            # Holt die Host- und Port-Informationen des Zielnutzers
            thost, tport = self.peers[target]
            # Versucht, das Bild zu senden
            success = client_send_img(thost, tport, self.config['handle'], path)
            # Wenn das Senden erfolgreich war, wird eine Bestätigung ausgegeben
            # andernfalls wird eine Fehlermeldung angezeigt
            if not success:
                print("Datei nicht gefunden.")
        # Wenn der Zielnutzer nicht in der Peer-Liste ist, wird eine Fehlermeldung ausgegeben
        else:
            print("Unbekannter Nutzer.")
    # Die do_show_config-Methode zeigt die aktuelle Konfiguration an

    def do_show_config(self, arg):
        # Die Syntax für den Befehl, wenn nur "show_config" eingegeben wird
        """show_config  –  Zeigt die aktuelle Konfiguration an."""
        # Aktualisiert den Zeitpunkt der letzten Aktivität
        self.last_activity = time.time()
        # Gibt die aktuelle Konfiguration aus
        print(self.config)

    # Die do_set_config-Methode ändert einen Konfigurationsparameter
    def do_set_config(self, arg):
        # Die Syntax für den Befehl, wenn nur "set_config" eingegeben wird
        """set_config <parameter> <wert>  –  Ändert einen Konfigurationsparameter."""
        self.last_activity = time.time()
        # Überprüft, ob der Argument-String leer ist
        parts = arg.split(" ", 1)
        # Wenn nicht genau zwei Teile vorhanden sind, wird die korrekte Syntax angezeigt
        if len(parts) != 2:
            print("Usage: set_config <parameter> <wert>")
            return
        key, val = parts
        # Überprüft, ob der angegebene Konfigurationsparameter existiert
        if key not in self.config:
            print("Unbekannter Konfigurationsparameter.")
            return
        # Wenn der Konfigurationsparameter ein Integer ist, wird versucht, den Wert in eine Ganzzahl umzuwandeln
        if isinstance(self.config[key], int):
            # Wenn die Umwandlung fehlschlägt, wird eine Fehlermeldung ausgegeben
            try:
                val = int(val)
            except ValueError:
                print("Wert muss eine Zahl sein.")
                return
            # Andernfalls wird der Wert als String gespeichert
        self.config[key] = val
        print(f"Konfig {key} = {val}")
    # Die do_exit-Methode beendet die CLI und den Hintergrund-Thread
    def do_exit(self, arg):
        # Die Syntax für den Befehl, wenn nur "exit" eingegeben wird
        """exit  –  Beendet CLI und Hintergrund-Thread."""
        # Aktualisiert den Zeitpunkt der letzten Aktivität
        self.last_activity = time.time()
        print("Beende CLI…")
        # Setzt das Stop-Event, um den Hintergrund-Thread zu beenden
        self._stop_event.set()
        return True
    
    # Die default-Methode fängt unbekannte Befehle ab und zeigt die korrekte Syntax an
    def default(self, line):
        """Fängt unbekannte Befehle ab und zeigt korrekte Syntax."""
        # Aktualisiert den Zeitpunkt der letzten Aktivität
        self.last_activity = time.time()
        # Teilt die Eingabezeile in Teile auf
        parts = line.strip().split()
        if not parts:
            return
        # Wenn nur ein Teil vorhanden ist, wird die korrekte Syntax angezeigt
        cmd = parts[0].lower()
        valid_cmds = {
            'join': "Usage: join <username> <port>",
            'leave': "Usage: leave",
            'who': "Usage: who",
            'msg': "Usage: msg <user> <text>",
            'msgall': "Usage: msgall <text>",
            'img': "Usage: img <user> <pfad>",
            'show_config': "Usage: show_config",
            'set_config': "Usage: set_config <parameter> <wert>",
            'help': "Usage: help",
            'exit': "Usage: exit"
        }
        # Überprüft, ob der Befehl in der Liste der gültigen Befehle vorhanden ist
        if cmd in valid_cmds:
            # Gibt die korrekte Syntax für den unbekannten Befehl aus
            print(valid_cmds[cmd])
        # Wenn der Befehl nicht in der Liste der gültigen Befehle ist, wird eine Fehlermeldung ausgegeben
        else:
            print(f"Unbekannter Befehl: '{parts[0]}'. Tippe 'help' für gültige Befehle.")
