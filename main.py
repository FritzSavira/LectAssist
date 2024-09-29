import os
import logging
import google.generativeai as genai

# Determine processing mode 'xml' or 'text'
PROCESSING_MODE = 'xml'

# Determine AI provider
PROVIDER ='google'

# Input filename
INPUT_FILENAME = 'CalwerFULL_240928.xml'

# File paths
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/'
FINISHED_PATH = 'C:/Users/Fried/documents/LectorAssistant/erledigt/'
OUTPUT_TXT_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)
CHECKPOINT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_check.json')
OUTPUT_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_out.xml')
PROCESS_LOG_FILE = os.path.join(OUTPUT_TXT_PATH, os.path.splitext(INPUT_FILENAME)[0]+'_process.log')


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
    elif PROVIDER == 'straico':
        pass
    else:
        pass

def initialize_model():
    if PROVIDER == 'google':
        """Initialize and return the GenerativeAI model."""
        model_name = 'gemini-1.5-pro'
        return genai.GenerativeModel(model_name)
    else:
        pass

def process_files(mode, model):
    """Process files based on the selected mode."""
    print(f"Processing mode: {mode}")
    if mode == 'text':
        from process_txt import process_text_files
        process_text_files(model, DIRECTORY_PATH, OUTPUT_TXT_PATH, FINISHED_PATH)
    elif mode == 'xml':
        from process_xml import process_xml_file
        process_xml_file(INPUT_FILE, model, OUTPUT_TXT_PATH, FINISHED_PATH, CHECKPOINT_FILE, OUTPUT_FILE)


def main():
    """Main function to run the script."""
    try:
        # Step 1: Set up logging
        configure_logging()
        print("Logging configured.")

        # Step 2: Configure API
        configure_api()
        print("API key configured successfully.")

        # Step 3: Initialize the model
        model = initialize_model()
        print("Model initialized.")

        # Step 4: Process files
        process_files(PROCESSING_MODE, model)

        print("Processing completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("The script will resume from the last checkpoint when restarted.")


if __name__ == "__main__":
    main()

