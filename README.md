# Chat Client

Dieses Projekt implementiert einen einfachen Peer-to-Peer Messenger.

## Mehrere Instanzen lokal starten

Um zwei Clients gleichzeitig auf einem Rechner zu betreiben, muss jeder Client auf einem eigenen UDP-Port lauschen. Setze außerdem die Broadcast-Adresse in `config.toml` auf `127.255.255.255`, damit Discovery lokal funktioniert. Starte jede Instanz mit einem unterschiedlichen Port:

```bash
python3 main.py --port 5001
python3 main.py --port 5002
```

Der Discovery-Service verwendet standardmäßig den gleichen `whoisport` für alle Clients. Durch die Verwendung von `SO_REUSEPORT` können mehrere Instanzen denselben Discovery-Port teilen.

## Peer-to-Peer im Netzwerk

Sollen sich Clients auf unterschiedlichen Rechnern finden, muss die Broadcast-Adresse auf das LAN angepasst werden. Gib sie entweder in der Konfiguration an oder direkt beim Starten:

```bash
python3 main.py --port 5001 --broadcast 192.168.1.255
```

Alle Clients müssen denselben `whoisport` und dieselbe Broadcast-Adresse verwenden, damit sie sich entdecken können.

## Abhängigkeiten installieren

Die Anwendung benötigt lediglich das `toml`-Paket. Installiere es mit:

```bash
pip install toml
```
