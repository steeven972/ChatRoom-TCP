import tkinter as tk

class ChatInterface(tk.Tk):
    def __init__(self, master):
        self.master = master
        master.title("Chat Application")
        master.geometry("400x500")
        master.resizable(True, True)
        self.text_widget = tk.Text(self.master, wrap=tk.WORD)
        self.text_widget.pack(padx=10, pady=10)
        self.send_message("Type your message here...")

    def loop(self):
        self.master.mainloop()

    def display_message(self, message):
        print(message)
        
        self.text_widget.insert(tk.END, message + "\n")
        
    
    def send_message(self, message):
        frame = tk.Frame(self.master)
        frame.pack(padx=10, pady=10)
        entry_widget = tk.Entry(frame)
        entry_widget.pack(padx=10, pady=10)
        button_widget = tk.Button(frame, text="Send", command=lambda: self.display_message(entry_widget.get()))
        button_widget.pack(padx=10, pady=10)


screen = tk.Tk()
ChatInterface(screen).loop()