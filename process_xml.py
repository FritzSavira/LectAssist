import os
import re
import time
import logging
import json
import xml.etree.ElementTree as ET

# Constants
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/'
OUTPUT_TXT_DIR = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt'
FINISHED_DIR = 'C:/Users/Fried/documents/LectorAssistant/erledigt'
INPUT_FILE = os.path.join(DIRECTORY_PATH, 'DEPDBIBLEN-Content.xml')
OUTPUT_FILE = os.path.join(OUTPUT_TXT_DIR, 'output.xml')
CHECKPOINT_FILE = os.path.join(DIRECTORY_PATH, 'checkpoint.json')
MAX_RETRIES = 5
BACKOFF_FACTOR = 0.3
MIN_WORDS_PARAGRAPH = 5

def get_prompt():
    return '''Du bist ein professioneller Lektor und lektorierst die hochgeladenen Textfragmente des
        Calwer Bibellexikons der Ausgabe von 1912.
        Verwende den Wortschatz des 21. Jahrhunderts.
        Verwende die Rechtschreibung des 21. Jahrhunderts.
        Verwende die Grammatik des 21. Jahrhunderts.
        Ersetze veraltete und selten gebrauchte Vokabeln durch aktuelle und häufig verwendete Vokabeln.
        Formuliere den Text in flüssig zu lesendes Schriftdeutsch um.
        Beachte, dass es sich um ein Lexikon handelt.

        2. Formatierung:
        - Die Textfragmente enthalten xml-Tags. Diese Tags müssen an der selben Stelle
          im ursprünglichen Textfragment erhalten bleiben. 
        - Die xml-Tags dürfen nicht verändert werden.

        3. Ausgabe:
        - Gib ausschließlich das bearbeitete Textfragment inclusive der ursprünglichen xml-Tags zurück.
        - Vermeide jeglichen weiteren Kommentar.
          Hier beginnt das Textfragment der xml-Datei:'''

def get_text(element: ET.Element) -> str:
    return ''.join(element.itertext())

def generate_content_with_retries(model, prompt: str, chunk: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Attempting content generation (Attempt {attempt + 1}/{MAX_RETRIES})...")
            response = model.generate_content(prompt + chunk)
            return response.text
        except ConnectionError as e:
            if attempt < MAX_RETRIES - 1:
                sleep_time = BACKOFF_FACTOR * (2 ** attempt)
                print(f"Connection error. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Maximum number of attempts reached. Connection not possible.")
                raise e
        except Exception as e:
            print(f"An error occurred in generate_content(): {e}")
            return str(e)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_checkpoint(processed_articles):
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_articles, f, ensure_ascii=False)

def update_checkpoint(processed_articles, article_id):
    processed_articles[article_id] = True
    save_checkpoint(processed_articles)

def compare_xml_tags(content: str, response: str) -> bool:
    content_tags = re.findall(r'<[^>]+>', content)
    response_tags = re.findall(r'<[^>]+>', response)
    return content_tags == response_tags

def process_paragraph(model, p):
    content = ET.tostring(p, encoding='unicode', method='xml')
    content_text = get_text(p)
    print(f"\nContent text: {content_text}")

    if len(content_text.split()) > MIN_WORDS_PARAGRAPH:
        response = generate_content_with_retries(model, get_prompt(), content)
        response_text = re.sub(r'<[^>]+>', '', response)
        print(f"\nResponse text: {response_text}")

        tags_match = compare_xml_tags(content, response)
        if tags_match:
            log_text = "XML tags in content and response are identical."
            print()
            print(log_text)
            p.clear()
            response_element = ET.fromstring(response)
            p.append(response_element)
            return True, log_text, content_text, response_text
        else:
            log_text = "Warning: XML tags in content and response do not match. Keeping original content."
            print(log_text)
            return False, log_text, content_text, response_text

    return False, "Paragraph too short, skipped processing.", content_text, "N/A"

def process_article(model, article, processed_articles):
    article_id = article.get('id')
    if article_id in processed_articles:
        print(f"Skipping already processed article: {article_id}")
        return False

    print(f"\nProcessing article_id: {article_id}")
    article_modified = False

    for p in article.findall('.//p'):
        modified, log_text, content_text, response_text = process_paragraph(model, p)
        if modified:
            article_modified = True

        log_entry = {
            "article_id": article_id,
            "log_text": log_text,
            "content_text": content_text,
            "response_text": response_text
        }
        logging.info(json.dumps(log_entry, ensure_ascii=False))

    if article_modified:
        update_checkpoint(processed_articles, article_id)

    return article_modified

def process_xml_file(file_path: str, model) -> ET.Element:
    print(f"Processing XML file: {file_path}")
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.parse(file_path, parser=parser)
    root = tree.getroot()

    processed_articles = load_checkpoint()

    for article in root.findall('.//article'):
        if process_article(model, article, processed_articles):
            tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
            print(f"XML file has been updated: {OUTPUT_FILE}")

    print(f"XML file has been processed successfully: {file_path}")
    return root

if __name__ == "__main__":
    # This block is for testing purposes only
    from main import initialize_model, configure_logging
    configure_logging()
    model = initialize_model()
    process_xml_file(INPUT_FILE, model)