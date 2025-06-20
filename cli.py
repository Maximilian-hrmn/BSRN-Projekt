import cmd
import threading
import queue
import socket
import time
from client import client_send_join, client_send_leave, client_send_who, client_send_msg, client_send_img

# Timeout für Auto-Reply (in Sekunden)
# 30 Sekunden Inaktivität, bevor Auto-Reply ausgelöst wird
AWAY_TIMEOUT = 30  

"""
    Hauptklasse für das Kommandozeilen-Interface des Peer-to-Peer-Chats.

    Verwaltet Benutzereingaben, Nachrichtenversand und -empfang sowie Auto-Reply-Logik.
 """

"""ChatCLI-Klasse, die das cmd-Modul erweitert, um eine Kommandozeilen-Schnittstelle für den Chat zu implementieren."""
class ChatCLI(cmd.Cmd):
    # Text der aufgrund des cmd Moduls automatisch angezeigt wird wenn man die CLI startet
    intro = "Willkommen zum Peer-to-Peer Chat. Tippe 'help', um alle Befehle zu sehen."
    # Prompt, der vor jeder Eingabe angezeigt wird (auch automatisch durch cmd gesetzt)
    prompt = "> "

    """Konstruktor der ChatCLI-Klasse"""
    def __init__(self, config, net_to_cli_queue, disc_to_cli_queue, cli_to_net_queue):
        # Ruft den Konstruktor der Basisklasse cmd.Cmd auf 
        super().__init__()
        # Enthält alle Einstellungen aus der config.toml Datei
        self.config = config
        # Thread sicheres Queue-Objekt für eingehende Nachrichten vom Netzwerk, Discovery und ausgehende Nachrichten an das Netzwerk
        self.net_to_cli = net_to_cli_queue
        self.disc_to_cli = disc_to_cli_queue
        self.cli_to_net = cli_to_net_queue
        # Flag, ob der Nutzer im Netzwerk eingeloggt ist
        # Wird auf True gesetzt, wenn der Nutzer dem Netzwerk beitritt
        self.joined = False
        # Dictionary, das die Peers (Nutzer) im Netzwerk speichert, dadruch können Funktionen wie who und msgall implementiert werden
        self.peers = {}

        # Zeitpunkt der letzten Nutzeraktivität (zur Auto-Reply-Erkennung)
        self.last_activity = time.time()

        # Event-Objekt zum Stoppen des Polling-Threads (wird gesetzt, wenn die CLI beendet wird und beendet die Loop)
        self._stop_event = threading.Event()
        # Erstellt einen Daemon-Thread, der in _poll_queues() laufend (≈ alle 100 ms) die beiden
        # Queues net_to_cli und disc_to_cli „pollt“, also wiederholt.  So erscheinen eingehende Chat-Nachrichten
        # und Peer-Events sofort im Terminal, während der Haupt-Thread weiter Benutzereingaben
        # verarbeiten kann.  daemon=True sorgt dafür, dass der Thread automatisch beendet wird,
        # sobald der Haupt-Thread (cmdloop) endet – ohne explizites join().
        self._poll_thread = threading.Thread(target=self._poll_queues, daemon=True)
        # Startet den Polling-Thread self._poll_thread
        self._poll_thread.start()

    """Diese Methode wird im Hintergrund-Thread ausgeführt und pollt die Queues"""
    def _poll_queues(self): 
        #läuft bis das _stop_event gesetzt wird
        while not self._stop_event.is_set():
            # Aktualisiert den Zeitpunkt der letzten Aktivität, um Auto-Reply zu steuern
            now = time.time()

            # 1. Eingehende Chat-Nachrichten abholen
            try:
                # get nowait() holt eine Nachricht aus der Queue, ohne zu blockieren
                msg = self.net_to_cli.get_nowait()
                # --- Fall A: Textnachricht ---
                if msg[0] == 'MSG':
                    from_handle = msg[1] # Absender der Nachricht
                    text = msg[2] # Inhalt der Nachricht

                    # Auto-Reply, falls Nutzer länger als AWAY_TIMEOUT “away” ist
                    if now - self.last_activity > AWAY_TIMEOUT and self.joined:
                        # Die Auto-Reply-Nachricht aus der Konfigurationsdatei auslesen
                        auto_msg = self.config.get('autoreply', None)
                        # Wenn eine Auto-Reply-Nachricht definiert ist, wird sie an den Absender gesendet
                        if auto_msg and from_handle in self.peers:
                            # Sende die Auto-Reply-Nachricht an den Absender falls einer vorhanden ist
                            thost, tport = self.peers[from_handle]
                            client_send_msg(thost, tport, self.config['handle'], auto_msg)

                    # Ausgabe der eigentlichen Nachricht
                    print(f"\n[Nachricht von {from_handle}]: {text}")

                # --- Fall B: Bildnachricht ---
                elif msg[0] == 'IMG':
                    from_handle = msg[1]
                    filepath = msg[2]
                    print(f"\n[Bild empfangen von {from_handle}]: gespeichert als {filepath}")

                # Prompt wieder anzeigen nach der Verarbeitung der Nachricht
                print(self.prompt, end='', flush=True)

            except queue.Empty:
                pass

            # 2. Updates der Peer-Liste abholen
            try:
                dmsg = self.disc_to_cli.get_nowait()
                # Der Discovery-Service sendet Updates über die Peer-Liste
                # ('PEERS', <dict>) – wir übernehmen das Dict.
                if dmsg[0] == 'PEERS':
                    self.peers = dmsg[1]
            except queue.Empty:
                pass
        
            # Pause damit die CPU nicht überlastet wird
            time.sleep(0.1)

    # Die folgenden Methoden sind die Befehle, die der Nutzer in der CLI eingeben kann.

    """Implementierung des join-Befehls"""
    def do_join(self, arg):
        #Docstring für den join-Befehl: nutzt man durch Eingabe von 'help join'
        """join <username>  –  So trittst du dem Netzwerk bei. Dein Port wird automatisch vergeben."""
        self.last_activity = time.time()
        # Überprüfen, ob der Nutzer bereits eingeloggt ist
        if self.joined:
            print("Du bist bereits eingeloggt. Zuerst 'leave', bevor du 'join' ausführst.")
            return
        # Überprüfen, ob ein Username angegeben wurde
        parts = arg.split()
        # len(parts) prüft, ob genau ein Argument (der Username) angegeben wurde
        if len(parts) != 1:
            print("Usage: join <username>")
            return
        # Der Username wird aus dem Argument extrahiert
        handle = parts[0]

        # 1: freien TCP-Port wählen
        # Erstellen eines temporären Sockets, um einen freien Port zu finden
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # binden an Port 0, um einen freien Port zu erhalten
        tmp_sock.bind(("", 0))
        # Abrufen des zugewiesenen Ports
        port = tmp_sock.getsockname()[1]
        # Schließen des temporären Sockets
        tmp_sock.close()

        # 2: Konfiguration aktualisieren
        self.config['handle'] = handle
        self.config['port'] = port
        # Falls eine CLI-zu-Netzwerk-Queue existiert, wird der Port gesetzt
        if self.cli_to_net:
            self.cli_to_net.put(('SET_PORT', port))
        # 3: Beitrittsnachricht an das Netzwerk senden
        client_send_join(self.config)
        self.joined = True
        print(f"Eingetreten als {handle} auf Port {port}")

    """Implementierung des leave-Befehls"""
    def do_leave(self, arg):
        """leave  –  Verlässt das Netzwerk."""
        self.last_activity = time.time()
        # Überprüfen, ob der Nutzer eingeloggt ist
        # Wenn der Nutzer nicht eingeloggt ist, wird eine Fehlermeldung ausgegeben
        if not self.joined:
            print("Du bist nicht eingeloggt.")
            return
        # Senden der Verlassen-Nachricht an das Netzwerk
        # Dadurch wird der Nutzer aus dem Netzwerk entfernt
        client_send_leave(self.config)
        self.joined = False
        print("Du hast das Netzwerk verlassen.")

    """Implementierung des who-Befehls"""
    def do_who(self, arg):
        """who  –  Fragt die Peer-Liste ab und zeigt sie an."""
        self.last_activity = time.time()
        # Überprüfen, ob der Nutzer eingeloggt ist
        if not self.joined:
            print("Zuerst 'join', bevor du 'who' ausführst.")
            return
        client_send_who(self.config)
        # Kurze Pause, um sicherzustellen, dass die Peer-Liste aktualisiert wurde
        time.sleep(0.2)
        # Falls keine Peers gefunden wurden, wird eine entsprechende Nachricht ausgegeben
        if not self.peers:
            print("Keine Peers gefunden.")
            return
        # Ausgabe der bekannten Nutzer
        print("Bekannte Nutzer:")
        # Iteration über die Peers und Ausgabe ihres Handles und Ports
        for h, (hhost, hport) in self.peers.items():
            print(f"  {h} @ {hhost}:{hport}")

    """Implementierung des msg-Befehls"""
    def do_msg(self, arg):
        """msg <user> <text>  –  Sendet eine Textnachricht an <user>."""
        self.last_activity = time.time()
        # Überprüfen, ob der Nutzer eingeloggt ist
        if not self.joined:
            print("Zuerst 'join', bevor du 'msg' ausführst.")
            return
        # Überprüfen, ob ein Nutzername und Text angegeben wurden
        parts = arg.split(" ", 1)
        # len(parts) prüft, ob genau zwei Argumente (Nutzername und Text) angegeben wurden
        if len(parts) != 2:
            print("Usage: msg <user> <text>")
            return
        target, text = parts
        # Überprüfen, ob der Zielnutzer in der Peer-Liste vorhanden ist
        # Wenn der Nutzer in der Peer-Liste ist, wird die Nachricht gesendet
        # Ansonsten wird eine Fehlermeldung ausgegeben
        if target in self.peers:
            thost, tport = self.peers[target]
            client_send_msg(thost, tport, self.config['handle'], text)
        else:
            print("Unbekannter Nutzer.")
    
    """Implementierung des msgall-Befehls"""
    def do_msgall(self, arg):
        """msgall <text>  –  Sendet eine Textnachricht an alle aktuell im Chat befindlichen Nutzer."""
        self.last_activity = time.time()
        if not self.joined:
            print("Zuerst 'join', bevor du 'msgall' ausführst.")
            return
        # Überprüfen, ob ein Text angegeben wurde
        text = arg.strip()
        if not text:
            print("Usage: msgall <text>")
            return
        # Überprüfen, ob es andere Peers im Chat gibt
        # Wenn keine Peers vorhanden sind, wird eine entsprechende Nachricht ausgegeben
        # Ansonsten wird die Nachricht an alle Peers gesendet
        if not self.peers:
            print("Keine anderen Peers im Chat.")
            return
        # Iteration über die Peers und Senden der Nachricht an jeden Peer
        for peer_handle, (phost, pport) in self.peers.items():
            try:
                client_send_msg(phost, pport, self.config['handle'], text)
            except Exception as e:
                print(f"Fehler beim Senden an {peer_handle}: {e}")
        print("Nachricht an alle gesendet.")

    """Implementierung des img-Befehls"""
    def do_img(self, arg):
        """img <user> <pfad>  –  Sendet ein Bild an <user>."""
        self.last_activity = time.time()
        if not self.joined:
            print("Zuerst 'join', bevor du 'img' ausführst.")
            return
        # Überprüfen, ob ein Nutzername und ein Pfad angegeben wurden
        parts = arg.split(" ", 1)
        if len(parts) != 2:
            print("Usage: img <user> <pfad>")
            return
        # Extrahieren des Zielnutzers und des Pfads
        target, path = parts
        if target in self.peers:
            # Überprüfen, ob der Zielnutzer in der Peer-Liste vorhanden ist
            thost, tport = self.peers[target]
            # Senden des Bildes an den Zielnutzer
            success = client_send_img(thost, tport, self.config['handle'], path)
            if not success:
                print("Datei nicht gefunden.")
        else:
            print("Unbekannter Nutzer.")

    
    """Implementierung des show_config-Befehls"""
    def do_show_config(self, arg):
        """show_config  –  Zeigt die aktuelle Konfiguration an."""
        self.last_activity = time.time()
        # ausgabe der aktuellen Konfiguration
        print(self.config)

    """Implementierung des set_config-Befehls"""
    def do_set_config(self, arg):
        """set_config <parameter> <wert>  –  Ändert einen Konfigurationsparameter."""
        self.last_activity = time.time()
        parts = arg.split(" ", 1)
        if len(parts) != 2:
            print("Usage: set_config <parameter> <wert>")
            return
        # Überprüfen, ob der Parameter und der Wert angegeben wurden existieren
        key, val = parts
        if key not in self.config:
            print("Unbekannter Konfigurationsparameter.")
            return
        # Überprüfen, ob der Wert ein Integer sein soll
        if isinstance(self.config[key], int):
            # Wenn der Parameter kein Integer ist, wird versucht, den Wert in einen Integer zu konvertieren
            try:
                val = int(val)
            # Wenn die Konvertierung fehlschlägt, wird eine Fehlermeldung ausgegeben
            except ValueError:
                print("Wert muss eine Zahl sein.")
                return
        # Aktualisieren des Konfigurationsparameters
        self.config[key] = val
        print(f"Konfig {key} = {val}")

    """Implementierung des exit-Befehls"""
    def do_exit(self, arg):
        """exit  –  Beendet CLI und Hintergrund-Thread."""
        self.last_activity = time.time()
        print("Beende CLI…")
        # Setzen des Stop-Events, um den Polling-Thread zu beenden
        self._stop_event.set()
        return True

    """Standardmethode, die aufgerufen wird, wenn ein unbekannter Befehl eingegeben wird"""
    def default(self, line):
        """Fängt unbekannte Befehle ab und zeigt korrekte Syntax."""
        self.last_activity = time.time()
        # Aufteilen der Eingabezeile in Teile
        parts = line.strip().split()

        if not parts:
            return
        # Der erste Teil der Eingabe wird als Befehl interpretiert
        cmd = parts[0].lower()
        # Überprüfen, ob der Befehl in der Liste der gültigen Befehle ist
        valid_cmds = {
            'join': "Usage: join <username>",
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
        # Wenn der Befehl gültig ist, wird die entsprechende Usage-Anweisung ausgegeben
        if cmd in valid_cmds:
            print(valid_cmds[cmd])
        # Wenn der Befehl nicht gültig ist, wird eine Fehlermeldung ausgegeben
        else:
            print(f"Unbekannter Befehl: '{parts[0]}'. Tippe 'help' für gültige Befehle.")
