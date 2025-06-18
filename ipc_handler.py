# ipc_handler.py – Verbindet CLI mit Netzwerkfunktionen über ChatClient
import socket   # Modul für die Netzwerkkommunikation
import json     # Modul für die JSON-Datenverarbeitung
import toml     # Modul zum Einlesen von Konfigurationsdateien im TOML-Format
import client   #Importiert die client-Funktionen, die Netzwerkoperationen durchführen


class IPCHandler:
    # Konstruktor, der die Konfiguration und den IPC-Socket initialisiert.
    def __init__(self, config):
        self.config = config # Speichert die Konfiguration aus der TOML Datei
        self.ipc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Initialisiert einen IPC-Socket für die Kommunikation
        self.ipc_socket.bind(('localhost', 9999)) # Hier wird der socket an den lokalen Host und Port 9999 gebunden, um auf eingehende Verbindungen zu warten.

    def listen_for_ui_commands(self): 
        self.ipc_socket.listen(1) #Lauscht auf genau eine eingehende Verbindung
        print("[IPC] Lauscht auf CLI-Befehle") 
        while True:
            conn, addr = self.ipc_socket.accept() #Hier wird die eingehende Verbidung akzeptiert und eine Verbindung (conn) sowie die Adresse (addr) des Clients erhalten.
            data = conn.recv(2048).decode("utf-8") # Es können bis zu 2048 bytes aus der CLI empfangen werden, die dann in einen lesbaren String umgewandelt werden. 
            try:
                cmd = json.loads(data) # Der command wird als JSON empfangen 
                action = cmd.get("action") # Hier wird der action key aus dem JSON command extrahiert, um zu bestimmen, welche Aktion ausgeführt werden soll.
                if action == "send_message": # Ab hier wird lediglich geprüft welcher command empfangen wurde und die entsprechende Funktion des client Moduls aufgerufen.
                    client.client_send_msg(
                        cmd["host"],
                        cmd["port"],
                        self.config["handle"],
                        cmd["message"],
                    )
                elif action == "send_image":
                    client.client_send_img(
                        cmd["host"],
                        cmd["port"],
                        self.config["handle"],
                        cmd["path"],
                    )
                elif action == "join_network":
                    client.client_send_join(self.config)
                elif action == "leave_network":
                    client.client_send_leave(self.config)
                elif action == "send_who":
                    client.client_send_who(self.config)
                conn.send(b"OK")
            except Exception as e:
                print(f"[IPC ERROR] {e}")
                conn.send(b"ERROR")
            finally:
                conn.close()

# Sollte das Skript direkt gestartet werden, wird der unterstehende Block ausgeführt.
# Dadurch wird die Konfiguration geladen und der IPCHandler gestartet.
if __name__ == "__main__":
    config = toml.load("config.toml")
    ipc = IPCHandler(config)
    ipc.listen_for_ui_commands()