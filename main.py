import os
import time
import shutil
import nltk
import google.generativeai as genai
from nltk.tokenize import sent_tokenize
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from lxml import etree


# Configuration variables
WORDS_PER_CHUNK = 1500
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/'
OUTPUT_TXT_DIR = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt'
FINISHED_DIR = 'C:/Users/Fried/documents/LectorAssistant/erledigt'
MODEL_NAME = 'gemini-1.5-pro'


def setup_environment():
    # Initializes the environment for script execution.
    print("=== Initializing the environment ===")
    print(f"Number of words per section for processing: {WORDS_PER_CHUNK}")

    print("Configuring API key...")
    genai_api_key = os.getenv('GENAI_API_KEY')
    genai.configure(api_key=genai_api_key)
    print("API key configured.")

    print("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt')
    print("NLTK punkt tokenizer downloaded.")

    print("Checking output directories...")
    os.makedirs(OUTPUT_TXT_DIR, exist_ok=True)
    os.makedirs(FINISHED_DIR, exist_ok=True)
    print("Output directories checked/created.")
    print("=== Initialization completed ===\n")


def split_text(text, words_per_chunk):
    # Splits the text into sections with a specific word count.
    print(f"Splitting text into sections with {words_per_chunk} words each...")
    sentences = sent_tokenize(text)
    chunks, current_chunk, current_word_count = [], [], 0

    for sentence in sentences:
        words = sentence.split()
        if current_word_count + len(words) > words_per_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk, current_word_count = words, len(words)
        else:
            current_chunk.extend(words)
            current_word_count += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    print(f"Text split into {len(chunks)} sections.")
    return chunks

def preprocess_xml(xml_text):
    # Entferne BOM, falls vorhanden
    xml_text = xml_text.lstrip('\ufeff')
    # Entferne Leerzeichen am Anfang
    xml_text = xml_text.lstrip()
    # Entferne XML-Deklaration, falls vorhanden
    if xml_text.startswith('<?xml'):
        xml_text = xml_text[xml_text.find('?>')+2:].lstrip()
    return xml_text


def split_xhtml_text(xhtml_text, words_per_chunk):
    print(f"Splitting XHTML/XML text into sections with approximately {words_per_chunk} words each...")

    # Versuche zuerst das Dokument als XML zu parsen
    try:
        parser = etree.XMLParser(recover=True)
        xhtml_text = preprocess_xml(xhtml_text)
        root = etree.XML(xhtml_text, parser)
        is_xml = True
    except etree.XMLSyntaxError:
        # Wenn XML-Parsing fehlschlägt, behandle es als HTML/XHTML
        soup = BeautifulSoup(xhtml_text, 'html.parser')
        is_xml = False

    chunks = []
    current_chunk = []
    current_word_count = 0

    def process_text(text):
        nonlocal current_chunk, current_word_count
        if text and text.strip():
            words = text.split()
            if current_word_count + len(words) > words_per_chunk:
                if current_chunk:
                    chunks.append(''.join(map(str, current_chunk)))
                current_chunk = []
                current_word_count = 0

            current_chunk.append(text)
            current_word_count += len(words)

    def process_element(element):
        nonlocal current_chunk, current_word_count

        # Füge öffnendes Tag hinzu
        current_chunk.append(f"<{element.tag}")
        for name, value in element.attrib.items():
            current_chunk.append(f' {name}="{value}"')
        current_chunk.append(">")

        if element.text:
            process_text(element.text)

        for child in element:
            process_element(child)
            if child.tail:
                process_text(child.tail)

        # Füge schließendes Tag hinzu
        current_chunk.append(f"</{element.tag}>")

        # Prüfe, ob wir einen neuen Chunk beginnen sollten
        if current_word_count >= words_per_chunk:
            chunks.append(''.join(map(str, current_chunk)))
            current_chunk = []
            current_word_count = 0

    if is_xml:
        process_element(root)
    else:
        for element in soup.descendants:
            if isinstance(element, str):
                process_text(element)
            else:
                current_chunk.append(str(element))
                if current_word_count >= words_per_chunk and element.name not in ['br', 'img', 'hr']:
                    chunks.append(''.join(map(str, current_chunk)))
                    current_chunk = []
                    current_word_count = 0

    if current_chunk:
        chunks.append(''.join(map(str, current_chunk)))

    print(f"XHTML/XML text split into {len(chunks)} sections.")
    return chunks


def save_as_md(text, filename):
    # Saves text as a Markdown file with an incrementing index.
    print(f"Saving Markdown file: {filename}")
    if not filename.endswith('.md'):
        filename += '.md'

    base_filename, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(new_filename):
        new_filename = f"{base_filename}({counter}){ext}"
        counter += 1

    with open(new_filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Response saved as Markdown file under: {new_filename}")


def generate_content_with_retries(model, prompt, chunk, retries=5, backoff_factor=0.3):
    # Generates content with retry attempts on connection errors.
    for attempt in range(retries):
        try:
            print(f"Attempting content generation (Attempt {attempt + 1}/{retries})...")
            return model.generate_content(prompt + chunk)
        except ConnectionError as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                print(f"Connection error. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Maximum number of attempts reached. Connection not possible.")
                raise e


def process_file(filename, model, prompt):
    print(f"\n=== Processing file: {filename} ===")
    file_path = os.path.join(DIRECTORY_PATH, filename)

    print("Reading file content...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print("File content read.")

    # Determine file type and split accordingly
    file_extension = os.path.splitext(filename)[1].lower()
    if file_extension == '.txt':
        text_chunks = split_text(content, WORDS_PER_CHUNK)
    elif file_extension in ['.xml', '.xhtml', '.html']:
        text_chunks = split_xhtml_text(content, WORDS_PER_CHUNK)
    else:
        print(f"Unsupported file type: {file_extension}")
        return

    print(f"Text split into {len(text_chunks)} sections.")

    responses = []
    for i, chunk in enumerate(text_chunks):
        print(f"Generating response for section {i + 1}/{len(text_chunks)}...")
        try:
            time.sleep(1)
            response = generate_content_with_retries(model, prompt, chunk)
            if response.parts:
                responses.append(response.text)
                print(f"Response generated for section {i + 1}.")
            else:
                error_message = f"!!! Section {i + 1} did not return valid parts."
                print(error_message)
                responses.append(error_message)
        except ValueError as e:
            error_message = f"!!! Error processing section {i + 1}: {e}"
            print(error_message)
            responses.append(error_message)

    base_filename = os.path.splitext(filename)[0]
    full_response = f"## {base_filename}\n\n" + " ".join(responses)

    # Save the processed content
    if file_extension in ['.xml', '.xhtml', '.html']:
        # For XHTML files, we need to insert the processed content back into the original structure
        soup = BeautifulSoup(content, 'html.parser')
        body = soup.find('body')
        if body:
            body.clear()
            body.append(BeautifulSoup(full_response, 'html.parser'))

        output_filename = os.path.join(OUTPUT_TXT_DIR, f'{base_filename}_bearbeitet{file_extension}')
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    else:
        # For TXT files, save as markdown
        md_filename = os.path.join(OUTPUT_TXT_DIR, f'{base_filename}_bearbeitet.md')
        save_as_md(full_response, md_filename)

    print(f"Moving processed file to {FINISHED_DIR}...")
    shutil.move(file_path, os.path.join(FINISHED_DIR, filename))
    print(f"Processed file moved to {FINISHED_DIR}.")
    print(f"=== Processing of {filename} completed ===\n")


def main():
    print("=== Starting main program ===")
    setup_environment()

    print("Initializing generative model...")
    model = genai.GenerativeModel(MODEL_NAME)
    print("Generative model initialized.")

    # Detailed instructions for the AI on text editing
    prompt = '''Du bist ein professioneller Lektor und lektorierst das hochgeladene Transkript einer frei gesprochenen
        Predigt. Deine Aufgabe ist es, das folgende Transkript in einen gut lesbaren Text zu überarbeiten,
        ohne formell zu werden. Folgende Schritte sind dabei zu beachten:

        1. Textinhalt und Stil:
        - Formuliere den Text in gut lesbares Schriftdeutsch um.
        – Stelle Wörter im Satz um, wenn es die Regeln für Schriftdeutsch erfordern.
        - Entferne Füllwörter und doppelte Aussagen, die direkt aufeinanderfolgen
          (z.B. kommt es häufig vor, dass der Sprecher ein oder zwei Worte wiederholt).
        - Die Bedeutung der Aussagen soll erhalten bleiben,
          sprachliche Wiederholungen innerhalb eines Satzes dürfen gekürzt werden.
        – Englische Ausdrücke (z.B. "crazy" oder "so goes it not") behalte bei.
        - Formuliere Sätze grammatikalisch korrekt. Vervollständige, wenn nötig, unvollständige Sätze.

        2. Formatierung:
        - Formatiere Bibelstellen-Angaben ins Standard-Format (z.B. Römer 8 Vers 28 bis 31 soll Römer 8,28–31 heißen).
        - Markiere verschiedene Sprecher mit SPK_1 und SPK_2 usw., wobei du bei erkennbaren Namen diese einfügst
          (z.B. wenn SPK_1 einen Sprecher mit Namen anspricht, wird der nächste SPK wohl so heißen.
          Du findest Sprecherangaben z.T. auch im Titel)
        - Strukturiere den Text in Absätze, um ein lesefreundliches Layout zu gewährleisten.
        – Achte auf eine richtige Kommasetzung vor "und".
        - Füge Zwischenüberschriften ein, die die Aussage des Absatzes zusammenfassen.
          Verwende vor allem nominalisierte Phrasen. Jede Zeile mit Überschrift beginnt mit "###".
          Nach maximal 15 Sätzen folgt ein Zeilenumbruch.
        - Verwende das deutsche System von Anführungszeichen („ ").
        - Vermeide drei folgende Punkte "..." im Text.
        Hier beginnt der Text des Transkripts:'''

    print(f"Searching for .txt and .xml/.xhtml/.html files in {DIRECTORY_PATH}...")
    valid_files = [f for f in os.listdir(DIRECTORY_PATH) if f.endswith(('.txt', '.xml', '.xhtml', '.html'))]
    print(f"{len(valid_files)} valid files found.")

    for i, filename in enumerate(valid_files):
        print(f"\nProcessing file {i + 1}/{len(valid_files)}: {filename}")
        process_file(filename, model, prompt)

    print("=== Script has processed all files ===")


if __name__ == "__main__":
    main()
