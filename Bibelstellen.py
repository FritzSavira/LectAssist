import json
import re

# Pfad zur JSON-Datei
datei_pfad = 'C:/Users/Fried/Documents/LectorAssistant/Bibelbücher.json'

# JSON-Datei laden
with open(datei_pfad, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Funktion zum Ersetzen von Ziffern durch 'X'
def replace_digits(text):
    return re.sub(r'\d+', 'X', text)

# Verarbeitung des Dictionaries
processed_data = {}
for key, value in data.items():
    new_key = replace_digits(key)
    new_value = replace_digits(value)

    # Überprüfen auf Doubletten
    if new_key not in processed_data:
        processed_data[new_key] = new_value

# Verarbeitetes Dictionary als JSON-Datei speichern
with open(datei_pfad, 'w', encoding='utf-8') as file:
    json.dump(processed_data, file, indent=4, ensure_ascii=False)

print("Verarbeitung abgeschlossen. Ergebnis in der Originaldatei gespeichert.")
