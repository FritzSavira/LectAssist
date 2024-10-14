'''Wertet die .log-Datei statistisch aus und schreibt das Ergebnis in eine .txt-Datei.'''

import pandas as pd
import json
import os
import sys
from datetime import datetime

INPUT_FILENAME = 'CalwerFULL_process.log'
DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)


def load_data(file_path):
    """Load data from log file and return a list of parsed entries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                try:
                    timestamp, json_text = line.split(' - ', 1)
                    entry = json.loads(json_text)
                    entry['timestamp'] = timestamp
                    data.append(entry)
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"Error processing line: {line}\n{e}")
    return data


def extract_message_short(message):
    """Extract short message from full message."""
    colon_indices = [pos for pos, char in enumerate(message) if char == ':']
    return message[:colon_indices[1] + 1] if len(colon_indices) >= 2 else message


def create_dataframe(data):
    """Create and preprocess DataFrame from loaded data."""
    df = pd.DataFrame(data)
    df['message_short'] = df['message'].apply(extract_message_short)
    df['message_short'] = df['message_short'].str.encode('ascii', errors='ignore').str.decode('ascii')
    df['id-content'] = df['id'] + '|' + df['content'].str[:50]
    df['id-content-message'] = df['id-content'] + ' | ' + df['message_short']

    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Sort the dataframe by 'id-content' and 'timestamp'
    df = df.sort_values(['id-content', 'timestamp'])

    # Create the 'latest' column
    df['latest'] = df.groupby('id-content')['timestamp'].transform('max') == df['timestamp']
    return df


def filter_dataframe(df, excluded_status, excluded_messages):
    """Filter DataFrame based on excluded status, messages, and latest flag."""
    return df[
        (~df['status'].isin(excluded_status)) &
        (~df['message'].isin(excluded_messages)) &
        (df['latest'] == True)
    ]


def main():
    # Get today's date in YYMMDD format
    today_date = datetime.now().strftime('_%y%m%d')
    base_output_filename = f'CalwerFullStat{today_date}.txt'
    OUTPUT_FILE = os.path.join(DIRECTORY_PATH, base_output_filename)

    # Check if the file already exists and append a counter if it does
    counter = 1
    while os.path.exists(OUTPUT_FILE):
        OUTPUT_FILENAME = f'CalwerFullStat{today_date}({counter}).txt'
        OUTPUT_FILE = os.path.join(DIRECTORY_PATH, OUTPUT_FILENAME)
        counter += 1

    # Open the output file and redirect stdout
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # Create a class to duplicate stdout writes
        class MultiWriter:
            def __init__(self, *writers):
                self.writers = writers
            def write(self, data):
                for w in self.writers:
                    w.write(data)
            def flush(self):
                for w in self.writers:
                    w.flush()

        original_stdout = sys.stdout  # Save a reference to the original standard output
        sys.stdout = MultiWriter(sys.stdout, f)  # Redirect stdout to both console and file

        try:
            data = load_data(INPUT_FILE)
            df = create_dataframe(data)

            excluded_status = ['success']
            excluded_messages = ['Paragraph too short, skipped processing.']
            df_filtered = filter_dataframe(df, excluded_status, excluded_messages)

            # Determine the unique messages in 'message_short' in df_filtered
            unique_messages = df_filtered['message_short'].unique()
            num_unique_messages = len(unique_messages)
            print(f"\nNumber of unique messages in 'message_short': {num_unique_messages}")

            # Get the counts of each unique message
            message_counts = df_filtered['message_short'].value_counts()

            # Print the unique messages and their counts
            print("\nUnique messages and their counts:")
            for message, count in message_counts.items():
                print(f"'{message}': {count}")

            # Determine the unique ids in 'id' in d_filtered
            unique_ids = df_filtered['id'].unique()
            num_unique_ids = len(unique_ids)
            print(f"\nNumber of unique IDs in 'ID': {num_unique_ids}")

            # Print the 'id-content-message' entries from df_filtered
            print("\nDatensätze von df_filtered['id-content-message']:")
            for entry in df_filtered['id-content-message']:
                print(entry)

        finally:
            sys.stdout = original_stdout  # Reset stdout to original

if __name__ == "__main__":
    main()
