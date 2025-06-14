# Chat Client

Dieses Projekt implementiert einen einfachen Peer-to-Peer Messenger.

## Mehrere Instanzen lokal starten

Mehrere Instanzen lassen sich parallel starten, ohne einen Port manuell zu vergeben. Beim Beitritt zu einem Chat wählt der Client automatisch einen freien TCP-Port und teilt ihn über den Discovery-Dienst mit. Stelle lediglich sicher, dass die Broadcast-Adresse in `config.toml` auf `127.255.255.255` gesetzt ist, wenn du Discovery lokal testen möchtest.

## Peer-to-Peer im Netzwerk

Sollen sich Clients auf unterschiedlichen Rechnern finden, muss die Broadcast-Adresse auf das LAN angepasst werden. Gib sie entweder in der Konfiguration an oder direkt beim Starten. Achte darauf, keine Loopback-Adresse (`127.x.x.x`) zu verwenden, da sonst alle Peers ihre eigene Adresse melden:

```bash
python3 main.py --broadcast 192.168.1.255
```

Alle Clients müssen denselben `whoisport` und dieselbe Broadcast-Adresse verwenden, damit sie sich entdecken können.

## Abhängigkeiten installieren

Die Anwendung benötigt lediglich das `toml`-Paket. Installiere es mit:

```bash
pip install toml
```
