import tkinter as tk
from tkinter import ttk
from config import Config
import locales

class LanguageSelector:
    def __init__(self, callback):
        self.callback = callback
        self.config = Config()
        
        self.root = tk.Tk()
        self.root.title("WMR Group Apps - Language Selection")
        self.root.geometry("500x350")
        self.root.configure(bg="#000000")
        self.center_window()
        
        self.setup_ui()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#000000")
        main_frame.pack(fill="both", expand=True, padx=50, pady=50)
        
        title_label = tk.Label(
            main_frame,
            text="WMR GROUP APPS",
            font=("Lucida Console", 20, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Select Language / Выберите язык",
            font=("Lucida Console", 12),
            bg="#000000",
            fg="#CCCCCC"
        )
        subtitle_label.pack(pady=(0, 30))
        
        button_frame = tk.Frame(main_frame, bg="#000000")
        button_frame.pack(fill="x", pady=10)
        
        english_btn = tk.Button(
            button_frame,
            text="English",
            font=("Lucida Console", 14),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=30,
            pady=15,
            cursor="hand2",
            command=lambda: self.select_language("en")
        )
        english_btn.pack(fill="x", pady=5)
        
        russian_btn = tk.Button(
            button_frame,
            text="Русский",
            font=("Lucida Console", 14),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=30,
            pady=15,
            cursor="hand2",
            command=lambda: self.select_language("ru")
        )
        russian_btn.pack(fill="x", pady=5)
        
        version_label = tk.Label(
            main_frame,
            text="v1.0.1",
            font=("Lucida Console", 10),
            bg="#000000",
            fg="#666666"
        )
        version_label.pack(side="bottom", pady=10)
    
    def select_language(self, lang):
        self.config.set("app.language", lang)
        self.root.destroy()
        self.callback()
    
    def run(self):
        self.root.mainloop()