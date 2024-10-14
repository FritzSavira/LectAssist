import os
import re
import time
import logging
import json
from openai import OpenAI
import xml.etree.ElementTree as ET

# Constants
MIN_WORDS_PARAGRAPH = 5  # Minimum number of words for a paragraph to be processed
MAX_RETRIES = 5  # Maximum number of retries for content generation
BACKOFF_FACTOR = 0.3  # Factor for exponential backoff in case of connection errors

def get_prompt():
    """
    Returns the prompt for the AI model in German.
    This prompt instructs the AI on how to process and edit the lexicon entries.
    """
    return '''Du bist ein KI-Assistent, als professioneller Lektor lektorierst du ein Lexikon.

Prämisse:
- XML-Tags und XML-Elemente müssen an ihrer ursprünglichen Position bleiben.

Hauptaufgaben:
1. Textbearbeitung
    b) Formuliere den Text in heute gebräuchliches Deutsch um.
    b) Der Text soll flüssig zu lesen sein und verschachtelte Sätze werden in ihre Hauptaussagen aufgeteilt.
    c) Teile längere Texte in thematische Absätze auf. Füge an den Start des neuen Absatzes "StartAbsatz" ein.
    d) Namen: Schreibe den Namen des lexikalischen Artikels im Text aus (keine Abkürzung).
    
3. Ausgabe
    - Gib ausschließlich das bearbeitete Textfragment mit den originalen XML-Tags zurück.
    - Vermeide jeglichen weiteren Kommentar.

Hinweis: Hier beginnt das Textfragment der XML-Datei:'''


def get_text(element: ET.Element) -> str:
    """
    Extracts all text from an XML element and its children.

    Args:
    element (ET.Element): The XML element to extract text from.

    Returns:
    str: The concatenated text content of the element and its children.
    """
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
            temperature=0.6
        )
        return completion.choices[0].message.content


def generate_content_with_retries(PROVIDER, model, chunk: str) -> str:
    """
    Attempts to generate content using the AI model with a retry mechanism.

    Args:
    model: The AI model used for content generation.
    prompt (str): The prompt to guide the AI's response.
    chunk (str): The text chunk to be processed.

    Returns:
    str: The generated content or an error message.
    """
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
    """
    Loads the checkpoint file containing processed articles.

    Args:
    checkpoint_file (str): Path to the checkpoint file.

    Returns:
    dict: A dictionary of processed articles.
    """
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint_file, processed_articles):
    """
    Saves the processed articles to the checkpoint file.

    Args:
    checkpoint_file (str): Path to the checkpoint file.
    processed_articles (dict): Dictionary of processed articles.
    """
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(processed_articles, f, ensure_ascii=False)


def update_checkpoint(checkpoint_file, processed_articles, article_id):
    """
    Updates the checkpoint file with a newly processed article.

    Args:
    checkpoint_file (str): Path to the checkpoint file.
    processed_articles (dict): Dictionary of processed articles.
    article_id (str): ID of the newly processed article.
    """
    processed_articles[article_id] = True
    save_checkpoint(checkpoint_file, processed_articles)


def remove_redundant_p_tags(element):
    """
    Recursively removes redundant <p> tags from the XML structure.

    Args:
    element (ET.Element): The XML element to process.
    """
    children = list(element)
    for index, child in enumerate(children):
        if child.tag == 'p' and not child.attrib:
            if len(child) == 1 and child[0].tag == 'p':
                element.remove(child)
                element.insert(index, child[0])
                remove_redundant_p_tags(child[0])
            else:
                remove_redundant_p_tags(child)
        else:
            remove_redundant_p_tags(child)


def process_paragraph(PROVIDER, model, paragraph):
    """
    Processes a single paragraph using the AI model.

    Args:
    model: The AI model used for content generation.
    paragraph (ET.Element): The paragraph XML element to process.

    Returns:
    tuple: A tuple containing processing status, log text, and other relevant information.
    """

    content = ET.tostring(paragraph, encoding='unicode', method='xml')
    content_text = get_text(paragraph)
    print("\n*** NEW PARAGRAPH ***")
    if len(content_text.split()) > MIN_WORDS_PARAGRAPH:
        response = generate_content_with_retries(PROVIDER, model, content)
        response_text = re.sub(r'<[^>]+>', '', response)
        print("content_text: ")
        print(content_text)
        print()
        print("response_text: ")
        print(response_text)
        paragraph.clear()
        try:
            response_element = ET.fromstring(response)
            paragraph.append(response_element)
            log_text = "Paragraph processed successfully."
            print(log_text)
            return True, log_text, content_text, response_text, content, response
        except Exception as e:
            response_element = ET.fromstring(content)
            paragraph.append(response_element)
            log_text = f"An error occurred in process_paragraph(): {e} - Keep original content from xml-file"
            print(log_text)
            return False, log_text, content_text, response_text, content, response
    else:
        log_text = "Paragraph too short, skipped processing."
        print(log_text)
        return True, log_text, content_text, "N/A", content, "N/A"


def process_article(PROVIDER, model, article, processed_articles, checkpoint_file):
    """
    Processes a single article, updating its paragraphs.

    Args:
    model: The AI model used for content generation.
    article (ET.Element): The article XML element to process.
    processed_articles (dict): Dictionary of processed articles.
    checkpoint_file (str): Path to the checkpoint file.

    Returns:
    bool: True if the article was modified, False otherwise.
    """
    article_id = article.get('id')
    if article_id in processed_articles:
        print(f"Skipping already processed article: {article_id}")
        return False

    print(f"\nProcessing article ID: {article_id}")
    article_modified = True

    for paragraph in article.findall('.//p'):
        modified, log_text, content_text, response_text, content, response = process_paragraph(
            PROVIDER, model, paragraph
        )
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


def process_xml_file(PROVIDER, model, INPUT_FILE: str, checkpoint_file, output_file, start_article=0) -> ET.Element:
    """
    Main function to process the XML file.

    Args:
    file_path (str): Path to the input XML file.
    model: The AI model used for content generation.
    checkpoint_file (str): Path to the checkpoint file.
    output_file (str): Path to the output XML file.
    start_article (int): The index of the article to start processing from.

    Returns:
    ET.Element: The root element of the processed XML tree.
    """
    print(f"Processing XML file: {INPUT_FILE}")
    parser = ET.XMLParser(encoding="utf-8")
    tree = ET.parse(INPUT_FILE, parser=parser)
    root = tree.getroot()
    processed_articles = load_checkpoint(checkpoint_file)
    articles = root.findall('.//article')

    for idx, article in enumerate(articles[start_article:], start=start_article + 1):
        print(f"Article Nr.: {idx}")
        if process_article(PROVIDER, model, article, processed_articles, checkpoint_file):
            remove_redundant_p_tags(root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            print(f"XML file has been updated: {output_file}")
    print(f"XML file has been processed successfully: {INPUT_FILE}")
    return root
