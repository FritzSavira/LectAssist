import os
import time
import json
import logging
from nltk.tokenize import sent_tokenize
from main import generate_content_with_retries

# Configuration variables
WORDS_PER_CHUNK = 1500


def get_prompt():
    return '''Du bist ein professioneller Lektor und bearbeitest einen Text
    von D. A. Schlatter 'Der Römerbrief' von 1890.
    In dem Text wir manchmal "der Jude" als Synonym für einen Menschen jüdischen 
    Glaubens verwendet.
    Deine Aufgabe: Analysiere die übergebenen Textabschnitte.
    Die Formulierung "der Jude" soll vermieden werden. Formuliere die Textstellen um, die den Begriff "der Jude"
    enthalten. Der Rest des Textes wird nicht geändert.
    Gib ausschließlich den Text zurück. Vermeide jeglichen ergänzenden Kommentar 
    Hier beginnt der Text:'''


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


def process_text_file(PROVIDER, model, INPUT_FILE, directory_path, OUTPUT_FILE):
    print(f"\n=== Processing file: {INPUT_FILE} ===")
    print("Reading file content...")
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
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
            response_text = generate_content_with_retries(PROVIDER, model, chunk, get_prompt())
            if response_text:
                print("chunk: ")
                print(chunk)
                print()
                print("response_text: ")
                print(response_text)
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
            "chunk_id": i + 1,
            "chunk_size": WORDS_PER_CHUNK,
            "status": "error" if error_message else "success",
            "message": error_message,
            "content": chunk,
            "response": response_text
        }
        logging.info(json.dumps(log_entry, ensure_ascii=False))

    # Concatenate responses to one single string.
    responses_str = "\n\n".join(responses)

    # Save response as MD-file
    save_as_md(responses_str, OUTPUT_FILE)

    print(f"=== Processing of {INPUT_FILE} completed ===\n")


