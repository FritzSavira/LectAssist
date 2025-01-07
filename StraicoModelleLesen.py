import json
import glob
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys

# **Konfiguration**
# Pfad zum Verzeichnis mit den JSON-Dateien (anpassen!)
JSON_DIRECTORY = r"C:\Users\Fried\OneDrive\Dokumente\PyCharmProjects_sync\Straico_Modelle"

# **Global Variable**
# Speichert den Namen des ausgewählten Modells
MODEL_NAME = None

def get_latest_json_file():
    """
    Ermittelt die neueste JSON-Datei im angegebenen Verzeichnis.

    :return: Pfad zur neuesten JSON-Datei
    :raises FileNotFoundError: Wenn keine JSON-Dateien gefunden werden
    """
    # Verwende os.path.join für plattformunabhängige Pfadkonstruktion
    search_pattern = os.path.join(JSON_DIRECTORY, 'straico_modelle_*.json')
    files = glob.glob(search_pattern)
    if not files:
        raise FileNotFoundError("No straico_response json files found")
    # Ermittle die neueste Datei basierend auf dem Dateinamen
    latest_file = max(files, key=lambda x: int(os.path.basename(x).split('_')[2].split('.')[0]))
    return latest_file

class ModelViewer:
    """
    GUI-Klasse zum Anzeigen und Auswählen von Modell-Daten.
    """

    def __init__(self, root, data):
        """
        Initialisiert die GUI-Komponenten.

        :param root: Tkinter-Root-Element
        :param data: Parsierte JSON-Daten
        """
        self.root = root
        self.data = data['data']['chat']
        self.index = 0  # Aktueller Datensatz-Index

        # Sortiere Datensätze nach Editors Choice Level (absteigend)
        self.data.sort(
            key=lambda x: int(x['metadata'].get('editors_choice_level', -1)),
            reverse=True
        )

        # Erstelle Text-Feld für die Anzeige von Modell-Daten
        self.text = tk.Text(root, wrap=tk.WORD, width=80, height=30)
        self.text.pack()

        # Zeige den ersten Datensatz an
        self.display_record()

        # Binden von Tasten-Ereignissen:
        # - Pfeil nach unten: Nächster Datensatz
        # - Pfeil nach oben: Vorheriger Datensatz
        # - Enter: Auswählen des aktuellen Modells
        root.bind('<Down>', self.next_record)
        root.bind('<Up>', self.previous_record)
        root.bind('<Return>', self.select_model)

    def select_model(self, event=None):
        """
        Speichert den Namen des aktuellen Modells und schließt die GUI.

        :param event: Tkinter-Ereignis (optional)
        """
        global MODEL_NAME
        current_model = self.data[self.index]
        MODEL_NAME = current_model['model']  # Speichere Modell-Namen
        self.root.destroy()  # Schließe GUI

    def display_record(self):
        """
        Zeigt die Daten des aktuellen Modells im Text-Feld an.
        """
        model_data = self.data[self.index]

        # Leere das Text-Feld
        self.text.delete(1.0, tk.END)

        # Erstelle eine Liste mit Modell-Informationen
        info = []
        info.append("=" * 50)
        info.append(f"Name: {model_data['name']}")
        info.append(f"Model: {model_data['model']}")
        info.append(f"Word Limit: {model_data['word_limit']}")
        pricing = model_data['pricing']
        info.append(f"Pricing: {pricing['coins']} coins per {pricing['words']} words")
        info.append(f"Max Output: {model_data['max_output']}")

        metadata = model_data['metadata']
        info.append("\nMetadata:")
        info.append(f"Editor's Choice Level: {metadata.get('editors_choice_level', 'N/A')}")

        # Füge weitere Metadaten-Informationen hinzu (sofern vorhanden)
        if metadata.get('pros'):
            info.append("\nPros:")
            for pro in metadata['pros']:
                info.append(f"- {pro}")

        if metadata.get('cons'):
            info.append("\nCons:")
            for con in metadata['cons']:
                info.append(f"- {con}")

        if metadata.get('applications'):
            info.append("\nApplications:")
            for app in metadata['applications']:
                info.append(f"- {app}")

        if metadata.get('features'):
            info.append("\nFeatures:")
            for feature in metadata['features']:
                info.append(f"- {feature}")

        if metadata.get('other'):
            info.append("\nOther:")
            for other in metadata['other']:
                info.append(f"- {other}")

        # Zeige die Modell-Informationen im Text-Feld an
        self.text.insert(tk.END, "\n".join(info))

    def next_record(self, event=None):
        """
        Zeigt den nächsten Modell-Datensatz an (sofern vorhanden).

        :param event: Tkinter-Ereignis (optional)
        """
        if self.index < len(self.data) - 1:
            self.index += 1
            self.display_record()
        else:
            messagebox.showinfo("Ende", "Dies ist der letzte Datensatz.")

    def previous_record(self, event=None):
        """
        Zeigt den vorherigen Modell-Datensatz an (sofern vorhanden).

        :param event: Tkinter-Ereignis (optional)
        """
        if self.index > 0:
            self.index -= 1
            self.display_record()
        else:
            messagebox.showinfo("Anfang", "Dies ist der erste Datensatz.")


def StraicoModelleLesen():
    """
    Haupt-Funktion:
    - Liest die neueste JSON-Datei aus dem angegebenen Verzeichnis
    - Startet die GUI für die Modell-Auswahl
    - Gibt den Namen des ausgewählten Modells zurück

    :return: Name des ausgewählten Modells (oder None bei Fehler)
    """
    try:
        # Überprüfe, ob das Verzeichnis existiert
        if not os.path.exists(JSON_DIRECTORY):
            raise FileNotFoundError(f"Das Verzeichnis {JSON_DIRECTORY} existiert nicht")

        latest_file = get_latest_json_file()
        print(f"Lade Datei: {latest_file}")

        with open(latest_file, 'r') as file:
            data = json.load(file)

        root = tk.Tk()
        root.title("Model Viewer")
        root.attributes('-topmost', True)
        root.focus_force()  # Erzwingt den Fokus auf das Fenster
        root.focus_set()  # Stellt sicher, dass das Fenster den Fokus erhält

        app = ModelViewer(root, data)
        root.mainloop()

        if MODEL_NAME:
            print(f"Selected model: {MODEL_NAME}")
        return MODEL_NAME

    except FileNotFoundError as e:
        print(f"Fehler: {str(e)}")
    except json.JSONDecodeError:
        print("Fehler: Ungültiges JSON-Format")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {str(e)}")

if __name__ == "__main__":
    StraicoModelleLesen()