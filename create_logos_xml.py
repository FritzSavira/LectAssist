import os
from lxml import etree
import re


# Input filename
INPUT_FILENAME = 'Schlatter_Der_Roemerbrief_WF1234_gpt-o4.md'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/Schlatter/Der_Roemerbrief/'
FINISHED_PATH = 'C:/Users/Fried/documents/LectorAssistant/Schlatter/Der_Roemerbrief/erledigt/'
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'5.xml')

with open(INPUT_FILE, 'r', encoding='utf-8') as datei:
    text = datei.read()



# The text variable containing your content
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

# The XML header
xml_header = '''<logos-resource-content xmlns:xsi=
        "http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="X:\\Schema\\content.xsd">
        </logos-resource-content>'''

# Create the root element
# Parse the XML header and get the root element
root = etree.fromstring(xml_header)

# Create the 'articles' element
articles_element = etree.SubElement(root, 'articles')

# Regular expression patterns
pattern_article = re.compile(r'[^\{]\{([^\{\}]+)\}')
pattern_p_headline = re.compile(r'[^\{]\{\{([^\{\}]+)\}\}')
pattern_p = re.compile(r'\[\[([^\[\]]+)\]\]')
pattern_bible = re.compile(r'\{\{\{([^\{\}]+)\}\}\}')

# Find articles
matches = list(pattern_article.finditer(text))

# Initialize the article counter
article_count = 1

for i in range(len(matches)):
    article_title = matches[i].group(1).strip()

    # Set the article_id to 'A.' followed by the counter
    article_id = 'A.' + str(article_count)

    # Create an 'article' element with the 'id' attribute
    article_element = etree.SubElement(articles_element, 'article', id=article_id)

    # Create the 'toc-entry' element as a child of 'article_element'
    toc_entry = etree.SubElement(article_element, 'toc-entry', level='2')
    toc_entry.text = article_title

    # Get the content between the current and next article
    start_pos = matches[i].end()
    if i + 1 < len(matches):
        end_pos = matches[i + 1].start()
    else:
        end_pos = len(text)
    article_content = text[start_pos:end_pos]

    # Find paragraph headlines and paragraphs within the article_content
    paragraph_matches = []
    for match in pattern_p_headline.finditer(article_content):
        paragraph_matches.append(('headline', match))
    for match in pattern_p.finditer(article_content):
        paragraph_matches.append(('paragraph', match))
    # Sort matches in order of their occurrence
    paragraph_matches.sort(key=lambda x: x[1].start())

    # Define the function to process paragraph text
    def process_para_text(para_text, parent_element):
        # Process para_text, adding content to parent_element
        pos = 0
        # Find all matches
        matches = list(pattern_bible.finditer(para_text))
        # If no matches
        if not matches:
            parent_element.text = para_text
            return
        # Else, we have matches
        last_node = None
        for m in matches:
            # Text before the match
            pre_text = para_text[pos:m.start()]
            if last_node is None:
                # First segment
                parent_element.text = pre_text
            else:
                last_node.tail = pre_text
            # Create the 'data' element
            data_element = etree.SubElement(parent_element, 'data', ref=m.group(1).strip())
            data_element.text = m.group(1).strip()
            # Update pos
            pos = m.end()
            # Keep track of last node
            last_node = data_element
        # Add the remaining text after the last match
        remaining_text = para_text[pos:]
        if last_node is not None:
            last_node.tail = remaining_text

    # For each paragraph match, create an element
    for match_type, para_match in paragraph_matches:
        para_text = para_match.group(1).strip()
        if match_type == 'headline':
            # Create a 'headline' element under 'article'
            headline_element = etree.SubElement(article_element, 'p', field='heading', class_='head3')
            # Process para_text for pattern_bible matches
            process_para_text(para_text, headline_element)
        elif match_type == 'paragraph':
            # Create a 'p' element under 'article'
            p_element = etree.SubElement(article_element, 'p')
            # Process para_text for pattern_bible matches
            process_para_text(para_text, p_element)

        elif match_type == 'paragraph':
            # Create a 'p' element under 'article' with style attribute
            style_string = create_style_string()
            p_element = etree.SubElement(article_element, 'p', style=style_string)
            # Process para_text for pattern_bible matches
            process_para_text(para_text, p_element)


    # Increment the article counter
    article_count += 1

# Print the resulting XML structure
print(etree.tostring(root, pretty_print=True, encoding='unicode'))

# Aktualisierte XML-Struktur in einer neuen Datei speichern
tree = etree.ElementTree(root)
tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)

print(f"XML file has been processed successfully: {OUTPUT_FILE}")