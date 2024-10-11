# Import der notwendigen Bibliothek
from lxml import etree
import os

# Input filename
INPUT_FILENAME = 'CalwerFULL_241009_out_TransBiblEnDe_AbsInXml_B_out.xml'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/'
FINISHED_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/erledigt/'
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/bearbeitet/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_Ueb.xml')


# XML-Datei einlesen
tree = etree.parse(INPUT_FILE)
root = tree.getroot()

root_string = etree.tostring(root, encoding='unicode')

root_string_headline_o = root_string.replace('{{', '<p field="heading" class="head3">')
root_string_headline_oc = root_string_headline_o.replace('}}', '</p>')


root = etree.fromstring(root_string_headline_oc)

# Erstellen Sie ein neues ElementTree-Objekt mit dem modifizierten root
new_tree = etree.ElementTree(root)

# Speichern Sie das neue ElementTree-Objekt als XML-Datei
new_tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True, pretty_print=True)

print(f"XML file has been processed successfully: {OUTPUT_FILE}")
print("Processing completed successfully.")