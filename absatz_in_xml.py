# Import der notwendigen Bibliothek
from lxml import etree
import os

# Input filename
INPUT_FILENAME = 'CalwerFULL_241009_out_TransBiblEnDe.xml'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/'
FINISHED_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/erledigt/'
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/bearbeitet/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_AbsInXml.xml')




# XML-Datei einlesen
tree = etree.parse(INPUT_FILE)
root = tree.getroot()

def split_p_element(p_elem):
    """
    Teilt den Inhalt eines <p>-Elements an jeder Stelle von "StartAbsatz",
    erhält dabei die inneren XML-Elemente und gibt eine Liste von neuen <p>-Elementen zurück.
    """
    chunks = []
    current_chunk = []

    # Bestimme das Namespace des <p>-Elements
    nsmap = p_elem.nsmap
    p_tag = etree.QName(p_elem.tag)
    ns_uri = p_tag.namespace
    p_tag_name = p_tag.localname

    # Hilfsfunktion zum Hinzufügen von Text zum aktuellen Chunk
    def add_text(text):
        while "StartAbsatz" in text:
            index = text.index("StartAbsatz")
            # Füge den Text vor "StartAbsatz" zum aktuellen Chunk hinzu
            if index > 0:
                current_chunk.append(text[:index])
            # Speichere den aktuellen Chunk und starte einen neuen
            chunks.append(current_chunk[:])
            current_chunk.clear()
            # Entferne "StartAbsatz" und verarbeite den Rest des Textes
            text = text[index + len("StartAbsatz"):]
        if text:
            # Füge den restlichen Text zum aktuellen Chunk hinzu
            current_chunk.append(text)

    # Verarbeite den anfänglichen Text des <p>-Elements
    if p_elem.text:
        add_text(p_elem.text)
        p_elem.text = None  # Entferne den Text aus dem ursprünglichen Element

    # Iteriere über alle Kinder des <p>-Elements
    for child in list(p_elem):
        # Füge das Kind zum aktuellen Chunk hinzu
        current_chunk.append(child)
        p_elem.remove(child)  # Entferne das Kind aus dem ursprünglichen Element

        # Verarbeite den Tail-Text des Kindes
        if child.tail:
            add_text(child.tail)
            child.tail = None  # Entferne den Tail-Text

    # Füge den letzten aktuellen Chunk zu den Chunks hinzu
    if current_chunk:
        chunks.append(current_chunk)

    # Erstelle neue <p>-Elemente aus den Chunks
    new_p_elements = []
    for chunk in chunks:
        # Erstelle ein neues <p>-Element mit dem gleichen Namespace
        if ns_uri:
            new_p = etree.Element(f"{{{ns_uri}}}{p_tag_name}", nsmap=nsmap)
        else:
            new_p = etree.Element(p_tag_name)

        last_element = None
        for item in chunk:
            if isinstance(item, str):
                # Füge Text hinzu
                if last_element is None:
                    if new_p.text:
                        new_p.text += item
                    else:
                        new_p.text = item
                else:
                    if last_element.tail:
                        last_element.tail += item
                    else:
                        last_element.tail = item
            else:
                # Füge das Element hinzu
                new_p.append(item)
                last_element = item
        new_p_elements.append(new_p)

    return new_p_elements

# Über <article>-Elemente iterieren
ns = root.nsmap  # Namespaces aus der Wurzel erhalten
for article in root.findall('.//article', namespaces=ns):
    # Listen zum Speichern der zu ersetzenden <p>-Elemente
    p_elements_to_remove = []
    new_p_elements_info = []

    # Über die <p>-Elemente innerhalb des <article>-Elements iterieren
    for p_elem in article.findall('.//p', namespaces=ns):
        # Teile das <p>-Element bei jedem Vorkommen von "StartAbsatz"
        new_p_elements = split_p_element(p_elem)

        if len(new_p_elements) > 1:
            # Aufteilung ist erfolgt
            parent = p_elem.getparent()
            index = parent.index(p_elem)
            new_p_elements_info.append((parent, index, new_p_elements))
            p_elements_to_remove.append(p_elem)
        elif len(new_p_elements) == 1:
            # Keine Aufteilung erfolgt; aktualisiere das ursprüngliche <p>-Element
            new_p_elem = new_p_elements[0]
            p_elem.clear()
            p_elem.extend(new_p_elem)
            p_elem.text = new_p_elem.text
        else:
            # new_p_elements ist leer
            # Behandle das leere Element entsprechend deinen Anforderungen
            # Zum Beispiel: Entferne das leere <p>-Element
            parent = p_elem.getparent()
            if parent is not None:
                parent.remove(p_elem)

    # Entferne die markierten ursprünglichen <p>-Elemente
    for p_elem in p_elements_to_remove:
        parent = p_elem.getparent()
        if parent is not None:
            parent.remove(p_elem)

    # Füge die neuen <p>-Elemente an den richtigen Positionen ein
    for parent, index, new_p_elems in new_p_elements_info:
        for offset, new_p in enumerate(new_p_elems):
            parent.insert(index + offset, new_p)

# Aktualisierte XML-Struktur in einer neuen Datei speichern
tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)

print(f"XML file has been processed successfully: {OUTPUT_FILE}")
print("Processing completed successfully.")