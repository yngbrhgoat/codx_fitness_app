# FitTrainer – Kivy Desktop Trainings-App

FitTrainer ist eine Python-Desktop-Anwendung (Kivy), mit der Benutzer geführte Trainings
durchführen können – inklusive:

- **Übungsdatenbank** mit Filtern
- **Benutzerverwaltung** und Trainingshistorie
- **Empfehlungssystem** basierend auf Ziel & Verfügbarkeit
- **Live-Modus** mit Timern, Pausen und Tempo-Anleitung

Die Anwendung ist als Python-Paket installierbar und speichert alle Daten lokal (SQLite).

---

## 🧱 Hauptfunktionen (Überblick)

Die wichtigsten Funktionsbereiche im Abgleich mit den Anforderungen:

### 1. Übungsdatenbank

- Verwaltung einer lokalen Übungsdatenbank mit:
  - Name
  - Bild/Icon/Animation (falls vorhanden)
  - Beschreibung
  - Benötigte Ausrüstung (z. B. „Hantel“, „keine“)
  - Ziel-Muskelgruppe (Brust, Rücken, Beine, Schultern, Arme, Core, Ganzkörper, …)
  - Für jedes Ziel:
    - Eignungsbewertung (0–10)
    - Empfohlene Sätze
    - Empfohlene Wiederholungen
    - Empfohlene Zeit (Sekunden)
- Übungsbrowser mit Filterung nach:
  - Ziel (Muskelaufbau, Gewichtsverlust, Kraftsteigerung, Ausdauersteigerung)
  - Muskelgruppe
  - Ausrüstung
- Detailansicht mit allen Parametern
- Formular zum Hinzufügen neuer Übungen
- Mindestens 15 vorinstallierte Übungen, die verschiedene Muskelgruppen abdecken

### 2. Benutzerverwaltung & Historie

- Anmeldung durch Eingabe eines **Benutzernamens**
- Pro Benutzer werden gespeichert:
  - Benutzername
  - Vollständige Trainingshistorie (alle Einheiten)
- Trainingshistorie-Ansicht:
  - Datum der Einheit
  - Liste der Übungen
  - Dauer der Einheit
- Filterung der Historie nach Datumsbereich
- Zusammenfassende Statistiken:
  - Gesamtanzahl der Trainingseinheiten
  - Gesamttrainingszeit
  - Am häufigsten durchgeführte Übungen

### 3. Trainings-Empfehlungssystem

- Benutzer wählt:
  - Ziel: `Muskelaufbau`, `Gewichtsverlust`, `Kraftsteigerung`, `Ausdauersteigerung`
  - Maximale verfügbare Trainingszeit (Minuten)
- Alle passenden Übungen werden bewertet anhand:
  - Eignungsbewertung (0–10)
  - Neuheit (nicht kürzlich ausgeführte Übungen werden bevorzugt)
- Kombinierter Empfehlungs-Score (siehe Abschnitt *Empfehlungsalgorithmus*)
- Ausgabe: sortierte Liste empfohlener Übungen
- Benutzer wählt Übungen für die Session aus, kann:
  - Übungen hinzufügen/entfernen
  - Reihenfolge frei ändern (Drag & Drop / Buttons)
- Berechnung der geschätzten Gesamttrainingszeit
- Sicherstellung, dass die geschätzte Zeit die Maximalzeit **nicht wesentlich** überschreitet
- Start-Schaltfläche zum Übergang in den Live-Modus

### 4. Live-Modus

- Zeigt nacheinander alle ausgewählten Übungen in der vorgegebenen Reihenfolge
- Für jede Übung werden angezeigt:
  - Name
  - Bild/Icon (falls vorhanden)
  - Anvisierte Muskelgruppe(n)
  - Benötigte Ausrüstung
  - Empfohlene Sätze und Wiederholungen
  - Timer (verstrichene Zeit je Übung)
  - Aktueller Satz
  - Aktuelle Wiederholungsanweisung
- Funktionen:
  - Automatisches Fortschreiten zum nächsten Satz (nach Ablauf Pause / Zeit)
  - Manuelles Fortschreiten zur nächsten Übung
  - Pause / Fortsetzen des Trainings
  - Aktuelle Übung überspringen
  - Training vorzeitig beenden
- Pausen-Timer zwischen Sätzen
- Akustische oder visuelle Hinweise bei:
  - Satzwechsel
  - Übungswechsel
- Anzeige des Gesamtfortschritts (z. B. „Übung 3 / 7“)
- Tempo-Anleitung:
  - Basierend auf empfohlener Zeit und Wiederholungen
  - z. B. „Du solltest jetzt bei Wiederholung 8 sein“

### 5. Trainingsabschluss & Protokollierung

- Zusammenfassung nach dem Training:
  - Gesamtdauer
  - Abgeschlossene Übungen
  - Übersprungene Übungen
  - Gesamtzahl der abgeschlossenen Sätze
- Speicherung in der Benutzerhistorie:
  - Datum/Uhrzeit
  - Ziel, das für die Empfehlung gewählt wurde
  - Alle versuchten Übungen
  - Markierung: abgeschlossen vs. übersprungen
  - Gesamtdauer der Einheit
- Option:
  - Zurück zum Hauptmenü
  - Neue Trainingseinheit starten

### 6. Benutzeroberfläche

- Hauptmenü mit Zugriff auf:
  - Übungen durchsuchen
  - Trainingsempfehlung
  - Trainingshistorie
  - Benutzerwahl/-anmeldung
- Alle Formulare mit Eingabevalidierung und verständlichen Fehlermeldungen
- Live-Modus im Vollbild/maximierten Fenster
- Konsistentes UI-Design, umgesetzt mit **Kivy-Widgets**

---

## 🧰 Technischer Überblick

- Programmiersprache: **Python 3.10+**
- GUI-Framework: **Kivy**
- Datenbank: **SQLite** (lokale Datei)
- Numerik & Statistik: **NumPy**
- Tests: **pytest** (oder `unittest`, je nach Umsetzung)
- Paketierung: **pyproject.toml** mit `setuptools` oder `hatchling` als Build-Backend

---

## 📦 Installation

> Voraussetzungen:
> - Python **3.10 oder höher**
> - `pip` installiert
> - Optional: virtuelles Environment wird empfohlen

1. Repository klonen oder Projektordner herunterladen:

   ```bash
   git clone <DEIN-REPO-URL> fittrainer
   cd fittrainer
