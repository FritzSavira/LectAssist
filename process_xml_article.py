import os
import re
import time
import logging
import json
from openai import OpenAI
import xml.etree.ElementTree as ET

MIN_WORDS_ARTICLE = 50
MAX_RETRIES = 5
BACKOFF_FACTOR = 0.3


def get_prompt():
    return '''Du bist ein KI-Assistent, als professioneller Lektor lektorierst du ein Lexikon.

Prämisse: - XML-Tags und XML-Elemente müssen an ihrer ursprünglichen Position bleiben.
          - Lasse den Wortlaut des Textes unverändert.

Hauptaufgaben:
1. Textbearbeitung
    a) Analysiere die Semantik des folgenden lexikalischen Eintrags.
    b) Finde basierend auf der semantischen Analyse kurze Schlagzeilen (Zeitungsstil) zu dem lexikalischen Eintrag.
       Die Schlagzeilen sollen den Text thematisch gliedern.
       Füge die Schlagzeilen in doppelt geschweiften Klammern in den Text ein.
       Die Schlagzeile wird immer unmittelbar vor dem zugehörigen Text platziert.
   
3. Ausgabe
    - Gib ausschließlich das bearbeitete Textfragment mit den originalen XML-Tags zurück.
    - Vermeide jeglichen weiteren Kommentar.

Hinweis: Hier beginnt der lexikalische Eintrag:'''


def get_text(element: ET.Element) -> str:
    return ''.join(element.itertext())


def call_ai(PROVIDER, model, prompt, chunk):
    if PROVIDER == 'google':
        return model.generate_content(prompt + chunk).text

    elif PROVIDER == 'openai':
        client = OpenAI()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": chunk}
            ],
            temperature=0.4
        )
        return completion.choices[0].message.content


def generate_content_with_retries(PROVIDER, model, chunk: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Attempting content generation (Attempt {attempt + 1}/{MAX_RETRIES})...")
            return call_ai(PROVIDER, model, get_prompt(), chunk)
        except ConnectionError:
            if attempt < MAX_RETRIES - 1:
                sleep_time = BACKOFF_FACTOR * (2 ** attempt)
                print(f"Connection error. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Maximum number of attempts reached. Connection not possible.")
                raise
        except Exception as e:
            print(f"An error occurred in generate_content(): {e}")
            return str(e)


def load_checkpoint(checkpoint_file):
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint_file, processed_articles):
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(processed_articles, f, ensure_ascii=False)


def update_checkpoint(checkpoint_file, processed_articles, article_id):
    processed_articles[article_id] = True
    save_checkpoint(checkpoint_file, processed_articles)

def convert_headline_in_xml():
    # '< p field = "heading" class ="headX" > Neue Unter-Überschrift < / p >'
    pass



def remove_redundant_article_tags(element):
    children = list(element)
    for index, child in enumerate(children):
        if child.tag == 'article' and not child.attrib:
            if len(child) == 1 and child[0].tag == 'article':
                element.remove(child)
                element.insert(index, child[0])
                remove_redundant_article_tags(child[0])
            else:
                remove_redundant_article_tags(child)
        else:
            remove_redundant_article_tags(child)


def process_article(PROVIDER, model, article, processed_articles, checkpoint_file):
    article_id = article.get('id')
    if article_id in processed_articles:
        print(f"Skipping already processed article: {article_id}")
        return False

    print(f"\nProcessing article ID: {article_id}")

    content = ET.tostring(article, encoding='unicode', method='xml')
    content_text = get_text(article)

    print("\n*** NEW ARTICLE ***")
    if len(content_text.split()) > MIN_WORDS_ARTICLE:
        response = generate_content_with_retries(PROVIDER, model, content)
        response_text = re.sub(r'<[^>]+>', '', response)
        print("content_text: ")
        print(content_text)
        print()
        print("response_text: ")
        print(response_text)
        article.clear()
        try:
            response_element = ET.fromstring(response)
            article.append(response_element)
            log_text = "Article processed successfully."
            print(log_text)
            modified = True
        except Exception as e:
            article.append(ET.fromstring(content))  # Keep original content
            log_text = f"An error occurred in process_article(): {e} - Keep original content from xml-file"
            print(log_text)
            modified = False
    else:
        log_text = "Article too short, skipped processing."
        print(log_text)
        modified = True  # Considered as processed, so we can update the checkpoint

    log_entry = {
        "id": article_id,
        "status": "success" if modified else "error",
        "message": log_text,
        "content_text": content_text,
        "response_text": response_text if 'response_text' in locals() else "N/A",
        "content": content,
        "response": response if 'response' in locals() else "N/A"
    }

    logging.info(json.dumps(log_entry, ensure_ascii=False))

    if modified:
        update_checkpoint(checkpoint_file, processed_articles, article_id)

    return modified


def process_xml_file(PROVIDER, model, file_path: str, checkpoint_file, output_file, start_article=0) -> ET.Element:
    print(f"Processing XML file: {file_path}")
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.parse(file_path, parser=parser)
    root = tree.getroot()
    processed_articles = load_checkpoint(checkpoint_file)
    articles = root.findall('.//article')

    for idx, article in enumerate(articles[start_article:], start=start_article + 1):
        print(f"Article Nr.: {idx}")
        if process_article(PROVIDER, model, article, processed_articles, checkpoint_file):
            remove_redundant_article_tags(root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            print(f"XML file has been updated: {output_file}")
    print(f"XML file has been processed successfully: {file_path}")
    return root