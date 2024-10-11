import tkinter as tk
from tkinter import filedialog, scrolledtext
import json
import nltk
from nltk.tokenize import word_tokenize
import difflib
import re

nltk.download('punkt')

class LogViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Log Viewer")
        self.records = []
        self.current_index = 0
        self.file_path = None

        self.create_widgets()
        self.load_file()

        # Hinzufügen der Event-Bindings für die Pfeiltasten
        self.master.bind('<Left>', lambda event: self.prev_record())
        self.master.bind('<Right>', lambda event: self.next_record())

    def create_widgets(self):
        # ID Input Field
        self.id_input_frame = tk.Frame(self.master)
        self.id_input_frame.pack(fill=tk.X)
        self.id_input_label = tk.Label(self.id_input_frame, text="Enter ID:")
        self.id_input_label.pack(side=tk.LEFT)
        self.id_input = tk.Entry(self.id_input_frame)
        self.id_input.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.id_input.bind('<Return>', self.search_id)

        # Info labels
        self.info_frame = tk.Frame(self.master)
        self.info_frame.pack(fill=tk.X)
        self.id_label = tk.Label(self.info_frame, text="ID: ")
        self.id_label.pack(side=tk.LEFT)
        self.status_label = tk.Label(self.info_frame, text="Status: ")
        self.status_label.pack(side=tk.LEFT)
        self.message_label = tk.Label(self.info_frame, text="Message: ")
        self.message_label.pack(side=tk.LEFT)

        # Text fields
        self.text_frame = tk.Frame(self.master)
        self.text_frame.pack(fill=tk.BOTH, expand=True)

        self.left_text = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD)
        self.left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_text = scrolledtext.ScrolledText(self.text_frame, wrap=tk.WORD)
        self.right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Synchronize scrollbars
        self.left_text.vbar.config(command=self.on_scroll)
        self.right_text.vbar.config(command=self.on_scroll)

        # Buttons
        self.button_frame = tk.Frame(self.master)
        self.button_frame.pack(fill=tk.X)

        self.prev_button = tk.Button(self.button_frame, text="Prev Record", command=self.prev_record)
        self.prev_button.pack(side=tk.LEFT)

        self.next_button = tk.Button(self.button_frame, text="Next Record", command=self.next_record)
        self.next_button.pack(side=tk.RIGHT)

        # Error message label
        self.error_label = tk.Label(self.master, text="", fg="red")
        self.error_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log")])
        if self.file_path:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.records = []
                for line in content.strip().split('\n'):
                    try:
                        parts = line.split(' - ', 1)
                        if len(parts) == 2:
                            record = json.loads(parts[1])
                            self.records.append(record)
                    except json.JSONDecodeError:
                        print(f"Fehler beim Parsen der Zeile: {line}")
                    except IndexError:
                        print(f"Ungültiges Zeilenformat: {line}")
            if self.records:
                self.display_record()
            else:
                print("Keine gültigen Datensätze gefunden.")

    def search_id(self, event):
        search_id = self.id_input.get()
        for i, record in enumerate(self.records):
            if record['id'] == search_id:
                self.current_index = i
                self.display_record()
                self.error_label.config(text="")
                return
        self.error_label.config(text="Keine übereinstimmende ID gefunden.")

    def display_record(self):
        if self.records:
            record = self.records[self.current_index]
            self.id_label.config(text=f"ID: {record['id']}")
            self.status_label.config(text=f"Status: {record['status']}")
            self.message_label.config(text=f"Message: {record['message']}")

            self.left_text.delete('1.0', tk.END)
            self.right_text.delete('1.0', tk.END)

            marked_content, marked_response = self.compare_texts(record['content'], record['response'])

            self.insert_colored_text(self.left_text, marked_content, 'red')
            self.insert_colored_text(self.right_text, marked_response, 'green')

    def compare_texts(self, text1, text2):
        tokens1 = self.tokenize_with_whitespace(text1)
        tokens2 = self.tokenize_with_whitespace(text2)

        d = difflib.Differ()
        diff = list(d.compare(tokens1, tokens2))

        marked_text1 = []
        marked_text2 = []

        for token in diff:
            if token.startswith('  '):
                marked_text1.append(token[2:])
                marked_text2.append(token[2:])
            elif token.startswith('- '):
                marked_text1.append(f"[{token[2:]}]")
            elif token.startswith('+ '):
                marked_text2.append(f"[{token[2:]}]")

        return ''.join(marked_text1), ''.join(marked_text2)

    def tokenize_with_whitespace(self, text):
        words = word_tokenize(text)
        tokens = []
        last_end = 0
        for word in words:
            try:
                start = text.index(word, last_end)
                end = start + len(word)
                if start > last_end:
                    tokens.append((' ' * (start - last_end)))
                tokens.append((word))
                last_end = end
            except ValueError:
                # Wenn das Wort nicht gefunden wird, fügen Sie es einfach hinzu
                tokens.append((word))
                last_end += len(word)
        return tokens

    def insert_colored_text(self, text_widget, text, color):
        parts = re.split(r'(\[.*?\])', text)
        for part in parts:
            if part.startswith('[') and part.endswith(']'):
                text_widget.insert(tk.END, part[1:-1], color)
            else:
                text_widget.insert(tk.END, part)
        text_widget.tag_configure('red', foreground='red')
        text_widget.tag_configure('green', foreground='green')

    def prev_record(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_record()

    def next_record(self):
        if self.current_index < len(self.records) - 1:
            self.current_index += 1
            self.display_record()


    def on_scroll(self, *args):
        self.left_text.yview_moveto(args[1])
        self.right_text.yview_moveto(args[1])

if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewer(root)
    root.mainloop()