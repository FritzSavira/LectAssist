import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox
import json
import re
import os

OUTPUT_TXT_DIR = 'C:/Users/Fried/documents/LectorAssistant/bearbeitet_txt'
PROCESSED_LOG_FILE = os.path.join(OUTPUT_TXT_DIR, 'process.log')


def highlight_word_differences(content_text, response_text):
    content_words = content_text.get("1.0", tk.END).split()
    response_words = response_text.get("1.0", tk.END).split()

    # Configure tags for both text widgets
    content_text.tag_configure("highlight_missing", foreground="red", font=tkfont.Font(weight="bold"))
    response_text.tag_configure("highlight_added", foreground="green", font=tkfont.Font(weight="bold"))

    # Clear previous highlights
    content_text.tag_remove("highlight_missing", "1.0", tk.END)
    response_text.tag_remove("highlight_added", "1.0", tk.END)

    # Highlight missing words in content_text
    for word in content_words:
        if word not in response_words:
            start = "1.0"
            while True:
                start = content_text.search(word, start, tk.END)
                if not start:
                    break
                end = f"{start}+{len(word)}c"
                content_text.tag_add("highlight_missing", start, end)
                start = end

    # Highlight added words in response_text
    for word in response_words:
        if word not in content_words:
            start = "1.0"
            while True:
                start = response_text.search(word, start, tk.END)
                if not start:
                    break
                end = f"{start}+{len(word)}c"
                response_text.tag_add("highlight_added", start, end)
                start = end



def insert_line_breaks(text):
    return re.sub(r'([.!?])\s+', r'\1\n', text)


def create_widgets(root):
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Create a Font object
    text_font = tkfont.Font(size=11)

    # Text fields for content_text and response_text
    content_text = tk.Text(main_frame, height=10, width=50, font=text_font)
    content_text.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

    response_frame = tk.Frame(main_frame)
    response_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

    response_text = tk.Text(response_frame, height=10, width=50, font=text_font)
    response_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add scrollbar to response_text
    response_scrollbar = tk.Scrollbar(response_frame, orient=tk.VERTICAL, command=response_text.yview)
    response_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    response_text.config(yscrollcommand=response_scrollbar.set)

    # Synchronize scrolling
    def sync_scroll(*args):
        content_text.yview_moveto(args[0])
    response_text.config(yscrollcommand=lambda *args: [response_scrollbar.set(*args), sync_scroll(*args)])

    # Add article_id label
    article_id_label = tk.Label(main_frame, text="Article ID: ")
    article_id_label.grid(row=1, column=0, columnspan=2, pady=5)

    # Status selection
    status_var = tk.StringVar(value="open")
    status_open = tk.Radiobutton(main_frame, text="Open", variable=status_var, value="open")
    status_final = tk.Radiobutton(main_frame, text="Final", variable=status_var, value="final")
    status_open.grid(row=2, column=0, pady=5)
    status_final.grid(row=2, column=1, pady=5)


    # Buttons for file operations
    load_button = tk.Button(main_frame, text="Load Log",
                            command=lambda: load_log(content_text, response_text, status_var))
    load_button.grid(row=3, column=0, pady=5)

    save_button = tk.Button(main_frame, text="Save Changes",
                            command=lambda: save_changes(content_text, response_text, status_var))
    save_button.grid(row=3, column=1, pady=5)

    prev_button = tk.Button(main_frame, text="Previous Entry",
                            command=lambda: prev_entry(content_text, response_text, status_var))
    prev_button.grid(row=4, column=0, pady=5)

    next_button = tk.Button(main_frame, text="Next Entry",
                            command=lambda: next_entry(content_text, response_text, status_var))
    next_button.grid(row=4, column=1, pady=5)

    save_log_button = tk.Button(main_frame, text="Save Log File",
                                command=save_log_file)
    save_log_button.grid(row=5, column=0, columnspan=2, pady=5)

    # Configure grid weights
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)

    return content_text, response_text, status_var, article_id_label



current_entry = None
all_entries = []


def load_log(content_text, response_text, status_var, article_id_label):
    global current_entry, all_entries
    file_path = PROCESSED_LOG_FILE
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                all_entries = re.findall(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ({.*})', content)
                if all_entries:
                    current_entry = 0
                    display_current_entry(content_text, response_text, status_var, article_id_label)
                else:
                    messagebox.showerror("Error", "No valid entries found in the log file")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {str(e)}")


def display_current_entry(content_text, response_text, status_var, article_id_label):
    global current_entry, all_entries
    if current_entry is not None and 0 <= current_entry < len(all_entries):
        timestamp, json_str = all_entries[current_entry]
        try:
            data = json.loads(json_str)
            content_text.delete(1.0, tk.END)
            content_text.insert(tk.END, insert_line_breaks(data.get('content_text', '')))
            response_text.delete(1.0, tk.END)
            response_text.insert(tk.END, insert_line_breaks(data.get('response_text', '')))
            status_var.set(data.get('Status', 'open'))

            # Display article_id
            #article_id = data.get('article_id', 'N/A')
            #article_id_label.config(text=f"Article ID: {article_id}")

            # Display article_id and log_text
            article_id = data.get('article_id', 'N/A')
            log_text = data.get('log_text', 'No log text available')
            article_id_label.config(text=f"Article ID: {article_id}\nLog Text: {log_text}")

            # Highlight word differences
            highlight_word_differences(content_text, response_text)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON in log entry")

def save_changes(content_text, response_text, status_var):
    global current_entry, all_entries
    if current_entry is not None and 0 <= current_entry < len(all_entries):
        timestamp, json_str = all_entries[current_entry]
        try:
            data = json.loads(json_str)
            # Remove line breaks that were added for display
            data['response_text'] = re.sub(r'\n(?=[^.!?])', ' ', response_text.get(1.0, tk.END).strip())
            data['Status'] = status_var.get()
            all_entries[current_entry] = (timestamp, json.dumps(data))
            messagebox.showinfo("Saved", "Changes saved for current entry")

            # Highlight word differences after saving changes
            highlight_word_differences(content_text, response_text)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON in log entry")



def save_log_file():
    global all_entries
    if not all_entries:
        messagebox.showerror("Error", "No log entries to save")
        return

    original_file = filedialog.askopenfilename(filetypes=[("Log files", "*.log")])
    if not original_file:
        return

    new_file = original_file.rsplit('.', 1)[0] + "_final.log"

    try:
        with open(new_file, 'w', encoding='utf-8') as file:
            for timestamp, json_str in all_entries:
                file.write(f"{timestamp} - {json_str}\n")
        messagebox.showinfo("Success", f"Log file saved as {new_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save file: {str(e)}")


def next_entry(content_text, response_text, status_var, article_id_label):
    global current_entry
    if current_entry is not None and current_entry < len(all_entries) - 1:
        current_entry += 1
        display_current_entry(content_text, response_text, status_var, article_id_label)


def prev_entry(content_text, response_text, status_var, article_id_label):
    global current_entry
    if current_entry is not None and current_entry > 0:
        current_entry -= 1
        display_current_entry(content_text, response_text, status_var, article_id_label)


def main():
    root = tk.Tk()
    root.title("Log Editor")
    root.geometry("1000x800")  # Increased height to accommodate the new label

    content_text, response_text, status_var, article_id_label = create_widgets(root)

    # Update function calls to include article_id_label
    load_button = root.nametowidget('.!frame.!button')
    load_button.config(command=lambda: load_log(content_text, response_text, status_var, article_id_label))

    prev_button = root.nametowidget('.!frame.!button3')
    prev_button.config(command=lambda: prev_entry(content_text, response_text, status_var, article_id_label))

    next_button = root.nametowidget('.!frame.!button4')
    next_button.config(command=lambda: next_entry(content_text, response_text, status_var, article_id_label))

    root.mainloop()


if __name__ == "__main__":
    main()