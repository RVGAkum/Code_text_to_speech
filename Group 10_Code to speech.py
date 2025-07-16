import tkinter as tk
from tkinter import filedialog, messagebox
import pyttsx3
import ast
import traceback
import re
import time
import requests

# Text-to-speech class  
class CodeSpeaker:
    def __init__(self, voice_index=0):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.set_voice(voice_index)
        self.engine.setProperty('rate', 150)

    def set_voice(self, index):
        self.engine.setProperty('voice', self.voices[index].id)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def save_to_mp3(self, text, filename="spoken_output.mp3"):
        self.engine.save_to_file(text, filename)
        self.engine.runAndWait()

# AI Interpreter
class CodeInterpreter:
    def __init__(self):
        self.api_key = "56c96cfddb627aa0e20f38776631b6ed07ecb9cad9f1ea2d57a619fbf4f0d4b0"
        self.endpoint = "https://api.together.xyz/v1/chat/completions"
        self.model = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    def explain_code(self, code):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": f"Explain this Python code simply:\n\n{code}"}
            ],
            "temperature": 0.5,
            "max_tokens": 500
        }

        try:
            response = requests.post(self.endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception:
            return "Oops! Check your network connection"

# GUI Application
class CodeReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Code to Speech Reader")
        self.root.configure(bg="#1e1e1e")
        self.speaker = CodeSpeaker()
        self.interpreter = CodeInterpreter()
        self.last_debug_output = ""

        self.setup_gui()

    def setup_gui(self):
        label = tk.Label(self.root, text="Paste your Python code below:", font=('Arial', 14), bg="#1e1e1e", fg="white")
        label.pack()

        self.code_text = tk.Text(self.root, height=20, width=80, font=('Courier', 12), bg="#2d2d2d", fg="white", insertbackground="white")
        self.code_text.pack(pady=10)

        # Voice selector
        self.voice_var = tk.StringVar(self.root)
        self.voice_options = [v.name for v in self.speaker.engine.getProperty('voices')]
        self.voice_menu = tk.OptionMenu(self.root, self.voice_var, *self.voice_options, command=self.change_voice)
        self.voice_var.set(self.voice_options[0])
        self.voice_menu.configure(bg="#3a3a3a", fg="white", font=('Arial', 10))
        self.voice_menu.pack(pady=5)

        # Buttons
        button_style = {'bg': '#444', 'fg': 'white', 'font': ('Arial', 10), 'width': 20}
        tk.Button(self.root, text="Load Python File", command=self.load_file, **button_style).pack(pady=2)
        tk.Button(self.root, text="Read & Explain Code", command=self.read_code, **button_style).pack(pady=2)
        tk.Button(self.root, text="Save Audio", command=self.save_audio, **button_style).pack(pady=2)
        tk.Button(self.root, text="Debug Code", command=self.debug_code, **button_style).pack(pady=2)
        tk.Button(self.root, text="Save Debug Report", command=self.save_debug_report, **button_style).pack(pady=2)
        

    def change_voice(self, selected_voice_name):
        index = self.voice_options.index(selected_voice_name)
        self.speaker.set_voice(index)

    def read_code(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            self.speaker.speak("Please enter your Python code.")
            return

        explanation = self.interpreter.explain_code(code)
        time.sleep(0.5)
        self.speaker.speak("Here's the explanation.")
        self.speaker.speak(explanation)

    def debug_code(self):
        code = self.code_text.get("1.0", tk.END)
        self.speaker.speak("Starting debug process.")
        try:
            exec(code, {})
            self.speaker.speak("Code ran successfully. No errors found.")
            self.clear_highlight()
            self.last_debug_output = "Code ran successfully. No errors found."
        except Exception as e:
            tb = traceback.format_exc()
            self.speaker.speak("An error occurred while running the code.")
            match = re.search(r'File "<string>", line (\d+)', tb)
            if match:
                line_num = int(match.group(1))
                self.highlight_error_line(line_num)
                self.speaker.speak(f"Check line {line_num} for errors.")
            else:
                self.speaker.speak("Could not locate the specific line of error.")
            self.last_debug_output = tb
            print(tb)

    def highlight_error_line(self, line_number):
        self.clear_highlight()
        self.code_text.tag_add("error", f"{line_number}.0", f"{line_number}.end")
        self.code_text.tag_config("error", background="red", foreground="white")

    def clear_highlight(self):
        self.code_text.tag_delete("error")

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if filepath:
            with open(filepath, "r") as file:
                content = file.read()
                self.code_text.delete("1.0", tk.END)
                self.code_text.insert(tk.END, content)

    def save_audio(self):
        code = self.code_text.get("1.0", tk.END)
        lines = code.strip().split("\n")
        all_text = []
        for i, line in enumerate(lines, start=1):
            clean_line = line.strip()
            if not clean_line:
                continue
            all_text.append(f"Line {i}: {clean_line}")
            try:
                parsed = ast.parse(line)
                for node in parsed.body:
                    if isinstance(node, ast.Assign):
                        var_name = node.targets[0].id
                        all_text.append(f"This assigns a value to '{var_name}'.")
                    elif isinstance(node, ast.If):
                        all_text.append("This checks a condition with an if-statement.")
                    elif isinstance(node, ast.For):
                        all_text.append("This is a for-loop over a sequence.")
                    elif isinstance(node, ast.FunctionDef):
                        all_text.append(f"This defines a function named '{node.name}'.")
                    else:
                        all_text.append("This is an executable line.")
            except:
                all_text.append("This line could not be explained.")
        combined = "\n".join(all_text)
        filepath = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")])
        if filepath:
            self.speaker.save_to_mp3(combined, filename=filepath)
        messagebox.showinfo("Saved", f"Audio saved at {filepath}")

    def save_debug_report(self):
        if not self.last_debug_output.strip():
            messagebox.showinfo("Info", "No debug result to save yet.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.last_debug_output)
            messagebox.showinfo("Saved", f"Debug report saved to {file_path}")

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = CodeReaderApp(root)
    root.mainloop()

