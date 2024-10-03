import os
import re
import time
import logging
import json
import subprocess
import xml.etree.ElementTree as ET

# Constants
MIN_WORDS_PARAGRAPH = 5
MAX_RETRIES = 5
BACKOFF_FACTOR = 0.3
STRAICO_API_KEY = 'iv-oKfDouiGpue58YhI6KYQcLdNNdkw70hvosoeypwaYY41X6zA'


def get_prompt():
    """
    Returns the prompt for the AI model.
    This prompt instructs the AI on how to process the text.
    """
    return '''Du bist ein KI-Assistent, als professioneller Lektor lektorierst du ein Lexikon.
        
        Prämisse: XML-Tags und XML-Elemente müssen an ihrer ursprünglichen Position bleiben.
                Vermeide neue XML-Tags.
                Vermeide neue XML-Elemente.
        
        Hauptaufgaben:
        1. Textbearbeitung
            a) Rechtschreibung: Wende die neue deutsche Rechtschreibung vom 01.08.2007 an.
            b) Vokabular: Ersetze veraltete Wörter durch moderne Äquivalente. 
                Beispiel: "ward" → "wurde"
            c) Lexikonformat: Behalte den sachlichen Stil eines Lexikons bei.
            d) Namen: Schreibe den Namen des lexikalischen Artikels im Text aus (keine Abkürzung).
            e) Abkürzungen: Ersetze Abkürzungen in den Textknoten durch den vollständigen Text.
                Beispiel: "u." → "und", "z.B." → "zum Beispiel"  
            f) Nutze das deutsche System von Anführungszeichen „ ".

        2. Formatierung
            a) XML: XML-Tags und XML-Elemente müssen an ihrer ursprünglichen Position bleiben.
            b) Absätze: Gliedere Artikel mit mehr als drei Sätzen in thematische Absätze, sofern vorhanden.
            Markiere den Beginn eines neuen Absatzes mit 'StartAbsatz'

        3. Ausgabe
            - Gib ausschließlich das bearbeitete Textfragment mit den originalen XML-Tags zurück.
            - Vermeide jeglichen weiteren Kommentar.
        
        Wichtig: XML-Tags und XML-Elemente müssen an ihrer ursprünglichen Position bleiben.
        
        Hinweis: Hier beginnt das Textfragment der XML-Datei:'''


def get_text(element: ET.Element) -> str:
    """
    Extracts all text from an XML element and its children.
    """
    return ''.join(element.itertext())


def generate_content_with_retries_google(model, prompt: str, chunk: str) -> str:
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


def generate_content_straico(model, prompt: str, chunk: str) -> str:
    data = {
        "model": "anthropic/claude-3.5-sonnet",
        "message": prompt + chunk
    }

    json_data = json.dumps(data, ensure_ascii=False)

    curl_command = [
        'curl',
        '--location', 'https://api.straico.com/v0/prompt/completion',
        '--header', f'Authorization: Bearer {STRAICO_API_KEY}',
        '--header', 'Content-Type: application/json',
        '--data', json_data
    ]
    # Versuche, die Ausgabe als JSON zu parsen
    output_json = json.loads(subprocess.run(curl_command, capture_output=True, text=True).stdout)

    # Überprüfe, ob 'content' im JSON vorhanden ist
    if 'content' in output_json['data']['completion']['choices'][0]['message']:
        content = output_json['data']['completion']['choices'][0]['message']['content']
        print(content)
    else:
        pass
    return content





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
    print()
    print("*** NEUER PARAGRAPH ***")

    if len(content_text.split()) > MIN_WORDS_PARAGRAPH:
        # Print commands for debugging purposes only.
        # print("content: ", content)

        response = generate_content_with_retries_google(model, get_prompt(), content)

        # Print commands for debugging purposes only.
        # print()
        # print("response direkt aus KI: ", response)

        content_tags = re.findall(r'<[^>]+>', content)
        response_tags = re.findall(r'<[^>]+>', response)
        tags_match = content_tags == response_tags

        if tags_match:
            # Perform the requested string replacements
            #response = response.replace('StartAbsatz', '</p><p class="Body">')
            # response = response.replace("EndeAbsatz", "</p>")
            # response = response.replace("~SH~", '<p field="heading" class="head2">')
            # response = response.replace("~EH~", "</p>")

            response_text = re.sub(r'<[^>]+>', '', response)
            # Print commands for debugging purposes only.
            # print(f"\nResponse text: {response_text}")

            log_text = "XML tags in content and response are identical."
            print(log_text)

            try:
                p.clear()
                # Print commands for debugging purposes only.
                # print()
                # print("response: ", response)
                response_element = ET.fromstring(response)
                p.append(response_element)

                return True, log_text, content_text, response_text, content, response

            except Exception as e:
                # Write original content back in xml-file
                response_element = ET.fromstring(content)
                p.append(response_element)
                log_text = f"An error occurred in process_paragraph(): {e} Keeping original content."
                print(log_text)
                return False, log_text, content_text, response_text, content, "N/A"

        else:
            # Extended comparison to display differences

            print()
            print("Warning: XML tags in content and response do not match.")
            print("Differences between content_tags and response_tags:")

            # Determine the maximum length between the two lists
            max_length = max(len(content_tags), len(response_tags))
            for i in range(max_length):
                ctag = content_tags[i] if i < len(content_tags) else 'None'
                rtag = response_tags[i] if i < len(response_tags) else 'None'
                if ctag != rtag:
                    print(f"At position {i}: content_tag = {ctag}  response_tag = {rtag}")

            response_text = re.sub(r'<[^>]+>', '', response)
            # Print commands for debugging purposes only.
            # print(f"\nResponse text: {response_text}")
            log_text = "!!!Warning: XML tags in content and response do not match!!!"
            print(log_text)
            p.clear()
            # Print commands for debugging purposes only.
            # print()
            # print("response: ", response)
            # Parse the response string into an XML element
            print("response:", response)
            response_element = ET.fromstring(response)
            print("check1")
            # Insert log_text at the beginning of the first text node
            found = False
            for elem in response_element.iter():
                if elem.text and elem.text.strip():
                    elem.text = log_text + elem.text
                    found = True
                    break
            if not found:
                # If no text node found with text, insert log_text in root's text
                if response_element.text:
                    response_element.text = log_text + response_element.text
                else:
                    response_element.text = log_text
            print("response_element:", response_element)
            p.append(response_element)
            return True, log_text, content_text, response_text, content, response
    else:
        log_text = "Paragraph too short, skipped processing."
        print(log_text)
        return True, log_text, content_text, "N/A", content, "N/A"


def process_article(model, article, processed_articles, checkpoint_file):
    """
    Processes a single article, updating its paragraphs.
    """
    article_id = article.get('id')
    if article_id in processed_articles:
        print(f"Skipping already processed article: {article_id}")
        return False

    print(f"\nProcessing article_id: {article_id}")
    article_modified = True

    for p in article.findall('.//p'):
        modified, log_text, content_text, response_text, content, response = process_paragraph(model, p)
        if not modified:
            article_modified = False

        log_entry = {
            "id": article_id,
            "status": "success" if modified else "error",
            "message": log_text,
            "content_text": content_text,
            "response_text": response_text,
            "content": content,
            "response": response


        }
        logging.info(json.dumps(log_entry, ensure_ascii=False))

    if article_modified:
        update_checkpoint(checkpoint_file, processed_articles, article_id)

    return article_modified


def process_xml_file(file_path: str, model, output_txt_dir, finished_dir, checkpoint_file, output_file,
                     start_article=1579) -> ET.Element:
    """
    Main function to process the XML file.
    It iterates through all articles starting from the specified start_article index, processes them, and updates the file.
    """
    print(f"Processing XML file: {file_path}")
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.parse(file_path, parser=parser)
    root = tree.getroot()

    processed_articles = load_checkpoint(checkpoint_file)

    # Retrieve all articles into a list
    articles = root.findall('.//article')

    # Iterate over articles starting from start_article
    for article in articles[start_article:]:
        start_article = start_article + 1
        print("Nr.: ", start_article)
        if process_article(model, article, processed_articles, checkpoint_file):
            tree.write(output_file, encoding='utf-8', xml_declaration=True)

            print(f"XML file has been updated: {output_file}")
            pass

    print(f"XML file has been processed successfully: {file_path}")
    return root

