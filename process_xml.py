import os
import re
import time
import logging
import json
import xml.etree.ElementTree as ET

# Constants
MIN_WORDS_PARAGRAPH = 5
MAX_RETRIES = 5
BACKOFF_FACTOR = 0.3


def get_prompt():
    """
    Returns the prompt for the AI model.
    This prompt instructs the AI on how to process the text.
    """
    return '''Du bist ein KI-Assistent, als professioneller Lektor lektorierst du das Calwer Bibellexikon von 1912.
        Deine Aufgabe ist es, Textfragmente zu modernisieren und zu formatieren.

        Kontext:
        Das Calwer Bibellexikon ist ein bedeutendes theologisches Nachschlagewerk.
        Deine Bearbeitung soll den Text für moderne Leser zugänglicher machen, ohne den ursprünglichen Sinn zu verfälschen.

        Hauptaufgaben:

        1. Textbearbeitung
            a) Rechtschreibung: Wende die neue deutsche Rechtschreibung vom 01.08.2007 an.
            b) Vokabular: Ersetze veraltete Wörter durch moderne Äquivalente. 
                Beispiel: "ward" → "wurde"
            c) Lexikonformat: Behalte den sachlichen Stil eines Lexikons bei.
            d) Namen: Schreibe den Namen des lexikalischen Artikels im Text aus (keine Abkürzung).
            e) Abkürzungen: Ersetze alle Abkürzungen durch den vollständigen Text.
                Beispiel: "u." → "und", "z.B." → "zum Beispiel"

        2. Formatierung
            a) **XML-Tags**: Bewahre alle vorhandenen XML-Tags an ihrer ursprünglichen Position.
            b) **Absätze**: Gliedere Artikel mit mindestens drei Sätzen in Absätze.
            Markiere neue Absätze wie folgt:
            ***Start Absatz***
            [Absatztext]
            ***Ende Absatz***

        3. Ausgabe
            - Gib ausschließlich das bearbeitete Textfragment mit den originalen XML-Tags zurück.
            - Vermeide jeglichen weiteren Kommentar.

        Hinweis: Hier beginnt das Textfragment der XML-Datei:'''


def get_text(element: ET.Element) -> str:
    """
    Extracts all text from an XML element and its children.
    """
    return ''.join(element.itertext())


def generate_content_with_retries(model, prompt: str, chunk: str) -> str:
    """
    Attempts to generate content using the AI model with retry mechanism.
    """
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Attempting content generation (Attempt {attempt + 1}/{MAX_RETRIES})...")
            return model.generate_content(prompt + chunk).text
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


def load_checkpoint(checkpoint_file):
    """
    Loads the checkpoint file containing processed articles.
    """
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint_file, processed_articles):
    """
    Saves the processed articles to the checkpoint file.
    """
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(processed_articles, f, ensure_ascii=False)


def update_checkpoint(checkpoint_file, processed_articles, article_id):
    """
    Updates the checkpoint file with a newly processed article.
    """
    processed_articles[article_id] = True
    save_checkpoint(checkpoint_file, processed_articles)


def process_paragraph(model, p):
    """
    Processes a single paragraph using the AI model.
    """
    content = ET.tostring(p, encoding='unicode', method='xml')
    content_text = get_text(p)
    # print commands for debugging purpose only.
    # print("content: ", content)
    # print(f"\nContent text: {content_text}")

    if len(content_text.split()) > MIN_WORDS_PARAGRAPH:
        response = generate_content_with_retries(model, get_prompt(), content)
        # print commands for debugging purpose only.
        # print()
        # print("response direkt aus KI: ", response)

        content_tags = re.findall(r'<[^>]+>', content)
        response_tags = re.findall(r'<[^>]+>', response)
        tags_match = content_tags == response_tags

        if tags_match:
            # Perform the requested string replacements
            response = response.replace("***Start Absatz***", "<p>")
            response = response.replace("***Ende Absatz***", "</p>")
            #response = response.replace("~SH~", '<p field="heading" class="head2">')
            #response = response.replace("~EH~", "</p>")

            response_text = re.sub(r'<[^>]+>', '', response)
            # print commands for debugging purpose only.
            # print(f"\nResponse text: {response_text}")

            log_text = "XML tags in content and response are identical."
            print(log_text)

            try:
                p.clear()
                # print commands for debugging purpose only.
                # print("response: ", response)
                response_element = ET.fromstring(response)
                p.append(response_element)
                return True, log_text, content_text, response_text

            except Exception as e:
                # Write original content back in xml-file
                response_element = ET.fromstring(content)
                p.append(response_element)
                log_text = f"An error occurred in process_paragraph(): {e} Keeping original content."
                print(log_text)
                return False, log_text, content_text, response_text

        else:
            response_text = re.sub(r'<[^>]+>', '', response)
            # print commands for debugging purpose only.
            # print(f"\nResponse text: {response_text}")
            log_text = "Warning: XML tags in content and response do not match. Keeping original content."
            print(log_text)
            return False, log_text, content_text, response_text
    else:
        log_text = "Paragraph too short, skipped processing."
        print(log_text)
    return False, log_text, content_text, "N/A"


def process_article(model, article, processed_articles, checkpoint_file):
    """
    Processes a single article, updating its paragraphs.
    """
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
            "id": article_id,
            "status": "success" if modified else "error",
            "message": log_text,
            "content": content_text,
            "response": response_text
        }
        logging.info(json.dumps(log_entry, ensure_ascii=False))

    if article_modified:
        update_checkpoint(checkpoint_file, processed_articles, article_id)

    return article_modified


def process_xml_file(file_path: str, model, output_txt_dir, finished_dir, checkpoint_file, output_file) -> ET.Element:
    """
    Main function to process the XML file.
    It iterates through all articles, processes them, and updates the file.
    """
    print(f"Processing XML file: {file_path}")
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.parse(file_path, parser=parser)
    root = tree.getroot()

    processed_articles = load_checkpoint(checkpoint_file)

    for article in root.findall('.//article'):
        if process_article(model, article, processed_articles, checkpoint_file):
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            print(f"XML file has been updated: {output_file}")

    print(f"XML file has been processed successfully: {file_path}")
    return root


if __name__ == "__main__":
    # This block is for testing purposes only
    from main import initialize_model, configure_logging, INPUT_FILE, OUTPUT_TXT_DIR, FINISHED_DIR, CHECKPOINT_FILE, OUTPUT_FILE
    configure_logging()
    model = initialize_model()
    process_xml_file(INPUT_FILE, model, OUTPUT_TXT_DIR, FINISHED_DIR, CHECKPOINT_FILE, OUTPUT_FILE)
