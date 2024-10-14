import sys
import os
import logging
import google.generativeai as genai
from openai import OpenAI

# Determine processing mode 'text' or 'xml_paragraph' or 'xml_article'
PROCESSING_MODE = 'xml_article'

# Determine AI provider 'openai' or 'google'
PROVIDER = 'openai'

# Input filename
INPUT_FILENAME = 'CalwerFULL_241011_B_mit_Ueb.xml'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/Documents/LectorAssistant/'
FINISHED_PATH = 'C:/Users/Fried/documents/LectorAssistant/erledigt/'
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
CHECKPOINT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_check.json')
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_out.xml')
PROCESS_LOG_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_process.log')
ERROR_LOG_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_error.log')


def configure_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        filename=PROCESS_LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )


def configure_api():
    if PROVIDER == 'google':
        """Configure the Google GenerativeAI API."""
        genai_api_key = os.getenv('GENAI_API_KEY')
        if not genai_api_key:
            raise ValueError("GENAI_API_KEY environment variable not set")
        genai.configure(api_key=genai_api_key)
        """Initialize and return the GenerativeAI model."""
        model_name = 'gemini-1.5-pro'
        return genai.GenerativeModel(model_name)
    elif PROVIDER == 'openai':
        model_name = 'gpt-4o'
        return model_name
    else:
        pass

def call_ai(PROVIDER, model, prompt, chunk):
    if PROVIDER == 'google':
        response = model.generate_content(prompt + chunk).text
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
        response = completion.choices[0].message.content
    return response

def process_files(mode, model):
    """Process files based on the selected mode."""
    print(f"Processing mode: {mode}")
    if mode == 'text':
        from process_txt import process_text_file
        process_text_file(PROVIDER, model, INPUT_FILE, DIRECTORY_PATH, OUTPUT_FILE)
    elif mode == 'xml_paragraph':
        from process_xml_paragraph import process_xml_file
        process_xml_file(PROVIDER, model, INPUT_FILE, CHECKPOINT_FILE, OUTPUT_FILE)
    elif mode == 'xml_article':
        from process_xml_article import process_xml_file
        process_xml_file(PROVIDER, model, INPUT_FILE, CHECKPOINT_FILE, OUTPUT_FILE)
    else:
        print("No valid processing mode available. Select available processing mode")


def main():
    """Main function to run the script."""
    try:
        # Step 0: Sicherheitsabfrage
        check = input("Hast du bei erneutem Durchlauf die _out.xml Datei eingefügt? (ja / nein)")
        if check != "ja":
            sys.exit()

        # Step 1: Set up logging
        configure_logging()
        print("Logging configured.")

        # Step 2: Configure API
        model = configure_api()
        print("API configured successfully.")

        # Step 3: Initialize the model
#        model = initialize_model()
#        print("Model initialized.")

        # Step 4: Process files
        process_files(PROCESSING_MODE, model)
        print("Processing completed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("The script will resume from the last checkpoint when restarted.")


if __name__ == "__main__":
    main()
