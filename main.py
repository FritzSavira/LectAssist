import os
import logging
import google.generativeai as genai

DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, 'DEPDBIBLEN-Content.xml')
OUTPUT_TXT_DIR = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt'
PROCESS_LOG_FILE = os.path.join(OUTPUT_TXT_DIR, 'process.log')

def configure_logging():
    logging.basicConfig(
        filename=PROCESS_LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )

def configure_api():
    genai_api_key = os.getenv('GENAI_API_KEY')
    if not genai_api_key:
        raise ValueError("GENAI_API_KEY environment variable not set")
    genai.configure(api_key=genai_api_key)
    print("API key configured.")

def initialize_model():
    MODEL_NAME = 'gemini-1.5-pro'
    return genai.GenerativeModel(MODEL_NAME)

def determine_processing_mode():
    # This function should be implemented to determine the processing mode
    # based on user input or command line arguments
    processing_mode = "text"
    #processing_mode = "xml"
    return processing_mode
    pass

def main():
    try:
        configure_logging()
        configure_api()
        model = initialize_model()

        processing_mode = determine_processing_mode()

        if processing_mode == 'text':
            from process_txt import process_text_files
            process_text_files(model)
        elif processing_mode == 'xml':
            from process_xml import process_xml_file
            process_xml_file(INPUT_FILE, model)

        print("Processing completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("The script will resume from the last checkpoint when restarted.")

if __name__ == "__main__":
    main()