# Chat Client

Dieses Projekt implementiert einen einfachen Peer-to-Peer Messenger.

## Mehrere Instanzen lokal starten

Um zwei Clients gleichzeitig auf einem Rechner zu betreiben, muss jeder Client auf einem eigenen UDP-Port lauschen. Starte daher jede Instanz mit einem unterschiedlichen Port:

```bash
python3 main.py --port 5001
python3 main.py --port 5002
```

Der Discovery-Service verwendet standardmäßig den gleichen `whoisport` für alle Clients. Durch die Verwendung von `SO_REUSEPORT` können mehrere Instanzen denselben Discovery-Port teilen.
