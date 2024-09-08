import os
import logging
import google.generativeai as genai
import argparse

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, 'DEPDBIBLEN-Content.xml')
OUTPUT_TXT_DIR = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt'
PROCESS_LOG_FILE = os.path.join(OUTPUT_TXT_DIR, 'process.log')
FINISHED_DIR = 'C:/Users/Fried/documents/LectorAssistant/erledigt'
CHECKPOINT_FILE = os.path.join(DIRECTORY_PATH, 'checkpoint.json')
OUTPUT_FILE = os.path.join(OUTPUT_TXT_DIR, 'output.xml')

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
    """Configure the Google GenerativeAI API."""
    genai_api_key = os.getenv('GENAI_API_KEY')
    if not genai_api_key:
        raise ValueError("GENAI_API_KEY environment variable not set")
    genai.configure(api_key=genai_api_key)
    print("API key configured successfully.")

def initialize_model():
    """Initialize and return the GenerativeAI model."""
    MODEL_NAME = 'gemini-1.5-pro'
    return genai.GenerativeModel(MODEL_NAME)

def get_processing_mode():
    """Determine the processing mode using command-line arguments."""
    parser = argparse.ArgumentParser(description='Choose processing mode: text or xml')
    parser.add_argument('mode', choices=['text', 'xml'], help='Processing mode')
    args = parser.parse_args()
    return args.mode

def process_files(mode, model):
    """Process files based on the selected mode."""
    if mode == 'text':
        from process_txt import process_text_files
        process_text_files(model, DIRECTORY_PATH, OUTPUT_TXT_DIR, FINISHED_DIR)
    elif mode == 'xml':
        from process_xml import process_xml_file
        process_xml_file(INPUT_FILE, model, OUTPUT_TXT_DIR, FINISHED_DIR, CHECKPOINT_FILE, OUTPUT_FILE)

def main():
    """Main function to run the script."""
    try:
        # Step 1: Set up logging
        configure_logging()
        print("Logging configured.")

        # Step 2: Configure API
        configure_api()

        # Step 3: Initialize the model
        model = initialize_model()
        print("Model initialized.")

        # Step 4: Determine processing mode
        processing_mode = get_processing_mode()
        print(f"Processing mode: {processing_mode}")

        # Step 5: Process files
        process_files(processing_mode, model)

        print("Processing completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("The script will resume from the last checkpoint when restarted.")

if __name__ == "__main__":
    main()