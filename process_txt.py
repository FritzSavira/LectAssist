import os
import time
import json
import shutil
import logging
import nltk
from nltk.tokenize import sent_tokenize
from requests.exceptions import ConnectionError

# Configuration variables
WORDS_PER_CHUNK = 2000


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
        response_text = ""
        print(f"Generating response for section {i + 1}/{len(text_chunks)}...")
        try:
            time.sleep(1)
            response = generate_content_with_retries(model, prompt, chunk)
            if response.parts:
                response_text = response.text
                responses.append(response_text)
                print(f"Response generated for section {i + 1}.")
            else:
                error_message = f"!!! Section {i + 1} did not return valid parts."
                print(error_message)
                responses.append(error_message)
        except AttributeError:
            error_message = f"!!! AttributeError: Response object has no 'parts' attribute in section {i + 1}."
            print(error_message)
            responses.append(error_message)
        except ValueError as e:
            error_message = f"!!! Error processing section {i + 1}: {e}"
            print(error_message)
            responses.append(error_message)
        except Exception as e:
            error_message = f"!!! Unexpected error in section {i + 1}: {e}"
            print(error_message)
            responses.append(error_message)

        # Logging
        log_entry = {
            "id": i + 1,
            "status": "error" if error_message else "success",
            "message": error_message,
            "content": chunk,
            "response": response_text or str(response),
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

    prompt = '''Du bist ein professioneller Übersetzer und übersetzt christliche Bücher aus
        der englischen in die deutsche Sprache.
        Deine Aufgabe ist es, den folgenden Abschnitt des Buches Sovereign Grace von Dwight L. Moody
        in die deutsche Sprache zu übersetzen.

        1. Textinhalt und Stil:       
        - Übersetze sehr nah am englischen Text.
        - Der Ausdruck und sprachliche Stil des ursprünglichen Textes muss erhalten bleiben.
        - Die ursprüngliche semantische Bedeutung der Aussagen muss erhalten bleiben.


        2. Formatierung:
        - Formatiere Bibelstellen-Angaben ins Standard-Format (z.B. Römer 8 Vers 28 bis 31 soll Römer 8,28–31 heißen).
        - Vorhandene Überschriften bleiben erhalten. 
        - Strukturiere den Text in Absätze, um ein lesefreundliches Layout zu gewährleisten.
        Hier beginnt der Text:'''

    print(f"Searching for .txt files in {directory_path}...")
    valid_files = [f for f in os.listdir(directory_path) if f.endswith('.txt')]
    print(f"{len(valid_files)} valid files found.")

    for i, filename in enumerate(valid_files):
        print(f"\nProcessing file {i + 1}/{len(valid_files)}: {filename}")
        process_file(filename, model, prompt, directory_path, output_txt_dir, finished_dir)

    print("=== Script has processed all files ===")
