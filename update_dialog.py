import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from updater import Updater
import locales

class UpdateDialog:
    def __init__(self, updater, update_info, config):
        self.updater = updater
        self.update_info = update_info
        self.config = config
        self.lang = config.get_language()
        self.tr = locales.LANGUAGES.get(self.lang, locales.LANGUAGES["en"])
        
        self.root = tk.Tk()
        self.root.title(self.tr["updating"])
        self.root.geometry("600x400")
        self.root.configure(bg="#000000")
        self.center_window()
        self.root.resizable(False, False)
        
        self.setup_ui()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#000000")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = tk.Label(
            main_frame,
            text=self.tr["updating"],
            font=("Lucida Console", 16, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(pady=(0, 10))
        
        version_label = tk.Label(
            main_frame,
            text=f"{self.update_info['current_version']} → {self.update_info['latest_version']}",
            font=("Lucida Console", 12),
            bg="#000000",
            fg="#CCCCCC"
        )
        version_label.pack(pady=(0, 20))
        
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=560
        )
        progress_bar.pack(pady=10)
        
        self.status_label = tk.Label(
            main_frame,
            text=self.tr["preparing_download"],
            font=("Lucida Console", 10),
            bg="#000000",
            fg="#00FF00"
        )
        self.status_label.pack(pady=5)
        
        console_frame = tk.Frame(main_frame, bg="#1A1A1A")
        console_frame.pack(fill="both", expand=True, pady=10)
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            height=8,
            bg="#1A1A1A",
            fg="#00FF00",
            font=("Lucida Console", 8),
            relief="solid",
            borderwidth=1
        )
        self.console_text.pack(fill="both", expand=True)
    
    def log_message(self, message):
        self.console_text.insert("end", f"> {message}\n")
        self.console_text.see("end")
        self.root.update()
    
    def update_progress(self, percent, status):
        self.progress_var.set(percent)
        self.status_label.config(text=status)
        self.root.update()
    
    def start_update(self):
        try:
            self.log_message("Starting update process...")
            
            zip_path = self.updater.download_update(
                self.update_info["download_url"],
                progress_callback=lambda p, s: self.update_progress(p * 0.7, s)
            )
            
            if not zip_path:
                raise Exception("Download failed")
            
            self.log_message("Download complete, applying update...")
            self.update_progress(70, "Applying update...")
            
            if self.updater.apply_update(zip_path):
                self.log_message("Update applied successfully")
                self.update_progress(100, "Update complete!")
                
                import time
                time.sleep(1)
                
                self.root.destroy()
                
                import tkinter as tk
                from tkinter import messagebox
                
                tk.Tk().withdraw()
                messagebox.showinfo(
                    self.tr["update_complete"],
                    self.tr["update_complete"]
                )
                
                import subprocess
                subprocess.Popen([sys.executable, __file__])
                sys.exit(0)
            else:
                raise Exception("Update application failed")
        
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.status_label.config(text=self.tr["installation_failed"])
    
    def run(self):
        thread = threading.Thread(target=self.start_update, daemon=True)
        thread.start()
        self.root.mainloop()