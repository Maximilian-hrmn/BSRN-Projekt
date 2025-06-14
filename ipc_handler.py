# ipc_handler.py – Verbindet CLI mit Netzwerkfunktionen über ChatClient
import socket
import json
import toml
import client

class IPCHandler:
    def __init__(self, config):
        self.config = config
        self.ipc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ipc_socket.bind(('localhost', 9999))

    def listen_for_ui_commands(self):
        self.ipc_socket.listen(1)
        print("[IPC] Lauscht auf CLI-Befehle")
        while True:
            conn, addr = self.ipc_socket.accept()
            data = conn.recv(2048).decode("utf-8")
            try:
                cmd = json.loads(data)
                action = cmd.get("action")
                if action == "send_message":
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

if __name__ == "__main__":
    config = toml.load("config.toml")
    ipc = IPCHandler(config)
    ipc.listen_for_ui_commands()