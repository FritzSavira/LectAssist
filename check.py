import tkinter as tk
from tkinter import filedialog, scrolledtext
import json
import nltk
from nltk.tokenize import word_tokenize
import difflib
import re

# Downloaden Sie das notwendige NLTK-Paket (nur einmal notwendig)
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

    def create_widgets(self):
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

        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_record)
        self.save_button.pack()

    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log")])
        if self.file_path:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.records = [json.loads(line.split(' - ', 1)[1]) for line in content.strip().split('\n')]
            self.display_record()

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
        # Tokenisiere den Text, behalte aber Whitespace und Satzzeichen bei
        tokens = []
        words = word_tokenize(text)
        last_end = 0
        for word in words:
            start = text.index(word, last_end)
            if start > last_end:
                tokens.append(text[last_end:start])
            tokens.append(word)
            last_end = start + len(word)
        if last_end < len(text):
            tokens.append(text[last_end:])
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

    def save_record(self):
        if self.records and self.file_path:
            self.records[self.current_index]['response'] = self.right_text.get('1.0', tk.END).strip()
            self.records[self.current_index]['status'] = 'edited'

            # Update the display to show the new status
            self.status_label.config(text=f"Status: edited")

            # Write the updated records back to the file
            with open(self.file_path, 'w', encoding='utf-8') as file:
                for record in self.records:
                    json_str = json.dumps(record)
                    file.write(f"{record['id']} - {json_str}\n")

    def on_scroll(self, *args):
        self.left_text.yview_moveto(args[1])
        self.right_text.yview_moveto(args[1])

if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewer(root)
    root.mainloop()