import pandas as pd
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from tabulate import tabulate

INPUT_FILENAME = 'CalwerFULL_process.log'

# Dateipfade
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
# Name und Pfad der PDF-Datei
PDF_FILENAME = 'CalwerFull_LogReport.pdf'
PDF_FILEPATH = os.path.join(DIRECTORY_PATH, PDF_FILENAME)

# Liste zur Speicherung der Datensätze
daten = []

# Öffne die Logdatei und lese sie zeilenweise ein
with open(INPUT_FILE, 'r', encoding='utf-8') as datei:
    for zeile in datei:
        # Entferne führende und folgende Leerzeichen
        zeile = zeile.strip()
        # Prüfe, ob die Zeile nicht leer ist
        if zeile:
            try:
                # Teile die Zeile in Timestamp und JSON auf
                timestamp, json_text = zeile.split(' - ', 1)
                # Lade den JSON-Text in ein Dictionary
                eintrag = json.loads(json_text)
                # Füge den Timestamp zum Dictionary hinzu
                eintrag['timestamp'] = timestamp
                # Füge den Eintrag der Datenliste hinzu
                daten.append(eintrag)
            except ValueError as ve:
                print(f"Fehler beim Verarbeiten der Zeile: {zeile}\n{ve}")
            except json.JSONDecodeError as je:
                print(f"Fehler beim Parsen des JSON: {zeile}\n{je}")

# Erstelle ein Pandas DataFrame aus der Datenliste
df = pd.DataFrame(daten)

# **Neue Spalte "message_short" erstellen**
def extract_message_short(message):
    # Finde die Positionen aller Doppelpunkte
    indices = [pos for pos, char in enumerate(message) if char == ':']
    if len(indices) >= 2:
        # Gibt den String bis einschließlich des zweiten Doppelpunkts zurück
        return message[:indices[1]+1]
    else:
        # Weniger als zwei Doppelpunkte gefunden, gesamte Nachricht zurückgeben
        return message

df['message_short'] = df['message'].apply(extract_message_short)

# **Neue Spalte "id-content" erstellen**
# Die Spalte enthält den Wert aus "id" und die ersten 50 Zeichen aus "content"
df['id-content'] = df['id'] + ' ' + df['content'].str[:50]

# Anzahl der individuellen Datensätze
anzahl_individuelle_datensaetze = df['id-content'].nunique()
print(f"\nAnzahl der individuellen Datensätze (id-content): {anzahl_individuelle_datensaetze}")


# Definiere die Werte, die ausgeschlossen werden sollen
ausgeschlossene_status = ['success']  # Beispiel: Status 'success' ausschließen
ausgeschlossene_messages = [
    'Paragraph too short, skipped processing.',
]  # Beispiel: Bestimmte Messages ausschließen

# Filtere das DataFrame, um die auszuschließenden Werte zu entfernen
df_gefiltert = df[~df['status'].isin(ausgeschlossene_status)]
df_gefiltert = df_gefiltert[~df_gefiltert['message'].isin(ausgeschlossene_messages)]

# Statistische Auswertung der gefilterten Spalte "message_short"
message_short_counts = df_gefiltert['message_short'].value_counts()
print("\nAnzahl der Einträge pro Message Short (gefiltert):")
print(message_short_counts)

# Optional: Darstellung der häufigsten Message Shorts (gefiltert)
top_n = 10  # Anzahl der anzuzeigenden Message Shorts
top_messages_short = message_short_counts.head(top_n)

# Erstelle ein Balkendiagramm für die häufigsten Message Shorts (gefiltert)
plt.figure(figsize=(12, 8))
top_messages_short.plot(kind='bar', color='coral')
plt.title(f'Häufigste Message Shorts (Top {top_n}, gefiltert)')
plt.xlabel('Message Short')
plt.ylabel('Anzahl')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()


# **Statistische Auswertung der Spalte "id-content"**
# Zähle die Häufigkeit jedes "id-content"-Wertes
id_content_counts = df_gefiltert['id-content'].value_counts()

# Erstelle ein DataFrame mit den Häufigkeiten
id_content_häufigkeit = id_content_counts.reset_index()
id_content_häufigkeit.columns = ['id-content', 'Häufigkeit']

# Filtere Datensätze mit Häufigkeit > 1
id_content_häufigkeit_gefiltert = id_content_häufigkeit[id_content_häufigkeit['Häufigkeit'] > 1]

# Ausgabe der gefilterten Häufigkeitstabelle
print("\nHäufigkeit der 'id-content'-Werte (nur Häufigkeit > 1):")
print(id_content_häufigkeit_gefiltert.to_string(index=False))

# **Darstellung der Häufigkeitsverteilung**
# Zähle, wie viele "id-content"-Werte 1-mal, 2-mal, 3-mal etc. vorkommen
häufigkeit_verteilung = id_content_häufigkeit['Häufigkeit'].value_counts().sort_index()

# Ausgabe der Verteilung
print("\nVerteilung der Häufigkeiten von 'id-content':")
print(häufigkeit_verteilung.to_string())

# Erstelle ein Balkendiagramm der Häufigkeitsverteilung
plt.figure(figsize=(8,6))
häufigkeit_verteilung.plot(kind='bar', color='skyblue')
plt.title("Anzahl der 'id-content'-Werte nach Häufigkeit")
plt.xlabel("Anzahl der Vorkommen eines 'id-content'-Wertes")
plt.ylabel("Anzahl der verschiedenen 'id-content'-Werte")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Gesamtzahl der individuellen Datensätze
gesamt_anzahl = anzahl_individuelle_datensaetze

# Häufigkeitsverteilung mit Prozentangaben
haeufigkeit_verteilung_prozent = (häufigkeit_verteilung / gesamt_anzahl) * 100

# Erstellen einer Tabelle mit Häufigkeit und Prozentwerten
haeufigkeit_verteilung_df = häufigkeit_verteilung.reset_index()
haeufigkeit_verteilung_df.columns = ['Häufigkeit', 'Anzahl_id-content']
haeufigkeit_verteilung_df['Prozent'] = (haeufigkeit_verteilung_df['Anzahl_id-content'] / gesamt_anzahl) * 100

# Ausgabe der Tabelle
print("\nHäufigkeitsverteilung der 'id-content'-Werte (mit Prozentangaben):")
print(haeufigkeit_verteilung_df.to_string(index=False))




# Ausgabe des DataFrames
#print(df[df['status'] == 'error'][['id-content', 'message', 'message_short']].to_string())





with PdfPages(PDF_FILEPATH) as pdf:
    # Seite 1: Zusammenfassung
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.text(0.5, 0.95, 'Statistischer Report', fontsize=20, ha='center')
    fig.text(0.1, 0.85, f"Anzahl der individuellen Datensätze (id-content): {anzahl_individuelle_datensaetze}", fontsize=12)

    # Tabelle der Häufigkeitsverteilung
    fig.text(0.1, 0.8, 'Häufigkeitsverteilung der "id-content"-Werte:', fontsize=12)
    table_text = tabulate(haeufigkeit_verteilung_df, headers='keys', tablefmt='grid', showindex=False)
    fig.text(0.1, 0.3, table_text, {'family': 'monospace'}, fontsize=10)

    ax.axis('off')
    pdf.savefig(fig)
    plt.close()

    # Seite 2: Balkendiagramm der Häufigkeitsverteilung
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(haeufigkeit_verteilung_df['Häufigkeit'].astype(str), haeufigkeit_verteilung_df['Anzahl_id-content'], color='skyblue')
    ax.set_title("Anzahl der 'id-content'-Werte nach Häufigkeit")
    ax.set_xlabel("Anzahl der Vorkommen eines 'id-content'-Wertes")
    ax.set_ylabel("Anzahl der verschiedenen 'id-content'-Werte")
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    pdf.savefig(fig)
    plt.close()

    # Seite 3: Häufigste Message Shorts
    fig, ax = plt.subplots(figsize=(12, 8))
    top_messages_short.plot(kind='bar', color='coral', ax=ax)
    ax.set_title(f'Häufigste Message Shorts (Top {top_n}, gefiltert)')
    ax.set_xlabel('Message Short')
    ax.set_ylabel('Anzahl')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()



print(f"\nDer Report wurde als '{PDF_FILEPATH}' gespeichert.")


