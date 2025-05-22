import socket
import json
from slcp_handler import SLCPHandler

class IPCHandler:
    def __init__(self, handle, port):
        self.slcp = SLCPHandler(handle, port)
        # IPC Socket für Kommunikation mit UI
        self.ipc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ipc_socket.bind(('localhost', 9999))  # IPC Port
        
    def listen_for_ui_commands(self):
        """Lauscht auf Befehle vom UI über IPC"""
        self.ipc_socket.listen(1)
        while True:
            conn, addr = self.ipc_socket.accept()
            
            # Empfange Befehl vom UI
            ui_command = conn.recv(1024).decode('utf-8')
            ui_data = json.loads(ui_command)
            
            # Verwende SLCP Handler zum Formatieren
            if ui_data['action'] == 'send_message':
                slcp_message = self.slcp.create_msg(
                    ui_data['target'], 
                    ui_data['message']
                )
                # Sende über Netzwerk...
                
            elif ui_data['action'] == 'join_network':
                slcp_message = self.slcp.create_join()
                # Sende über Netzwerk...
    
    def send_to_ui(self, parsed_message):
        """Sendet geparste Nachrichten an das UI"""
        # Formatiere für UI
        ui_message = json.dumps(parsed_message)
        # Sende über IPC an UI...