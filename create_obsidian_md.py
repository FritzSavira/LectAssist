import os
import re


# Input filename
INPUT_FILENAME = 'Schlatter_Der_Roemerbrief_WF1234_gpt-o4.txt'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/Schlatter/Der_Roemerbrief/'
FINISHED_PATH = 'C:/Users/Fried/documents/LectorAssistant/Schlatter/Der_Roemerbrief/erledigt/'
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'5.md')

with open(INPUT_FILE, 'r', encoding='utf-8') as datei:
    text = datei.read()




# Der Text, der verarbeitet werden soll
'''text =
{Vorwort}

{{Vorwort zur ersten Auflage}}

[[Den Anlass zu diesem Buch gaben mir Vorträge, die ich im Winter 1885/86 über den Römerbrief vor einer Gruppe von Männern hielt. Die Auslegung der Schrift bereitet große Freude. Wir tauchen ein in einen Reichtum an Licht und Wahrheit, der das Herz jubeln lässt. Es ist das Licht des Lebens, das sowohl erleuchtet als auch belebt. Daher möchte ich das, was ich damals einem kleinen Kreis bieten konnte, gerne auch anderen zugänglich machen.]]

[[Wie kann die Gemeinde heutzutage eine gefestigte christliche Haltung erlangen, wenn nicht durch eigene Einblicke in die Schrift? Angesichts der Vielzahl von Gedanken und Lehren, die uns umgeben, und der Gegensätze innerhalb der kirchlichen Lehrmeinungen, ist jeder, der nach Gott strebt, auf die Schrift angewiesen, um das Zeugnis der Apostel selbst zu hören und sich darauf zu gründen. Wer den Römerbrief mit dem Verlangen nach der Wahrheit und Gerechtigkeit, die vor Gott Bestand hat, liest, wird ihn im Wesentlichen auch ohne Ausleger und Hilfsmittel verstehen.]]

[[Dennoch können wir uns gegenseitig wesentliche Unterstützung und Förderung beim Verständnis der Schrift geben. Ich meine, unsere theologischen Fakultäten sind hier, um mit Paulus zu sprechen, der Kirche gegenüber verpflichtet. Neben ihrem wissenschaftlichen Auftrag haben sie auch die Aufgabe, der Gemeinde den Zugang zur Schrift zu eröffnen. Da dieses Buch allein darauf abzielt, über das Wort des Apostels nachzudenken, wünsche ich ihm ohne Furcht und Scheu viele Leser, jedoch nur solche, die nicht nur die Auslegung, sondern zuerst und zugleich den Brief des Apostels selbst lesen.]]

{{Vorwort zur zweiten Auflage}}

[[Auch wenn das erste Vorwort einen etwas jugendlichen Charakter hat, drückt es doch die Überzeugungen aus, die mich dazu bewegten, dieses Buch gerne ein zweites Mal zu überarbeiten. Es wurde überall dort verändert, wo ich befürchten musste, dass die Auslegung aufgrund ihrer nur andeutenden Kürze oder einer gewissen abstrakten Blässe dem Text wenig gedient haben könnte.]]

{Kapitel 1, 1-17 - Warum Paulus nach Rom reisen möchte}

[[{{{Röm. 1, 1-17}}}]]

[[Nachdem Paulus in Kleinasien und Griechenland einen Kreis von christlichen Gemeinden fest begründet hatte, sodass sie das Evangelium bewahren und in ihrer Umgebung verbreiten konnten, wuchs in ihm der dringende Wunsch, Rom zu besuchen. Rom war damals die Weltstadt, in der sich Menschen aus allen Völkern versammelten. Für ihn als Apostel der Heiden war es der ideale Ort.]]

[[Zudem war Rom die Kaiserstadt, die das gesamte Reich regierte. Der Erfolg des Evangeliums in Rom war für die Kirche überall von großer Bedeutung. Schließlich konnte Paulus von Rom aus auch die westlichen Völker erreichen, und es wäre ihm eine Freude gewesen, das Evangelium bis an die Grenzen der ihm bekannten Welt, bis nach Spanien, zu bringen.]]

{{ Paulus und die römischen Christen}}

[[Paulus war den Christen in Rom persönlich noch unbekannt. Deshalb nutzte er seinen letzten Aufenthalt in Korinth, um seinen bevorstehenden Besuch anzukündigen. Er wollte die römische Gemeinde darauf vorbereiten, indem er ihnen Einblick in seine Art der Verkündigung gab: die Botschaft von Christus und die Einladung zum Glauben.]]'''

def save_as_md(text, filename):
    print(f"Saving Markdown file: {filename}")
    if not filename.endswith('.md'):
        filename += '.md'

    base_filename, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(new_filename):
        new_filename = f"{base_filename}({counter}){ext}"
        counter += 1

    with open(new_filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Response saved as Markdown file under: {new_filename}")



# Reguläre Ausdrucksmuster
pattern_article = re.compile(r'[^\{]\{([^\{\}]+)\}')
pattern_p_headline = re.compile(r'[^\{]\{\{([^\{\}]+)\}\}')
pattern_p = re.compile(r'\[\[([^\[\]]+)\]\]')
pattern_bible = re.compile(r'\{\{\{([^\{\}]+)\}\}\}')

# Zeilenumbrüche vor den Artikeln einfügen und keine XML-Elemente dafür erstellen
# Füge vor jedem match von pattern_article einen Zeilenumbruch ein
text = pattern_article.sub(lambda m: '\n### ' + m.group(0)[2:-1], text)
text = pattern_p_headline.sub(lambda m: '\n#### ' + m.group(0)[3:-2], text)
text = pattern_p.sub(lambda m: '' + m.group(0)[2:-2], text)
text = pattern_bible.sub(lambda m: '[[' + m.group(0)[3:-3] + ']]', text)

print(text)

# Save response as MD-file
save_as_md(text, OUTPUT_FILE)