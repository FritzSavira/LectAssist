import pandas as pd
import json
import os
import sys
from datetime import datetime

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
    df['id-content'] = df['id'] + ' ' + df['content'].str[:50]
    return df


def filter_dataframe(df, excluded_status, excluded_messages):
    """Filter DataFrame based on excluded status and messages."""
    return df[~df['status'].isin(excluded_status) & ~df['message'].isin(excluded_messages)]


def analyze_message_short(df):
    """Analyze and print message_short statistics."""
    message_short_counts = df['message_short'].value_counts()
    print("\nNumber of entries per Message Short (filtered):")
    print(message_short_counts)


def analyze_id_content(df):
    """Analyze and print id-content statistics."""
    id_content_counts = df['id-content'].value_counts()
    id_content_freq = id_content_counts.reset_index()
    id_content_freq.columns = ['id-content', 'Frequency']
    id_content_freq_filtered = id_content_freq[id_content_freq['Frequency'] > 1]

    print("\nFrequency of 'id-content' values (only Frequency > 1):")
    print(id_content_freq_filtered.to_string(index=False))


def analyze_frequency_distribution(df):
    """Analyze and print frequency distribution of id-content."""
    id_content_counts = df['id-content'].value_counts()

    # Get the frequency distribution
    freq_distribution = id_content_counts.value_counts().sort_index()
    total_count = len(df['id-content'].unique())

    # Rename index and values
    freq_distribution = freq_distribution.rename_axis('Frequency').reset_index(name='Count_id-content')

    # Calculate percentages
    freq_distribution['Percent'] = (freq_distribution['Count_id-content'] / total_count) * 100

    # Output the results
    print("\nFrequency distribution of 'id-content' values (with percentages):")
    print(freq_distribution.to_string(index=False))


def main():
    INPUT_FILENAME = 'CalwerFULL_process.log'
    DIRECTORY_PATH = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt/'
    INPUT_FILE = os.path.join(DIRECTORY_PATH, INPUT_FILENAME)

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

            unique_count = df['id-content'].nunique()
            print(f"\nNumber of unique datasets (id-content): {unique_count}")

            excluded_status = ['success']
            excluded_messages = ['Paragraph too short, skipped processing.']
            df_filtered = filter_dataframe(df, excluded_status, excluded_messages)

            analyze_message_short(df_filtered)
            analyze_id_content(df_filtered)
            analyze_frequency_distribution(df_filtered)
        finally:
            sys.stdout = original_stdout  # Reset stdout to original

if __name__ == "__main__":
    main()



