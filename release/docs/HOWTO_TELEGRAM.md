# Telegram Integration einrichten

Haruko kann jetzt via Telegram gesteuert werden!

## Schritte

1.  **Telegram öffnen**:
    Öffne Telegram auf deinem Handy oder PC.

2.  **BotFather suchen**:
    Suche nach dem Nutzer `@BotFather` (das ist der offizielle Bot von Telegram zum Erstellen von Bots).

3.  **Neuen Bot erstellen**:
    -   Schreibe `/newbot` an BotFather.
    -   Gib dem Bot einen Namen (z.B. "Haruko AI").
    -   Gib dem Bot einen Username (z.B. "MeinHarukoBot", muss auf "bot" enden).

4.  **Token erhalten**:
    BotFather gibt dir einen langen API Token (z.B. `123456789:ABCdefGHIjklMNOpqrstUVwxyz`).
    Kopiere diesen Token.

5.  **Token in Haruko eintragen**:
    -   Öffne die Datei `E:\moltbotback\backend\main.py` mit einem Texteditor (Rechtsklick -> Bearbeiten).
    -   Suche die Zeile `TELEGRAM_TOKEN = ...`.
    -   Ersetze den Platzhalter durch deinen Token.
    -   Beispiel: `TELEGRAM_TOKEN = "123456789:ABCdefGHIjklMNOpqrstUVwxyz"`
    -   Speichere die Datei.

6.  **Neustart**:
    Starte Haruko neu (`start_haruko_windows.bat`).

## Befehle

-   Schreibe einfach Nachrichten an den Bot, um mit Haruko zu chatten.
-   `/cam` : Macht einen Screenshot vom Server (ideal, wenn die Kamera-App offen ist).
-   `/cam webcam` : Versucht, ein Bild von der Webcam zu machen.