import xml.etree.ElementTree as ET
import os

INPUT_FILENAME = 'CalwerFULL_240929_out_clean_p_clean_p.xml'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_clean_p.xml')

def remove_redundant_p_tags(xml_file_path, output_file_path):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Function to recursively process XML elements
    def process_element(element):
        # Make a copy of the list of children to iterate over
        children = list(element)
        # Iterate over the indices and child elements
        for index, child in enumerate(children):
            # If the child is a <p> tag without attributes
            if child.tag == 'p' and not child.attrib:
                # If the <p> tag has only one child which is also a <p> tag
                if len(child) == 1 and child[0].tag == 'p':
                    # Remove the current child
                    element.remove(child)
                    # Insert the grandchild at the original position
                    element.insert(index, child[0])
                    # Process the new child recursively
                    process_element(child[0])
                else:
                    # Process the child recursively
                    process_element(child)
            else:
                # Process the child recursively
                process_element(child)

    # Start processing from the root
    process_element(root)

    # Write the modified XML back to a file
    tree.write(output_file_path, encoding='utf-8', xml_declaration=True)


remove_redundant_p_tags(INPUT_FILE, OUTPUT_FILE)
