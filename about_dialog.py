import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import os
from config import Config
import locales

class AboutDialog:
    def __init__(self, parent, config=None):
        self.parent = parent
        self.config = config or Config()
        self.lang = self.config.get_language()
        self.tr = locales.LANGUAGES.get(self.lang, locales.LANGUAGES["en"])
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(self.tr["about_program"])
        self.dialog.geometry("700x600")
        self.dialog.configure(bg="#000000")
        self.center_window()
        self.dialog.resizable(False, False)
        
        self.setup_ui()
    
    def center_window(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tk.Frame(self.dialog, bg="#000000")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        logo_frame = tk.Frame(main_frame, bg="#000000")
        logo_frame.pack(pady=(0, 20))
        
        logo_paths = ["Logo.png", "logo.png", "icon.png", "icon.ico"]
        logo_image = None
        
        for path in logo_paths:
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img = img.resize((100, 100), Image.Resampling.LANCZOS)
                    logo_image = ImageTk.PhotoImage(img)
                    break
                except:
                    continue
        
        if logo_image:
            logo_label = tk.Label(
                logo_frame,
                image=logo_image,
                bg="#000000"
            )
            logo_label.image = logo_image
            logo_label.pack()
        else:
            logo_text = tk.Label(
                logo_frame,
                text="WMR",
                font=("Lucida Console", 36, "bold"),
                bg="#000000",
                fg="#3B82F6"
            )
            logo_text.pack()
        
        title_label = tk.Label(
            main_frame,
            text=self.tr["program_name"],
            font=("Lucida Console", 24, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(pady=(0, 10))
        
        version_label = tk.Label(
            main_frame,
            text=f"{self.tr['version']}: v1.0.1",
            font=("Lucida Console", 12),
            bg="#000000",
            fg="#CCCCCC"
        )
        version_label.pack(pady=(0, 20))
        
        separator1 = tk.Frame(main_frame, height=1, bg="#666666")
        separator1.pack(fill="x", pady=10)
        
        info_frame = tk.Frame(main_frame, bg="#000000")
        info_frame.pack(fill="x", pady=10)
        
        info_items = [
            (self.tr["developer"], "NightAuroraCoder"),
            (self.tr["organization"], "WMR Group"),
            (self.tr["github_repo"], "github.com/WMR-Group/WMR-GROUP-APPS"),
            (self.tr["license"], self.tr["mit_license"])
        ]
        
        for label, value in info_items:
            row = tk.Frame(info_frame, bg="#000000")
            row.pack(fill="x", pady=5)
            
            lbl = tk.Label(
                row,
                text=label + ":",
                font=("Lucida Console", 10),
                bg="#000000",
                fg="#999999"
            )
            lbl.pack(side="left")
            
            val = tk.Label(
                row,
                text=value,
                font=("Lucida Console", 10, "bold"),
                bg="#000000",
                fg="#CCCCCC"
            )
            val.pack(side="left", padx=(10, 0))
        
        separator2 = tk.Frame(main_frame, height=1, bg="#666666")
        separator2.pack(fill="x", pady=10)
        
        description_label = tk.Label(
            main_frame,
            text=self.tr["description"],
            font=("Lucida Console", 11),
            bg="#000000",
            fg="#FFFFFF",
            wraplength=600,
            justify="center"
        )
        description_label.pack(pady=10)
        
        features_frame = tk.Frame(main_frame, bg="#1A1A1A")
        features_frame.pack(fill="x", pady=15, ipadx=10, ipady=10)
        
        features_label = tk.Label(
            features_frame,
            text=self.tr["features"] + ":",
            font=("Lucida Console", 12, "bold"),
            bg="#1A1A1A",
            fg="#FFFFFF",
            anchor="w"
        )
        features_label.pack(anchor="w", padx=10, pady=(5, 10))
        
        features = [
            self.tr["feature1"],
            self.tr["feature2"],
            self.tr["feature3"],
            self.tr["feature4"],
            self.tr["feature5"]
        ]
        
        for feature in features:
            feature_label = tk.Label(
                features_frame,
                text=feature,
                font=("Lucida Console", 10),
                bg="#1A1A1A",
                fg="#CCCCCC",
                anchor="w"
            )
            feature_label.pack(anchor="w", padx=20, pady=2)
        
        close_btn = tk.Button(
            main_frame,
            text=self.tr["close"],
            font=("Lucida Console", 11),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.dialog.destroy
        )
        close_btn.pack(pady=20)
    
    def show(self):
        self.dialog.grab_set()
        self.dialog.wait_window()