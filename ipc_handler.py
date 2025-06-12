# ipc_handler.py – Verbindet CLI mit Netzwerkfunktionen über ChatClient
import socket
import json
from client import ChatClient

class IPCHandler:
    def __init__(self):
        self.client = ChatClient()
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
                    self.client.send_msg(cmd["target"], cmd["message"])
                elif action == "send_image":
                    self.client.send_img(cmd["target"], cmd["path"])
                elif action == "join_network":
                    self.client.send_join()
                elif action == "leave_network":
                    self.client.send_leave()
                elif action == "send_who":
                    self.client.send_who()
                conn.send(b"OK")
            except Exception as e:
                print(f"[IPC ERROR] {e}")
                conn.send(b"ERROR")
            finally:
                conn.close()

if __name__ == "__main__":
    ipc = IPCHandler()
    ipc.listen_for_ui_commands()