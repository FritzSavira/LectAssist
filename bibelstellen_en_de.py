'''Übersetzt die englischen Bibelstellenverweise in standardisierte deutsche Labels im Text
im Logos xml-Format.'''

import xml.etree.ElementTree as ET
import os

# Input filename
INPUT_FILENAME = 'CalwerFULL_241009_out.xml'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/'
FINISHED_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/erledigt/'
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/logos_tags/bearbeitet/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_TransBiblEnDe.xml')

transl_bibl_books = {
    "Bible:Ge": "1Mos.",
    "Bible:Ex": "2Mos.",
    "Bible:Le": "3Mos.",
    "Bible:Nu": "4Mos.",
    "Bible:Dt": "5Mos.",
    "Bible:Jos": "Jos.",
    "Bible:Jdg": "Richt.",
    "Bible:Ru": "Ruth",
    "Bible:1 Sa": "1Sam.",
    "Bible:2 Sa": "2Sam.",
    "Bible:1 Ki": "1Kön.",
    "Bible:2 Ki": "2Kön.",
    "Bible:2 K": "2Kön.",
    "Bible:1 Ch": "1Chr.",
    "Bible:2 Ch": "2Chr.",
    "Bible:Ezr": "Esr.",
    "Bible:Ne": "Neh.",
    "Bible:Es": "Est.",
    "Bible:Job": "Hiob",
    "Bible:Ps": "Psa.",
    "Bible:Pr": "Spr.",
    "Bible:Ec": "Pred.",
    "Bible:So": "Hohel.",
    "Bible:Song": "Hohel.",
    "Bible:Is": "Jes.",
    "Bible:Let": "Jer.",
    "Bible:Je": "Jer.",
    "Bible:La": "Kla.",
    "Bible:Eze": "Hes.",
    "Bible:Da": "Dan.",
    "Bible:De": "Dan.", # Fehler in Originaldatei
    "Bible:Ho": "Hos.",
    "Bible:Hos": "Hos.",
    "Bible:Joe": "Joe.",
    "Bible:Am": "Amos",
    "Bible:Ob": "Oba.",
    "Bible:Jon": "Jon.",
    "Bible:Mic": "Micha",
    "Bible:Na": "Nah.",
    "Bible:Hab": "Hab.",
    "Bible:Zep": "Zef.",
    "Bible:Hag": "Hag.",
    "Bible:Zec": "Sach.",
    "Bible:Mal": "Mal.",
    "Bible:Mt": "Matth.",
    "Bible:Mk": "Mark.",
    "Bible:Lk": "Luk.",
    "Bible:Jn": "Joh.",
    "Bible:Ac": "Apg.",
    "Bible:Ro": "Röm.",
    "Bible:1 Co": "1Kor.",
    "Bible:2 Co": "2Kor.",
    "Bible:Ga": "Gal.",
    "Bible:Eph": "Eph.",
    "Bible:Php": "Phil.",
    "Bible:Col": "Kol.",
    "Bible:1 Th": "1Thes.",
    "Bible:2 Th": "2Thes.",
    "Bible:1 Ti": "1Tim.",
    "Bible:2 Ti": "2Tim.",
    "Bible:Tt": "Tit.",
    "Bible:Tit": "Tit.",
    "Bible:Phm": "Philem.",
    "Bible:Heb": "Hebr.",
    "Bible:Jas": "Jak.",
    "Bible:1 Pe": "1Petr.",
    "Bible:2 Pe": "2Petr.",
    "Bible:1 Jn": "1Joh.",
    "Bible:2 Jn": "2Joh.",
    "Bible:3 Jn": "3Joh.",
    "Bible:Jud": "Jud.",
    "Bible:Re": "Offb.",
    "Bible:Sir": "Sir.",
    "Bible:1 Mac": "1Makk.",
    "Bible:2 Mac": "2Makk.",
    "Bible:Wis": "Weish.",
    "Bible:Jdt": "Judit",
    "Bible:Tob": "Tob.",
    "Bible:Sus": "Sus.",
    "Bible:Bel": "Bel.",
    "Bible:Bar": "Bar.",
    "Bible:LJe": "Bar.",
    "Bible:He": "Hen."
}


def read_xml_file(input_file):
    """ Function to read the XML file. """
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.parse(input_file, parser=parser)
    return tree

def get_tags(root):
    """Erstellt ein Dictionary mit XML-Tags, Textinhalt und schließendem Tag."""
    tags_dict = {}

    def traverse_element(element):
        # Konstruktion des öffnenden Tags mit Attributen
        opening_tag = '<' + element.tag
        for attr_name, attr_value in element.attrib.items():
            opening_tag += f' {attr_name}="{attr_value}"'
        opening_tag += '>'

        # Inhalt des Textknotens
        text_content = element.text.strip() if element.text and element.text.strip() else ''

        # Konstruktion des schließenden Tags
        closing_tag = f'</{element.tag}>'

        # Überprüfen, ob das Tag bereits im Dictionary vorhanden ist
        if opening_tag in tags_dict:
            # Wenn ja, fügen wir ein weiteres Vorkommen hinzu
            tags_dict[opening_tag].append({'text': text_content, 'closing_tag': closing_tag})
        else:
            # Wenn nicht, erstellen wir einen neuen Eintrag
            tags_dict[opening_tag] = [{'text': text_content, 'closing_tag': closing_tag}]

        # Rekursives Durchlaufen der Kindelemente
        for child in element:
            traverse_element(child)

    # Starten der Traversierung mit der Wurzel des Baums
    traverse_element(root)

    return tags_dict

def find_second_colon(text):
    first_colon = text.find(':')
    if first_colon != -1:
        return text.find(':', first_colon + 1)
    return -1


def find_and_translate_bible_elements(root, transl_bibl_books):
    elements_to_modify = []
    for elem in root.iter('data'):
        ref = elem.get('ref', '')
        if ref.startswith('Bible:'):
            elements_to_modify.append(elem)
        else:
            pass


    for elem in elements_to_modify:
    # Perform the modifications here

        elem_str = ET.tostring(elem, encoding='unicode', method='xml')
        print()
        print("elem_str: ", elem_str)

        # Biblisches Buchname aus englischer in deutsche Abkürzung übersetzen
        start_elem = elem_str.find('Bible:')
        end_tag_elem = elem_str.find('">')
        mit_kap_vers_elem = elem_str[start_elem:end_tag_elem]
        ohne_kap_vers_elem = mit_kap_vers_elem.find(' ', 8)
        bibl_books_en = elem_str[start_elem:end_tag_elem][
                        :ohne_kap_vers_elem]  # Das ist der String mit dem man als Schlüssel das Dictionary durchsucht.
        bibl_books_de = transl_bibl_books[bibl_books_en]

        # Kapitel und Vers aus englischer in deutsche Schreibweise übersetzen
        start_elem_vers = elem_str[:end_tag_elem]
        end_elem_vers = start_elem_vers.rfind(' ')
        elem_vers_en = start_elem_vers[end_elem_vers:]
        elem_vers_de = elem_vers_en.replace(':', ', ')

        bible_ref_de = bibl_books_de + elem_vers_de
        print("bible_ref_de: ", bible_ref_de)
        elem.text = bible_ref_de


    return root

def main():
    """Main function to run the script."""

    # Step 1: Read xml-file
    tree = read_xml_file(INPUT_FILE)

    # Step 2: Finden und Drucken der gewünschten XML-Elemente
    root = tree.getroot()
    print(root)
    root = find_and_translate_bible_elements(root, transl_bibl_books)

    # Step 3: Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_FILE)
    os.makedirs(output_dir, exist_ok=True)

    # Step 4: Write the processed XML file to disk
    print(f"Start writing the processed XML file to: {OUTPUT_FILE}")

    new_tree = ET.ElementTree(root)
    with open(OUTPUT_FILE, 'wb') as file:
        new_tree.write(file, encoding='utf-8', xml_declaration=True)

    print(f"Processed XML file written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()