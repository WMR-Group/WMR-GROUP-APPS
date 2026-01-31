import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class LoadingScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WMR Group Apps")
        self.root.geometry("600x400")
        self.root.configure(bg="#000000")
        self.center_window()
        
        self.logo_path = None
        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_ui()
    
    def on_close(self):
        self.running = False
        if hasattr(self, 'progress_bar'):
            try:
                self.progress_bar.stop()
            except:
                pass
        self.root.destroy()
    
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
        
        logo_frame = tk.Frame(main_frame, bg="#000000")
        logo_frame.pack(expand=True)
        
        logo_paths = ["Logo.png", "logo.png", "icon.png", "icon.ico"]
        for path in logo_paths:
            if os.path.exists(path):
                self.logo_path = path
                break
        
        if self.logo_path:
            try:
                img = Image.open(self.logo_path)
                img = img.resize((200, 200), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
                
                logo_label = tk.Label(
                    logo_frame,
                    image=self.logo_image,
                    bg="#000000"
                )
                logo_label.pack()
            except:
                self.create_text_logo(logo_frame)
        else:
            self.create_text_logo(logo_frame)
        
        title_label = tk.Label(
            main_frame,
            text="WMR Group Apps",
            font=("Lucida Console", 24, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(pady=20)
        
        version_label = tk.Label(
            main_frame,
            text="v1.0.1",
            font=("Lucida Console", 12),
            bg="#000000",
            fg="#CCCCCC"
        )
        version_label.pack(pady=5)
        
        loading_label = tk.Label(
            main_frame,
            text="Loading...",
            font=("Lucida Console", 14),
            bg="#000000",
            fg="#00FF00"
        )
        loading_label.pack(pady=20)
        
        self.progress_bar = ttk.Progressbar(
            main_frame,
            maximum=100,
            length=400,
            mode="indeterminate"
        )
        self.progress_bar.pack(pady=10)
        
        if self.running:
            self.progress_bar.start(10)
    
    def create_text_logo(self, parent):
        logo_text = tk.Label(
            parent,
            text="WMR",
            font=("Lucida Console", 48, "bold"),
            bg="#000000",
            fg="#3B82F6"
        )
        logo_text.pack()
        
        subtitle_label = tk.Label(
            parent,
            text="GROUP APPS",
            font=("Lucida Console", 18),
            bg="#000000",
            fg="#FFFFFF"
        )
        subtitle_label.pack()
    
    def close(self):
        self.running = False
        if hasattr(self, 'progress_bar'):
            try:
                self.progress_bar.stop()
            except:
                pass
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()