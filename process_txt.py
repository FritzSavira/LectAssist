import os
import time
import logging
import json
import shutil
import nltk
from nltk.tokenize import sent_tokenize
from requests.exceptions import ConnectionError

# Configuration variables
WORDS_PER_CHUNK = 1500


def setup_environment(output_txt_dir, finished_dir):
    print("=== Initializing the environment ===")
    print(f"Number of words per section for processing: {WORDS_PER_CHUNK}")

    print("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt')
    print("NLTK punkt tokenizer downloaded.")

    print("Checking output directories...")
    os.makedirs(output_txt_dir, exist_ok=True)
    os.makedirs(finished_dir, exist_ok=True)
    print("Output directories checked/created.")
    print("=== Initialization completed ===\n")


def split_text(text, words_per_chunk):
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


def save_as_md(text, filename):
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
        except Exception as e:
            print(f"An error occurred in generate_content(): {e}")
            return str(e)


def process_file(filename, model, prompt, directory_path, output_txt_dir, finished_dir):
    print(f"\n=== Processing file: {filename} ===")
    file_path = os.path.join(directory_path, filename)

    print("Reading file content...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print("File content read.")

    text_chunks = split_text(content, WORDS_PER_CHUNK)
    print(f"Text split into {len(text_chunks)} sections.")

    responses = []
    for i, chunk in enumerate(text_chunks):
        error_message = ""
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
        log_entry = {
            "section": i + 1,
            "status": "error" if error_message else "success",
            "error_message": error_message,
            "chunk": chunk,
            "response": response.text if hasattr(response, 'text') else str(response),
        }
        logging.info(json.dumps(log_entry, ensure_ascii=False))

    base_filename = os.path.splitext(filename)[0]
    full_response = f"## {base_filename}\n\n" + " ".join(responses)

    md_filename = os.path.join(output_txt_dir, f'{base_filename}_bearbeitet.md')
    save_as_md(full_response, md_filename)

    print(f"Moving processed file to {finished_dir}...")
    shutil.move(file_path, os.path.join(finished_dir, filename))
    print(f"Processed file moved to {finished_dir}.")
    print(f"=== Processing of {filename} completed ===\n")


def process_text_files(model, directory_path, output_txt_dir, finished_dir):
    setup_environment(output_txt_dir, finished_dir)

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

    print(f"Searching for .txt files in {directory_path}...")
    valid_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
    print(f"{len(valid_files)} valid files found.")

    for i, filename in enumerate(valid_files):
        print(f"\nProcessing file {i + 1}/{len(valid_files)}: {filename}")
        process_file(filename, model, prompt, directory_path, output_txt_dir, finished_dir)

    print("=== Script has processed all files ===")


if __name__ == "__main__":
    # This block is for testing purposes only
    from main import initialize_model
    model = initialize_model()
    process_text_files(model)
