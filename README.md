# 🗨️ Peer-to-Peer LAN Messenger

Ein einfacher Chat-Client für lokale Netzwerke (LAN), der sowohl eine **Kommandozeilen-Interface (CLI)** als auch eine **grafische Benutzeroberfläche (GUI)** unterstützt. Nachrichten und Bilder können direkt zwischen Peers ausgetauscht werden – ohne zentralen Server.

---

## 🚀 Funktionen

- Text- und Bildnachrichten im lokalen Netzwerk
- Automatische Peer-Erkennung via UDP-Broadcast
- Auto-Reply bei Inaktivität
- CLI- und GUI-Modus
- Konfigurierbar über `config.toml`

---

## 🧰 Voraussetzungen

- Python 3.8+
- Abhängigkeiten:

  ```
  pip install pyqt5 toml
  ```

---

## 🗂️ Projektstruktur

```
.
├── main.py              # Einstiegspunkt, wählt GUI oder CLI
├── cli.py               # Kommandozeilen-Oberfläche
├── gui.py               # PyQt-basierte GUI
├── client.py            # Sendet Nachrichten (JOIN, MSG, IMG, etc.)
├── server.py            # Empfängt Nachrichten, speichert Bilder
├── discovery_service.py # Peer Discovery via UDP
├── ipc_handler.py       # IPC-Integration (für UI)
├── slcp_handler.py      # SLCP-Nachrichtenformat (Parser & Builder)
├── config.toml          # Konfiguration
└── images/              # Empfangene Bilder
```

---

## ⚙️ Konfiguration (`config.toml`)

Beispiel:

```toml
handle = "user_name"
port = 5005
whoisport = 4000
broadcast = "255.255.255.255"
imagepath = "./images"
autoreply = "Ich bin gerade nicht da. Ich melde mich später bei dir."
```

---

## 🧑‍💻 Nutzung

### Starten:

```
python main.py
```

Dann wählen:
- `g` → GUI
- `c` → CLI

### CLI-Befehle:

| Befehl             | Beschreibung                          |
|--------------------|----------------------------------------|
| `join <name>`      | Netzwerk beitreten                     |
| `leave`            | Netzwerk verlassen                     |
| `who`              | Peerliste anzeigen                     |
| `msg <user> <text>`| Nachricht an Benutzer senden           |
| `msgall <text>`    | Nachricht an alle senden               |
| `img <user> <pfad>`| Bild senden                            |
| `show_config`      | Aktuelle Konfiguration anzeigen        |
| `set_config <key> <val>` | Konfigurationsparameter ändern  |
| `exit`             | Anwendung beenden                      |

---

## 💬 Textnachrichten senden

- In CLI via:

  ```
  msg Alice Hallo, wie geht’s?
  ```

- In GUI: Nachricht in das Texteingabefeld schreiben → Empfänger auswählen → **„Senden“** klicken

---

## 📸 Bilder senden

- In CLI via:

  ```
  img Alice ./pfad/zum/bild.jpg
  ```

- In GUI: Kamera-Button anklicken → Bild auswählen

---

## 🔐 Hinweise

- Dieses Tool ist **nicht für produktiven Einsatz** oder über öffentliche Netzwerke gedacht.
- Die Nachrichten werden **nicht verschlüsselt** übertragen.