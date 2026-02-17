# Konzept für Haruko's Langzeitgedächtnis (Phase 2 & 3)

## Ziel
Haruko soll sich an vergangene Gespräche, Vorlieben und Fakten erinnern können, ohne dass der User manuell `EXECUTE: memory` aufrufen muss. Das System muss auf dem 16GB-Server effizient laufen.

## Phase 2: Assoziatives Erinnern (RAG Light)

### Problem
Wenn das Gedächtnis wächst (z.B. 1000 Fakten), können wir nicht alle in den System-Prompt laden (zu teuer, Kontext-Limit).

### Lösung: Keyword-Based Retrieval (SQLite FTS)
Statt Vektor-Datenbanken (die viel RAM brauchen), nutzen wir **SQLite FTS5 (Full-Text Search)**.

1.  **Datenbank-Upgrade**:
    *   Tabelle `conversations` hinzufügen (speichert User-Input & Haruko-Antwort).
    *   FTS-Index auf `facts` und `conversations` erstellen.

2.  **Abruf-Logik (Retrieval)**:
    *   Bevor Haruko antwortet, extrahiert sie Keywords aus der User-Anfrage (z.B. "Was weißt du über *Jenny*?").
    *   SQL-Query: `SELECT content FROM facts WHERE content MATCH 'Jenny'`.
    *   Die Top-3 Treffer werden in den System-Prompt injiziert (`CONTEXT: ...`).

## Phase 3: Automatisches Lernen & Pflege (Auto-Memory)

### Teil A: Extraktion (Geplant)
Der User will nicht ständig sagen "Merk dir das". Haruko soll es selbst merken.
Nach jedem Turn analysiert ein LLM den Dialog auf neue Fakten (noch nicht implementiert).

### Teil B: Reflexion & Konsolidierung (Implementiert)
Da die Liste der Fakten (Facts) unbegrenzt wachsen kann, muss sie regelmäßig aufgeräumt werden.

**Lösung: Der "Reflexion"-Loop**
Alle 24 Stunden prüft der Secretary-Dienst im Hintergrund die vorhandenen Fakten.
Ein LLM (Gemini Pro) erhält die gesamte Liste und hat die Aufgabe:
1.  Ähnliche Fakten zusammenzufassen.
2.  Veraltetes oder Widersprüchliches zu entfernen.
3.  Die Liste zu komprimieren.

**Ablauf:**
1.  `secretary.py` prüft Zeitstempel (`last_reflection_date`).
2.  Wenn > 24h: Lade alle Facts aus SQLite.
3.  Sende an Gemini mit Prompt: "Fasse zusammen und bereinige".
4.  Ersetze die Facts in der DB durch die bereinigte Liste.

### Technische Umsetzung
1.  **Hintergrund-Task in `main.py`**: Integriert in `start_secretary_loop`.
2.  **Turnus**: 1x täglich (konfigurierbar).
3.  **Modell**: Gemini Pro (via `google-generativeai`).

## Vorteile
*   **Sauberkeit**: Verhindert, dass das Gedächtnis mit Duplikaten "zumüllt".
*   **Effizienz**: Spart Tokens im System-Prompt durch kompaktere Fakten.
*   **Kosten**: Läuft nur 1x am Tag, daher vernachlässigbare API-Kosten.

## Phase 4: Dynamic User Profiling (Neu in v2.10)

### Ziel
Haruko soll nicht nur Fakten wissen ("User heißt Stephan"), sondern den *Charakter* des Users verstehen, um emotional intelligenter zu reagieren.

### Umsetzung
1.  **Profiler-Modul**: `user_profiler.py` analysiert im Hintergrund die Interaktionen.
2.  **Datenstruktur**: Tabelle `user_profiles` speichert ein flexibles JSON-Objekt pro User (FaceID).
3.  **Prompt-Injection**:
    *   Beim Start eines Chats wird das Profil geladen.
    *   In den System-Prompt wird eingefügt:
        ```text
        ### USER PROFILE (Stephan):
        {
          "communication_style": "direct, technical",
          "likes": ["SciFi", "Coding"],
          "current_mood": "focused"
        }
        ```
    *   Haruko passt ihren Tonfall automatisch an diese Attribute an.

