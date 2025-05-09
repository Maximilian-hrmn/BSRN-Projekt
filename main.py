import toml
import socket

def main():
	
    # TOML-Datei wird geladen und eingebetet und mit try-catch abgefangen
        try:
            config = toml.load("config.toml")
            print("Konfigurationsdatei geladen...")
        
        except FileNotFoundError: 
            print("Konfigurationsdatei nicht gefunden.")
            return  
        
        except toml.TomlDecodeError:
            print("Fehler beim Dekodieren der Konfigurationsdatei.")
            return
        
        


	