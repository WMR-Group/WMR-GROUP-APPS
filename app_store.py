import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, Menu
import webbrowser
import os
import sys
import subprocess
import threading
import json
import shutil
import re
import requests
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import tempfile
import queue
from concurrent.futures import ThreadPoolExecutor
import math

from config import Config
import locales
from about_dialog import AboutDialog
from prog_info import ProgramInfo

class CodeEditor:
    def __init__(self, parent, file_path):
        self.parent = parent
        self.file_path = file_path
        
        self.editor_window = tk.Toplevel(parent)
        self.editor_window.title(f"Code Editor - {os.path.basename(file_path)}")
        self.editor_window.geometry("1000x700")
        self.editor_window.configure(bg="#000000")
        
        self.setup_ui()
        self.load_file()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.editor_window, bg="#000000")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        header_frame = tk.Frame(main_frame, bg="#000000")
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text=f"Editing: {os.path.basename(self.file_path)}",
            font=("Lucida Console", 12, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(side="left")
        
        button_frame = tk.Frame(header_frame, bg="#000000")
        button_frame.pack(side="right")
        
        save_btn = tk.Button(
            button_frame,
            text="SAVE",
            font=("Lucida Console", 9, "bold"),
            bg="#224422",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.save_file
        )
        save_btn.pack(side="left", padx=5)
        
        close_btn = tk.Button(
            button_frame,
            text="CLOSE",
            font=("Lucida Console", 9),
            bg="#442222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.editor_window.destroy
        )
        close_btn.pack(side="left", padx=5)
        
        edit_frame = tk.Frame(main_frame, bg="#000000")
        edit_frame.pack(fill="both", expand=True)
        
        line_numbers_frame = tk.Frame(edit_frame, bg="#1A1A1A", width=50)
        line_numbers_frame.pack(side="left", fill="y")
        line_numbers_frame.pack_propagate(False)
        
        self.line_numbers = tk.Text(
            line_numbers_frame,
            bg="#1A1A1A",
            fg="#888888",
            font=("Lucida Console", 10),
            width=5,
            height=30,
            relief="flat",
            borderwidth=0,
            state="disabled"
        )
        self.line_numbers.pack(side="left", fill="both", expand=True)
        
        text_frame = tk.Frame(edit_frame, bg="#000000")
        text_frame.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.text_widget = tk.Text(
            text_frame,
            bg="#1A1A1A",
            fg="#00FF00",
            font=("Lucida Console", 10),
            insertbackground="#FFFFFF",
            selectbackground="#444444",
            relief="solid",
            borderwidth=1,
            yscrollcommand=scrollbar.set,
            undo=True
        )
        self.text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_widget.yview)
        
        self.text_widget.bind("<KeyRelease>", self.update_line_numbers)
        self.text_widget.bind("<MouseWheel>", self.update_line_numbers)
        self.text_widget.bind("<Button-4>", self.update_line_numbers)
        self.text_widget.bind("<Button-5>", self.update_line_numbers)
    
    def load_file(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(1.0, content)
            
            self.update_line_numbers()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def save_file(self):
        try:
            content = self.text_widget.get(1.0, tk.END)
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Success", "File saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def update_line_numbers(self, event=None):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete(1.0, tk.END)
        
        lines = self.text_widget.get(1.0, tk.END).count('\n') + 1
        for i in range(1, lines + 1):
            self.line_numbers.insert(tk.END, f"{i}\n")
        
        self.line_numbers.config(state="disabled")
        
        self.text_widget.yview_moveto(self.text_widget.yview()[0])
        self.line_numbers.yview_moveto(self.text_widget.yview()[0])
    
    def show(self):
        self.editor_window.grab_set()
        self.editor_window.wait_window()

class WMRGroupApps:
    def __init__(self, root, config=None):
        self.root = root
        self.config = config or Config()
        self.lang = self.config.get_language()
        self.tr = locales.LANGUAGES.get(self.lang, locales.LANGUAGES["en"])
        
        self.root.title(f"{self.tr['app_title']} - Application Manager")
        self.root.geometry("1400x800")
        self.root.minsize(1000, 600)
        
        self.base_dir = Path(__file__).parent
        self.install_dir = self.config.get_install_path()
        self.downloads_dir = self.config.get_downloads_path()
        self.temp_dir = self.config.get_temp_path()
        self.config_file = self.base_dir / "wmr_config.json"
        
        os.makedirs(self.install_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.app_config = self.load_config()
        self.prog_info = ProgramInfo(self.config)
        
        self.sync_program_info()
        
        self.apps = self.get_apps_data()
        
        self.detected_files = {}
        self.releases_cache = {}
        
        self.right_panel = None
        self.current_app = None
        self.apps_frame = None
        self.canvas = None
        
        self.task_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self.process_tasks()
        
        self.sound_enabled = self.config.get_sound_effects()
        
        self.setup_ui()
        
        self.check_app_versions()
        
        self.root.bind('<Configure>', self.on_window_resize)
        self.setup_scroll_events()
        
        self.check_manager_update_on_start()
    
    def check_manager_update_on_start(self):
        def check_task():
            try:
                from updater import Updater
                updater = Updater(self.config)
                update_info = updater.check_for_updates()
                
                if update_info.get("available", False):
                    self.root.after(0, lambda: self.show_update_notification(update_info))
            except:
                pass
        
        self.add_task(check_task)
    
    def show_update_notification(self, update_info):
        response = messagebox.askyesno(
            self.tr["update_available_title"],
            f"New version {update_info['latest_version']} is available!\n\n"
            f"Current version: {update_info['current_version']}\n"
            f"Release date: {update_info.get('release_date', 'Unknown')}\n\n"
            f"Would you like to view the changelog and update?"
        )
        
        if response:
            self.show_changelog_and_update(update_info)
    
    def show_changelog_and_update(self, update_info):
        changelog_window = tk.Toplevel(self.root)
        changelog_window.title(f"Update to v{update_info['latest_version']}")
        changelog_window.geometry("800x600")
        changelog_window.configure(bg="#000000")
        
        main_frame = tk.Frame(changelog_window, bg="#000000")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = tk.Label(
            main_frame,
            text=f"Update v{update_info['current_version']} → v{update_info['latest_version']}",
            font=("Lucida Console", 16, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(pady=(0, 10))
        
        changelog_text = scrolledtext.ScrolledText(
            main_frame,
            bg="#1A1A1A",
            fg="#00FF00",
            font=("Lucida Console", 9),
            height=20
        )
        changelog_text.pack(fill="both", expand=True, pady=10)
        
        try:
            changelog_url = self.config.get("updater.changelog_url")
            response = requests.get(changelog_url, timeout=10)
            if response.status_code == 200:
                changelog_text.insert("1.0", response.text)
            else:
                changelog_text.insert("1.0", update_info.get("changelog", "No changelog available"))
        except:
            changelog_text.insert("1.0", update_info.get("changelog", "No changelog available"))
        
        changelog_text.config(state="disabled")
        
        button_frame = tk.Frame(main_frame, bg="#000000")
        button_frame.pack(fill="x", pady=10)
        
        update_btn = tk.Button(
            button_frame,
            text="UPDATE NOW",
            font=("Lucida Console", 10, "bold"),
            bg="#224422",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=10,
            cursor="hand2",
            command=lambda: self.start_manager_update(update_info, changelog_window)
        )
        update_btn.pack(side="left", padx=10)
        
        cancel_btn = tk.Button(
            button_frame,
            text="CANCEL",
            font=("Lucida Console", 10),
            bg="#442222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=10,
            cursor="hand2",
            command=changelog_window.destroy
        )
        cancel_btn.pack(side="right", padx=10)
    
    def start_manager_update(self, update_info, window):
        window.destroy()
        from updater import Updater
        from update_dialog import UpdateDialog
        
        updater = Updater(self.config)
        update_dialog = UpdateDialog(updater, update_info, self.config)
        update_dialog.run()
    
    def play_sound(self, sound_type="hover"):
        if not self.sound_enabled:
            return
        
        try:
            if sys.platform == "win32":
                import winsound
                if sound_type == "hover":
                    winsound.Beep(800, 50)
                elif sound_type == "click":
                    winsound.Beep(1000, 30)
        except:
            pass
    
    def setup_scroll_events(self):
        def on_mousewheel(event):
            if self.canvas:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.root.bind_all("<MouseWheel>", on_mousewheel)
        
        def on_linux_scroll_up(event):
            if self.canvas:
                self.canvas.yview_scroll(-1, "units")
        self.root.bind_all("<Button-4>", on_linux_scroll_up)
        
        def on_linux_scroll_down(event):
            if self.canvas:
                self.canvas.yview_scroll(1, "units")
        self.root.bind_all("<Button-5>", on_linux_scroll_down)
    
    def on_window_resize(self, event):
        if event.widget == self.root:
            self.update_ui_layout()
    
    def update_ui_layout(self):
        if hasattr(self, 'right_panel') and self.right_panel:
            for widget in self.right_panel.winfo_children():
                if isinstance(widget, tk.Canvas):
                    widget.update_idletasks()
                    widget.configure(scrollregion=widget.bbox("all"))
    
    def sync_program_info(self):
        self.prog_info.check_and_sync_all(str(self.install_dir))
    
    def animate_widget_color(self, widget, from_color, to_color, steps=10, duration=100):
        def interpolate_color(color1, color2, factor):
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            r = int(r1 + (r2 - r1) * factor)
            g = int(g1 + (g2 - g1) * factor)
            b = int(b1 + (b2 - b1) * factor)
            return f'#{r:02x}{g:02x}{b:02x}'
        
        for i in range(steps + 1):
            factor = i / steps
            color = interpolate_color(from_color, to_color, factor)
            widget.after(int(duration * i / steps), lambda c=color: widget.config(bg=c))
    
    def slide_widget(self, widget, start_x, end_x, start_y, end_y, steps=20, duration=200):
        dx = (end_x - start_x) / steps
        dy = (end_y - start_y) / steps
        
        widget.place(x=start_x, y=start_y)
        
        for i in range(steps + 1):
            x = start_x + dx * i
            y = start_y + dy * i
            widget.after(int(duration * i / steps), lambda x=x, y=y: widget.place(x=x, y=y))
    
    def fade_in_widget(self, widget, steps=20, duration=200):
        if hasattr(widget, 'winfo_exists') and not widget.winfo_exists():
            return
            
        current_alpha = widget.winfo_toplevel().attributes('-alpha') if hasattr(widget.winfo_toplevel(), 'attributes') else 1.0
        
        for i in range(steps + 1):
            alpha = current_alpha + (1.0 - current_alpha) * (i / steps)
            try:
                widget.after(int(duration * i / steps), 
                           lambda a=alpha: widget.winfo_toplevel().attributes('-alpha', a))
            except:
                pass
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        colors = {
            "bg": "#000000",
            "fg": "#FFFFFF",
            "bg_secondary": "#1A1A1A",
            "bg_tertiary": "#333333",
            "border": "#666666",
            "highlight": "#FFFFFF",
            "button_bg": "#222222",
            "button_fg": "#FFFFFF",
            "button_active": "#444444"
        }
        
        font_family = "Lucida Console"
        font_size = 8
        
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("TLabel", 
                           background=colors["bg"],
                           foreground=colors["fg"],
                           font=(font_family, font_size))
        
        self.style.configure("Title.TLabel",
                           font=(font_family, 16, "bold"))
        
        self.style.configure("Card.TFrame",
                           background=colors["bg_secondary"],
                           relief="solid",
                           borderwidth=1)
        
        self.style.configure("Square.TButton",
                           background=colors["button_bg"],
                           foreground=colors["button_fg"],
                           font=(font_family, font_size),
                           borderwidth=1,
                           relief="solid",
                           padding=6)
        
        self.style.map("Square.TButton",
                      background=[("active", colors["button_active"])])
        
        self.style.configure("Status.TLabel",
                           font=(font_family, 7))
    
    def get_apps_data(self):
        apps_info = self.prog_info.get_all_programs_info()
        
        apps = []
        for app_name, info in apps_info.items():
            app_path = Path(self.install_dir) / app_name
            status = self.check_app_status(app_name)
            
            app_data = {
                "id": len(apps) + 1,
                "name": info["name"],
                "version": info.get("latest_version", "1.0.0"),
                "description": "",
                "author": "WMR Group",
                "github_url": "",
                "github_api": "",
                "releases_api": "",
                "download_url": "",
                "release_date": info.get("last_updated", datetime.now().strftime("%d.%m.%Y")),
                "stars": 0,
                "forks": 0,
                "category": self.tr["utilities"],
                "install_path": str(app_path),
                "status": status,
                "local_version": self.get_local_version(app_name),
                "has_update": info.get("update_available", False),
                "latest_version": info.get("latest_version", "1.0.0")
            }
            
            if app_name == "WALMFAST":
                app_data.update({
                    "description": "WALM Fastboot - tool for easier device flashing via fastboot",
                    "author": "WALM Studio & MintVioletAurora",
                    "github_url": "https://github.com/WALMFAST/walmfast",
                    "github_api": "https://api.github.com/repos/WALMFAST/walmfast/releases/latest",
                    "releases_api": "https://api.github.com/repos/WALMFAST/walmfast/releases",
                    "download_url": "https://github.com/WALMFAST/walmfast/archive/refs/heads/main.zip",
                    "category": self.tr["flashing_tools"],
                })
            elif app_name == "Wlap-FlashTool":
                app_data.update({
                    "description": "Professional flashing tool for mobile devices",
                    "author": "MintVioletAurora",
                    "github_url": "https://github.com/MintVioletAurora/Wlap-FlashTool",
                    "github_api": "https://api.github.com/repos/MintVioletAurora/Wlap-FlashTool/releases/latest",
                    "releases_api": "https://api.github.com/repos/MintVioletAurora/Wlap-FlashTool/releases",
                    "download_url": "https://github.com/MintVioletAurora/Wlap-FlashTool/archive/refs/heads/main.zip",
                    "category": self.tr["flashing_tools"],
                })
            elif app_name == "NightAuroraZIP":
                app_data.update({
                    "description": "Powerful archiver for ZIP, RAR, 7z, TAR archives",
                    "author": "MintVioletAurora",
                    "github_url": "https://github.com/MintVioletAurora/NightAuroraZIP",
                    "github_api": "https://api.github.com/repos/MintVioletAurora/NightAuroraZIP/releases/latest",
                    "releases_api": "https://api.github.com/repos/MintVioletAurora/NightAuroraZIP/releases",
                    "download_url": "https://github.com/MintVioletAurora/NightAuroraZIP/archive/refs/heads/main.zip",
                    "category": self.tr["utilities"],
                })
            elif app_name == "deltarune-translator":
                app_data.update({
                    "description": "Deltarune translation tool",
                    "author": "WALM Studio",
                    "github_url": "https://github.com/walmstudio/deltarune-translator",
                    "github_api": "https://api.github.com/repos/walmstudio/deltarune-translator/releases/latest",
                    "releases_api": "https://api.github.com/repos/walmstudio/deltarune-translator/releases",
                    "download_url": "https://github.com/walmstudio/deltarune-translator/archive/refs/heads/main.zip",
                    "category": self.tr["utilities"],
                })
            elif app_name == "musm":
                app_data.update({
                    "description": "Music manager and player",
                    "author": "WALM Studio",
                    "github_url": "https://github.com/walmstudio/musm",
                    "github_api": "https://api.github.com/repos/walmstudio/musm/releases/latest",
                    "releases_api": "https://api.github.com/repos/walmstudio/musm/releases",
                    "download_url": "https://github.com/walmstudio/musm/archive/refs/heads/main.zip",
                    "category": self.tr["utilities"],
                })
            elif app_name == "wayset":
                app_data.update({
                    "description": "Wireless audio system setup tool",
                    "author": "WALM Studio",
                    "github_url": "https://github.com/walmstudio/wayset",
                    "github_api": "https://api.github.com/repos/walmstudio/wayset/releases/latest",
                    "releases_api": "https://api.github.com/repos/walmstudio/wayset/releases",
                    "download_url": "https://github.com/walmstudio/wayset/archive/refs/heads/main.zip",
                    "category": self.tr["utilities"],
                })
            elif app_name == "lifus":
                app_data.update({
                    "description": "Life utilities collection",
                    "author": "WALM Archive",
                    "github_url": "https://github.com/walm-archive/lifus",
                    "github_api": "https://api.github.com/repos/walm-archive/lifus/releases/latest",
                    "releases_api": "https://api.github.com/repos/walm-archive/lifus/releases",
                    "download_url": "https://github.com/walm-archive/lifus/archive/refs/heads/main.zip",
                    "category": self.tr["utilities"],
                })
            
            apps.append(app_data)
        
        return apps
    
    def check_app_status(self, app_name):
        app_path = Path(self.install_dir) / app_name
        if not app_path.exists():
            return "not_installed"
        
        exe_files = self.find_executable_files(str(app_path))
        if exe_files:
            return "installed"
        
        for item in os.listdir(app_path):
            item_path = app_path / item
            if item_path.is_dir():
                return "partial"
            if item.endswith((".py", ".txt", ".md", ".json")):
                return "partial"
        
        return "not_installed"
    
    def find_executable_files(self, path):
        executables = []
        if not os.path.exists(path):
            return executables
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith((".exe", ".bat", ".py", ".sh", ".command", ".ps1", ".cmd", ".dll")):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(path)
                    file_type = "exe" if file.lower().endswith(".exe") else \
                               "bat" if file.lower().endswith(".bat") else \
                               "py" if file.lower().endswith(".py") else \
                               "sh" if file.lower().endswith(".sh") else \
                               "command" if file.lower().endswith(".command") else \
                               "ps1" if file.lower().endswith(".ps1") else \
                               "dll" if file.lower().endswith(".dll") else "cmd"
                    
                    executables.append({
                        "name": file,
                        "path": str(full_path),
                        "rel_path": str(rel_path),
                        "size": full_path.stat().st_size,
                        "type": file_type
                    })
        return executables
    
    def get_local_version(self, app_name):
        info = self.prog_info.get_program_info(app_name)
        version = info.get("current_version", "unknown")
        return "v" + version if version != "unknown" and not version.startswith("v") else version
    
    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"installed_apps": {}, "last_update_check": None}
    
    def save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.app_config, f, indent=2, ensure_ascii=False)
    
    def process_tasks(self):
        try:
            while not self.task_queue.empty():
                task = self.task_queue.get_nowait()
                if task:
                    self.executor.submit(task)
        except:
            pass
        
        self.root.after(100, self.process_tasks)
    
    def add_task(self, task):
        self.task_queue.put(task)
    
    def check_app_versions(self):
        def check_versions_task():
            for app in self.apps:
                try:
                    if app.get("github_api"):
                        response = requests.get(app["github_api"], timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            latest_version = data.get("tag_name", app["version"])
                            
                            local_ver = self.normalize_version(app["local_version"])
                            latest_ver = self.normalize_version(latest_version)
                            
                            if self.compare_versions(latest_ver, local_ver) > 0:
                                app["has_update"] = True
                                app["latest_version"] = latest_version
                                self.prog_info.set_update_available(app["name"], True, latest_version)
                            else:
                                app["has_update"] = False
                                app["latest_version"] = app["local_version"]
                                self.prog_info.set_update_available(app["name"], False)
                        else:
                            app["has_update"] = False
                    else:
                        app["has_update"] = False
                
                except:
                    app["has_update"] = False
            
            self.root.after(0, self.display_apps_list)
        
        self.add_task(check_versions_task)
    
    def normalize_version(self, version):
        if not version or version.lower() in ["unknown", "vunknown"]:
            return [0, 0, 0]
        
        version = re.sub(r"^[vV]", "", version)
        parts = version.split(".")
        normalized = []
        
        for part in parts[:3]:
            match = re.match(r"(\d+)", part)
            if match:
                normalized.append(int(match.group(1)))
            else:
                try:
                    normalized.append(int(part))
                except:
                    normalized.append(0)
        
        while len(normalized) < 3:
            normalized.append(0)
        
        return normalized
    
    def compare_versions(self, ver1, ver2):
        for v1, v2 in zip(ver1, ver2):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        return 0
    
    def setup_ui(self):
        self.root.attributes('-alpha', 0.0)
        
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.tr["file"], menu=file_menu)
        file_menu.add_command(label=self.tr["sync"], command=self.sync_programs)
        file_menu.add_separator()
        file_menu.add_command(label=self.tr["exit"], command=self.root.quit)
        
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.tr["view"], menu=view_menu)
        view_menu.add_command(label=self.tr["check_updates"], command=self.check_manager_updates)
        view_menu.add_command(label=self.tr["check_app_updates"], command=self.check_github_updates)
        view_menu.add_command(label=self.tr["open_install_folder"], command=lambda: self.open_folder(self.install_dir))
        
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.tr["tools"], menu=tools_menu)
        tools_menu.add_command(label=self.tr["detect_all_files"], command=self.detect_all_executables)
        tools_menu.add_command(label="Refresh App Status", command=self.refresh_all_app_status)
        tools_menu.add_separator()
        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        tools_menu.add_checkbutton(label="Sound Effects", variable=self.sound_var, command=self.toggle_sound_effects)
        
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.tr["help"], menu=help_menu)
        help_menu.add_command(label=self.tr["about"], command=self.show_about)
        
        header = tk.Frame(self.root, bg="#1A1A1A", height=60)
        header.pack(fill="x")
        
        logo_frame = tk.Frame(header, bg="#1A1A1A")
        logo_frame.pack(side="left", padx=20, pady=12)
        
        logo_label = tk.Label(
            logo_frame,
            text="WMR GROUP APPS",
            font=("Lucida Console", 18, "bold"),
            fg="#FFFFFF",
            bg="#1A1A1A"
        )
        logo_label.pack(side="left")
        
        version_label = tk.Label(
            logo_frame,
            text="v1.1.3",
            font=("Lucida Console", 8),
            fg="#CCCCCC",
            bg="#1A1A1A"
        )
        version_label.pack(side="left", padx=(8, 0), pady=2)
        
        header_buttons = tk.Frame(header, bg="#1A1A1A")
        header_buttons.pack(side="right", padx=20, pady=12)
        
        sync_btn = tk.Button(
            header_buttons,
            text=self.tr["sync"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.sync_programs
        )
        sync_btn.pack(side="left", padx=4)
        
        about_btn = tk.Button(
            header_buttons,
            text=self.tr["about"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.show_about
        )
        about_btn.pack(side="left", padx=4)
        
        check_manager_update_btn = tk.Button(
            header_buttons,
            text=self.tr["check_manager_update"],
            font=("Lucida Console", 8, "bold"),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.check_manager_updates
        )
        check_manager_update_btn.pack(side="left", padx=4)
        
        check_app_updates_btn = tk.Button(
            header_buttons,
            text=self.tr["check_app_updates"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.check_github_updates
        )
        check_app_updates_btn.pack(side="left", padx=4)
        
        folder_btn = tk.Button(
            header_buttons,
            text=self.tr["open_install_folder"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=lambda: self.open_folder(self.install_dir)
        )
        folder_btn.pack(side="left", padx=4)
        
        main_container = tk.Frame(self.root, bg="#000000")
        main_container.pack(fill="both", expand=True, padx=10, pady=8)
        
        left_panel = tk.Frame(main_container, bg="#1A1A1A", width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 8))
        left_panel.pack_propagate(False)
        
        list_header = tk.Frame(left_panel, bg="#1A1A1A")
        list_header.pack(fill="x", padx=15, pady=(15, 8))
        
        list_title = tk.Label(
            list_header,
            text=self.tr["available_apps"],
            font=("Lucida Console", 12, "bold"),
            fg="#FFFFFF",
            bg="#1A1A1A"
        )
        list_title.pack(anchor="w")
        
        filter_frame = tk.Frame(left_panel, bg="#1A1A1A")
        filter_frame.pack(fill="x", padx=15, pady=(0, 8))
        
        filter_label = tk.Label(
            filter_frame,
            text=self.tr["category_filter"] + ":",
            font=("Lucida Console", 7),
            fg="#CCCCCC",
            bg="#1A1A1A"
        )
        filter_label.pack(side="left")
        
        filters = [self.tr["all"], self.tr["flashing_tools"], self.tr["utilities"]]
        self.filter_buttons = []
        for i, filt in enumerate(filters):
            btn = tk.Button(
                filter_frame,
                text=filt,
                font=("Lucida Console", 7),
                bg="#333333" if i == 0 else "#222222",
                fg="white",
                relief="solid",
                borderwidth=1,
                padx=8,
                pady=2
            )
            btn.pack(side="left", padx=(6, 0))
            self.filter_buttons.append(btn)
        
        canvas_frame = tk.Frame(left_panel, bg="#1A1A1A")
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=(0, 8))
        
        self.canvas = tk.Canvas(canvas_frame, bg="#1A1A1A", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.apps_frame = tk.Frame(self.canvas, bg="#1A1A1A")
        
        self.apps_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.apps_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.display_apps_list()
        
        stats_frame = tk.Frame(left_panel, bg="#1A1A1A")
        stats_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        self.stats_label = tk.Label(
            stats_frame,
            text="",
            font=("Lucida Console", 8),
            fg="#FFFFFF",
            bg="#1A1A1A"
        )
        self.stats_label.pack()
        
        self.update_stats()
        
        # СОЗДАЕМ ПРАВУЮ ПАНЕЛЬ ПРАВИЛЬНО
        self.right_panel = tk.Frame(main_container, bg="#000000")
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # Инициализируем правую панель с приветствием
        self.show_welcome()
        
        self.root.after(100, lambda: self.fade_in_widget(self.root, steps=30, duration=300))
    
    def toggle_sound_effects(self):
        self.sound_enabled = self.sound_var.get()
        self.config.set_sound_effects(self.sound_enabled)
        messagebox.showinfo("Settings", f"Sound effects {'enabled' if self.sound_enabled else 'disabled'}.")
    
    def check_manager_updates(self):
        from updater import Updater
        
        updater = Updater(self.config)
        update_info = updater.check_for_updates()
        
        if update_info.get("available", False):
            self.show_changelog_and_update(update_info)
        else:
            messagebox.showinfo(
                self.tr["info"],
                self.tr["no_update"]
            )
    
    def check_github_updates(self):
        def check_updates_task():
            updates_found = 0
            for app in self.apps:
                try:
                    if app.get("github_api"):
                        response = requests.get(app["github_api"], timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            latest_version = data.get("tag_name", app["version"])
                            
                            local_ver = self.normalize_version(app["local_version"])
                            latest_ver = self.normalize_version(latest_version)
                            
                            if self.compare_versions(latest_ver, local_ver) > 0:
                                app["has_update"] = True
                                app["latest_version"] = latest_version
                                self.prog_info.set_update_available(app["name"], True, latest_version)
                                updates_found += 1
                            else:
                                app["has_update"] = False
                                self.prog_info.set_update_available(app["name"], False)
                        else:
                            app["has_update"] = False
                    else:
                        app["has_update"] = False
                
                except:
                    app["has_update"] = False
            
            self.root.after(0, self.update_ui_after_check)
            
            if updates_found > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    self.tr["info"],
                    f"Found {updates_found} application(s) with updates available!"
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    self.tr["info"],
                    self.tr["no_update"]
                ))
        
        self.add_task(check_updates_task)
    
    def refresh_all_app_status(self):
        def refresh_task():
            for app in self.apps:
                app["status"] = self.check_app_status(app["name"])
                app["local_version"] = self.get_local_version(app["name"])
                
                self.prog_info.update_program_status(
                    app["name"], 
                    app["status"], 
                    app["install_path"] if app["status"] == "installed" else None
                )
            
            self.root.after(0, self.display_apps_list)
            self.root.after(0, self.update_stats)
            if self.current_app:
                self.root.after(0, lambda: self.show_app_details(self.current_app))
        
        self.add_task(refresh_task)
    
    def detect_all_executables(self):
        def detect_all_task():
            for app in self.apps:
                if app["status"] == "installed":
                    app_path = Path(app["install_path"])
                    if app_path.exists():
                        files = self.find_executable_files(str(app_path))
                        if files:
                            self.detected_files[app["name"]] = files
                            self.prog_info.update_executable_files(app["name"], files)
            
            self.root.after(0, lambda: messagebox.showinfo(
                self.tr["info"],
                f"Detected executables in {len([a for a in self.apps if a['status'] == 'installed'])} installed applications"
            ))
            
            if self.current_app:
                self.root.after(0, lambda: self.show_app_details(self.current_app))
        
        self.add_task(detect_all_task)
    
    def sync_programs(self):
        def sync_task():
            self.prog_info.check_and_sync_all(str(self.install_dir))
            
            self.sync_program_info()
            
            self.apps = self.get_apps_data()
            
            self.root.after(0, lambda: messagebox.showinfo(
                self.tr["sync_complete"],
                "Program information synchronized successfully!"
            ))
            
            self.root.after(0, self.display_apps_list)
            self.root.after(0, self.update_stats)
            if self.current_app:
                self.root.after(0, lambda: self.show_app_details(self.current_app))
        
        self.add_task(sync_task)
    
    def show_about(self):
        about_dialog = AboutDialog(self.root, self.config)
        about_dialog.show()
    
    def update_stats(self):
        if not hasattr(self, "stats_label"):
            return
        
        installed_count = sum(1 for app in self.apps if app["status"] == "installed")
        update_count = sum(1 for app in self.apps if app.get("has_update", False))
        
        stats_text = f"{self.tr['all']}: {len(self.apps)} | {self.tr['installed'].lower()}: {installed_count}"
        if update_count > 0:
            stats_text += f" | {self.tr['update_available'].lower()}: {update_count}"
        
        self.stats_label.config(text=stats_text)
    
    def display_apps_list(self):
        if not hasattr(self, "apps_frame") or not self.apps_frame:
            return
        
        for widget in self.apps_frame.winfo_children():
            widget.destroy()
        
        for app in self.apps:
            self.create_app_card(app)
    
    def create_app_card(self, app):
        if not hasattr(self, "apps_frame") or not self.apps_frame:
            return
        
        for widget in self.apps_frame.winfo_children():
            widget.destroy()
        
        for app in self.apps:
            card = tk.Frame(
                self.apps_frame,
                bg="#222222",
                relief="solid",
                borderwidth=1
            )
            card.pack(fill="x", padx=8, pady=4, ipady=3)
            
            status_icon = "●"
            status_color = "#00FF00" if app["status"] == "installed" else "#FF0000"
            
            if app.get("has_update", False):
                status_icon = "↻"
                status_color = "#FFFF00"
            
            icon_label = tk.Label(
                card,
                text=status_icon,
                font=("Lucida Console", 10),
                bg="#222222",
                fg=status_color
            )
            icon_label.pack(side="left", padx=(10, 6), pady=6)
            
            text_frame = tk.Frame(card, bg="#222222")
            text_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
            
            name_text = app["name"]
            if app.get("has_update", False):
                name_text += f" [{self.tr['update_to']} {app['latest_version']}]"
            
            name_label = tk.Label(
                text_frame,
                text=name_text,
                font=("Lucida Console", 9, "bold"),
                bg="#222222",
                fg="#FFFFFF",
                anchor="w"
            )
            name_label.pack(fill="x", pady=(3, 1))
            
            version_text = f"{app['local_version']} | {app['category']}"
            version_label = tk.Label(
                text_frame,
                text=version_text,
                font=("Lucida Console", 7),
                bg="#222222",
                fg="#CCCCCC",
                anchor="w"
            )
            version_label.pack(fill="x")
            
            status_frame = tk.Frame(card, bg="#222222")
            status_frame.pack(side="right", padx=(0, 10), pady=6)
            
            status_text = self.tr["installed"] if app["status"] == "installed" else self.tr["not_installed"]
            status_bg = "#333333" if app["status"] == "installed" else "#222222"
            
            status_label = tk.Label(
                status_frame,
                text=status_text,
                font=("Lucida Console", 7, "bold"),
                bg=status_bg,
                fg="#FFFFFF",
                padx=6,
                pady=1,
                relief="solid",
                borderwidth=1
            )
            status_label.pack()
            
            def on_enter(e):
                self.play_sound("hover")
                original_bg = e.widget["bg"]
                self.animate_widget_color(e.widget, original_bg, "#333333", steps=5, duration=50)
            
            def on_leave(e):
                original_bg = "#222222"
                self.animate_widget_color(e.widget, "#333333", original_bg, steps=5, duration=50)
            
            def on_click_app(e, app_data=app):
                self.play_sound("click")
                self.show_app_details(app_data)
            
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            card.bind("<Button-1>", on_click_app)
            
            icon_label.bind("<Enter>", on_enter)
            icon_label.bind("<Leave>", on_leave)
            icon_label.bind("<Button-1>", on_click_app)
            
            name_label.bind("<Enter>", on_enter)
            name_label.bind("<Leave>", on_leave)
            name_label.bind("<Button-1>", on_click_app)
            
            version_label.bind("<Enter>", on_enter)
            version_label.bind("<Leave>", on_leave)
            version_label.bind("<Button-1>", on_click_app)
            
            status_label.bind("<Enter>", on_enter)
            status_label.bind("<Leave>", on_leave)
            status_label.bind("<Button-1>", on_click_app)
    
    def show_welcome(self):
        if not hasattr(self, "right_panel") or not self.right_panel:
            return
        
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        welcome_frame = tk.Frame(self.right_panel, bg="#000000")
        welcome_frame.pack(fill="both", expand=True, padx=30, pady=40)
        
        title_label = tk.Label(
            welcome_frame,
            text=self.tr["welcome_title"],
            font=("Lucida Console", 22, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(pady=(0, 20))
        
        separator = tk.Frame(welcome_frame, height=2, bg="#666666")
        separator.pack(fill="x", pady=12)
        
        desc_label = tk.Label(
            welcome_frame,
            text=self.tr["welcome_text"],
            font=("Lucida Console", 8),
            bg="#000000",
            fg="#CCCCCC",
            justify="left",
            wraplength=900
        )
        desc_label.pack(pady=(0, 25))
        
        actions_frame = tk.Frame(welcome_frame, bg="#000000")
        actions_frame.pack(pady=15)
        
        update_btn = tk.Button(
            actions_frame,
            text=self.tr["check_manager_update"],
            font=("Lucida Console", 8, "bold"),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.check_manager_updates
        )
        update_btn.pack(side="left", padx=8)
        
        check_app_updates_btn = tk.Button(
            actions_frame,
            text=self.tr["check_app_updates"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.check_github_updates
        )
        check_app_updates_btn.pack(side="left", padx=8)
        
        sync_btn = tk.Button(
            actions_frame,
            text=self.tr["sync_now"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.sync_programs
        )
        sync_btn.pack(side="left", padx=8)
        
        folder_btn = tk.Button(
            actions_frame,
            text=self.tr["open_install_directory"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=8,
            cursor="hand2",
            command=lambda: self.open_folder(self.install_dir)
        )
        folder_btn.pack(side="left", padx=8)
        
        for btn in [update_btn, check_app_updates_btn, sync_btn, folder_btn]:
            btn.bind("<Enter>", lambda e: [self.play_sound("hover"), self.animate_widget_color(e.widget, "#222222", "#444444", steps=5, duration=50)])
            btn.bind("<Leave>", lambda e: self.animate_widget_color(e.widget, "#444444", "#222222", steps=5, duration=50))
            btn.bind("<Button-1>", lambda e: self.play_sound("click"))
    
    def show_app_details(self, app):
        if not hasattr(self, "right_panel") or not self.right_panel:
            print("DEBUG: right_panel not found!")
            return
        
        self.current_app = app
        
        # Очищаем правую панель
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        # Создаем Canvas для прокрутки
        main_canvas = tk.Canvas(self.right_panel, bg="#000000", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.right_panel, orient="vertical", command=main_canvas.yview)
        main_frame = tk.Frame(main_canvas, bg="#000000")
        
        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Добавляем прокрутку колесиком мыши
        def on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Верхняя часть с названием и кнопками
        top_frame = tk.Frame(main_frame, bg="#000000")
        top_frame.pack(fill="x", pady=(0, 15), padx=12)
        
        name_frame = tk.Frame(top_frame, bg="#000000")
        name_frame.pack(side="left", fill="x", expand=True)
        
        name_label = tk.Label(
            name_frame,
            text=app["name"],
            font=("Lucida Console", 18, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        name_label.pack(anchor="w")
        
        version_text = f"{self.tr['local_version']}: {app['local_version']}"
        if app.get("has_update", False):
            version_text += f" → {app['latest_version']} {self.tr['update_available'].lower()}"
        
        version_label = tk.Label(
            name_frame,
            text=version_text,
            font=("Lucida Console", 8),
            bg="#000000",
            fg="#CCCCCC"
        )
        version_label.pack(anchor="w", pady=(2, 0))
        
        action_frame = tk.Frame(top_frame, bg="#000000")
        action_frame.pack(side="right")
        
        # Кнопка просмотра релизов (если есть API)
        if app.get("releases_api"):
            releases_btn = tk.Button(
                action_frame,
                text=self.tr["view_releases"],
                font=("Lucida Console", 8),
                bg="#222244",
                fg="#FFFFFF",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda: self.show_releases(app)
            )
            releases_btn.pack(side="left", padx=3)
        
        # Кнопка GitHub
        github_btn = tk.Button(
            action_frame,
            text=self.tr["github"],
            font=("Lucida Console", 8, "bold"),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: webbrowser.open(app["github_url"])
        )
        github_btn.pack(side="left", padx=3)
        
        # Кнопки в зависимости от статуса приложения
        if app["status"] == "installed":
            # Кнопка обновления если есть обновление
            if app.get("has_update", False):
                update_btn = tk.Button(
                    action_frame,
                    text=f"{self.tr['update_to']} {app['latest_version']}",
                    font=("Lucida Console", 8, "bold"),
                    bg="#444400",
                    fg="#FFFF00",
                    relief="solid",
                    borderwidth=1,
                    padx=10,
                    pady=4,
                    cursor="hand2",
                    command=lambda: self.update_app(app)
                )
                update_btn.pack(side="left", padx=3)
            
            # Кнопка удаления
            uninstall_btn = tk.Button(
                action_frame,
                text=self.tr["uninstall"],
                font=("Lucida Console", 8),
                bg="#442222",
                fg="#FFFFFF",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda: self.uninstall_app(app)
            )
            uninstall_btn.pack(side="left", padx=3)
            
            # Кнопка обнаружения файлов
            detect_btn = tk.Button(
                action_frame,
                text=self.tr["detect_files"],
                font=("Lucida Console", 8),
                bg="#222244",
                fg="#FFFFFF",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda: self.detect_app_files(app)
            )
            detect_btn.pack(side="left", padx=3)
            
            # Кнопка меню запуска
            run_menu_btn = tk.Button(
                action_frame,
                text=self.tr["run_menu"],
                font=("Lucida Console", 8, "bold"),
                bg="#224422",
                fg="#FFFFFF",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda: self.show_run_menu(app)
            )
            run_menu_btn.pack(side="left", padx=3)
        else:
            # Кнопка установки (если доступна для платформы)
            if sys.platform != "win32" or (sys.platform == "win32" and app["name"] not in ["MUSM", "Lifus"]):
                install_btn = tk.Button(
                    action_frame,
                    text=self.tr["install"],
                    font=("Lucida Console", 8, "bold"),
                    bg="#224422",
                    fg="#FFFFFF",
                    relief="solid",
                    borderwidth=1,
                    padx=10,
                    pady=4,
                    cursor="hand2",
                    command=lambda: self.install_app(app)
                )
                install_btn.pack(side="left", padx=3)
        
        separator = tk.Frame(main_frame, height=1, bg="#666666")
        separator.pack(fill="x", pady=(0, 15), padx=12)
        
        # Описание приложения
        desc_frame = tk.Frame(main_frame, bg="#1A1A1A")
        desc_frame.pack(fill="x", pady=(0, 15), padx=12, ipadx=12, ipady=10)
        
        desc_label = tk.Label(
            desc_frame,
            text=app["description"],
            font=("Lucida Console", 8),
            bg="#1A1A1A",
            fg="#FFFFFF",
            wraplength=1000,
            justify="left"
        )
        desc_label.pack(anchor="w")
        
        # Информация о приложении (2 колонки)
        info_container = tk.Frame(main_frame, bg="#000000")
        info_container.pack(fill="x", pady=(0, 15), padx=12)
        
        left_info = tk.Frame(info_container, bg="#000000")
        left_info.pack(side="left", fill="both", expand=True)
        
        info_left = [
            (self.tr["author"], app["author"]),
            (self.tr["release_date"], app["release_date"]),
            (self.tr["github_stars"], str(app["stars"])),
            (self.tr["category"], app["category"])
        ]
        
        for label, value in info_left:
            row = tk.Frame(left_info, bg="#000000")
            row.pack(fill="x", pady=4)
            
            lbl = tk.Label(
                row,
                text=label + ":",
                font=("Lucida Console", 8),
                bg="#000000",
                fg="#999999"
            )
            lbl.pack(side="left")
            
            val = tk.Label(
                row,
                text=value,
                font=("Lucida Console", 8, "bold"),
                bg="#000000",
                fg="#CCCCCC"
            )
            val.pack(side="left", padx=(10, 0))
        
        right_info = tk.Frame(info_container, bg="#000000")
        right_info.pack(side="right", fill="both", expand=True)
        
        info_right = [
            (self.tr["install_path"], app["install_path"]),
            (self.tr["status"], self.tr["installed"] if app["status"] == "installed" else self.tr["not_installed"]),
            (self.tr["local_version"], app["local_version"]),
            (self.tr["update_available"], self.tr["yes"] if app.get("has_update", False) else self.tr["no"])
        ]
        
        for label, value in info_right:
            row = tk.Frame(right_info, bg="#000000")
            row.pack(fill="x", pady=4)
            
            lbl = tk.Label(
                row,
                text=label + ":",
                font=("Lucida Console", 8),
                bg="#000000",
                fg="#999999"
            )
            lbl.pack(side="left")
            
            val = tk.Label(
                row,
                text=value,
                font=("Lucida Console", 8, "bold"),
                bg="#000000",
                fg="#CCCCCC"
            )
            val.pack(side="left", padx=(10, 0))
        
        separator2 = tk.Frame(main_frame, height=1, bg="#666666")
        separator2.pack(fill="x", pady=(0, 15), padx=12)
        
        # Заголовок для обнаруженных файлов
        files_header = tk.Frame(main_frame, bg="#000000")
        files_header.pack(fill="x", pady=(0, 10), padx=12)
        
        files_title = tk.Label(
            files_header,
            text=self.tr["detected_executable_files"],
            font=("Lucida Console", 10, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        files_title.pack(anchor="w")
        
        # Отображение обнаруженных файлов или сообщения об их отсутствии
        if app["name"] in self.detected_files and self.detected_files[app["name"]]:
            self.show_detected_files(main_frame, app)
        else:
            no_files_frame = tk.Frame(main_frame, bg="#1A1A1A")
            no_files_frame.pack(fill="x", pady=(0, 15), padx=12, ipadx=12, ipady=30)
            
            no_files_label = tk.Label(
                no_files_frame,
                text=self.tr["no_files_detected"],
                font=("Lucida Console", 8),
                bg="#1A1A1A",
                fg="#999999",
                justify="center"
            )
            no_files_label.pack()
        
        # Отступ снизу
        bottom_padding = tk.Frame(main_frame, height=30, bg="#000000")
        bottom_padding.pack(fill="x")
        
        # Добавляем обработчики событий для кнопок
        buttons_to_bind = []
        if 'releases_btn' in locals():
            buttons_to_bind.append(releases_btn)
        if 'github_btn' in locals():
            buttons_to_bind.append(github_btn)
        if 'update_btn' in locals():
            buttons_to_bind.append(update_btn)
        if 'uninstall_btn' in locals():
            buttons_to_bind.append(uninstall_btn)
        if 'detect_btn' in locals():
            buttons_to_bind.append(detect_btn)
        if 'run_menu_btn' in locals():
            buttons_to_bind.append(run_menu_btn)
        if 'install_btn' in locals():
            buttons_to_bind.append(install_btn)
        
        for btn in buttons_to_bind:
            btn.bind("<Enter>", lambda e: [self.play_sound("hover"), self.animate_widget_color(e.widget, e.widget["bg"], "#444444", steps=5, duration=50)])
            btn.bind("<Leave>", lambda e: self.animate_widget_color(e.widget, "#444444", e.widget["bg"], steps=5, duration=50))
            btn.bind("<Button-1>", lambda e: self.play_sound("click"))
    
    def show_run_menu(self, app):
        if app["name"] not in self.detected_files or not self.detected_files[app["name"]]:
            self.detect_app_files(app)
            return
        
        menu = tk.Menu(self.root, tearoff=0, bg="#1A1A1A", fg="#FFFFFF", font=("Lucida Console", 8))
        
        files = self.detected_files[app["name"]]
        
        if not files:
            menu.add_command(
                label="No executable files found",
                state="disabled"
            )
        else:
            menu.add_command(
                label=f"Run {app['name']} Executables:",
                state="disabled"
            )
            menu.add_separator()
            
            for file_info in files:
                if file_info["type"] == "py":
                    submenu = tk.Menu(menu, tearoff=0, bg="#1A1A1A", fg="#FFFFFF")
                    submenu.add_command(
                        label="Run Normally",
                        command=lambda f=file_info.copy(): self.run_file(f)
                    )
                    submenu.add_command(
                        label="Run as Administrator",
                        command=lambda f=file_info.copy(): self.run_as_admin(f)
                    )
                    submenu.add_command(
                        label="Edit Code",
                        command=lambda f=file_info.copy(): self.edit_code_file(f)
                    )
                    menu.add_cascade(
                        label=f"▶ {file_info['name']} (PY)",
                        menu=submenu
                    )
                elif file_info["type"] == "exe":
                    submenu = tk.Menu(menu, tearoff=0, bg="#1A1A1A", fg="#FFFFFF")
                    submenu.add_command(
                        label="Run Normally",
                        command=lambda f=file_info.copy(): self.run_file(f)
                    )
                    submenu.add_command(
                        label="Run as Administrator",
                        command=lambda f=file_info.copy(): self.run_as_admin(f)
                    )
                    menu.add_cascade(
                        label=f"▶ {file_info['name']} (EXE)",
                        menu=submenu
                    )
                else:
                    menu.add_command(
                        label=f"▶ {file_info['name']} ({file_info['type'].upper()})",
                        command=lambda f=file_info.copy(): self.run_file(f)
                    )
        
        menu.add_separator()
        menu.add_command(
            label="Refresh File List",
            command=lambda: self.detect_app_files(app)
        )
        menu.add_command(
            label="Open Installation Folder",
            command=lambda: self.open_folder(Path(app["install_path"]))
        )
        
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()
    
    def edit_code_file(self, file_info):
        if file_info["type"] != "py":
            messagebox.showinfo("Info", "Only Python (.py) files can be edited.")
            return
        
        editor = CodeEditor(self.root, file_info["path"])
        editor.show()
    
    def run_as_admin(self, file_info):
        if sys.platform != "win32":
            messagebox.showinfo("Info", "Run as Administrator is only available on Windows.")
            return self.run_file(file_info)
        
        def run_task():
            try:
                file_path = file_info["path"]
                file_type = file_info["type"]
                file_name = file_info["name"]
                file_dir = os.path.dirname(file_path)
                
                if sys.platform == "win32":
                    import ctypes
                    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
                    
                    if not is_admin:
                        if file_type == "py":
                            ctypes.windll.shell32.ShellExecuteW(
                                None, "runas", sys.executable, 
                                f'"{file_path}"', None, 1
                            )
                        elif file_type == "exe":
                            ctypes.windll.shell32.ShellExecuteW(
                                None, "runas", file_path, 
                                None, None, 1
                            )
                    else:
                        self.run_file(file_info)
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Info",
                    f"Attempting to run {file_name} as Administrator..."
                ))
                        
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to run as Administrator:\n{str(e)}"
                ))
        
        self.add_task(run_task)
    
    def show_releases(self, app):
        if not hasattr(self, "right_panel") or not self.right_panel:
            return
        
        self.current_app = app
        
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        main_canvas = tk.Canvas(self.right_panel, bg="#000000", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.right_panel, orient="vertical", command=main_canvas.yview)
        main_frame = tk.Frame(main_canvas, bg="#000000")
        
        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        top_frame = tk.Frame(main_frame, bg="#000000")
        top_frame.pack(fill="x", pady=(0, 15), padx=12)
        
        name_frame = tk.Frame(top_frame, bg="#000000")
        name_frame.pack(side="left", fill="both", expand=True)
        
        name_label = tk.Label(
            name_frame,
            text=f"{app['name']} - {self.tr['release_history']}",
            font=("Lucida Console", 16, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        name_label.pack(anchor="w")
        
        back_btn = tk.Button(
            top_frame,
            text="← " + self.tr["close"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: self.show_app_details(app)
        )
        back_btn.pack(side="right", padx=3)
        
        refresh_btn = tk.Button(
            top_frame,
            text=self.tr["refresh"],
            font=("Lucida Console", 8, "bold"),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: self.load_releases(app, main_frame)
        )
        refresh_btn.pack(side="right", padx=3)
        
        separator = tk.Frame(main_frame, height=1, bg="#666666")
        separator.pack(fill="x", pady=(0, 15), padx=12)
        
        loading_frame = tk.Frame(main_frame, bg="#1A1A1A")
        loading_frame.pack(fill="x", pady=15, padx=12, ipadx=12, ipady=35)
        
        loading_label = tk.Label(
            loading_frame,
            text=self.tr["loading_releases"] + "...",
            font=("Lucida Console", 10),
            bg="#1A1A1A",
            fg="#00FF00",
            justify="center"
        )
        loading_label.pack()
        
        self.load_releases(app, main_frame)
        
        bottom_padding = tk.Frame(main_frame, height=30, bg="#000000")
        bottom_padding.pack(fill="x")
    
    def load_releases(self, app, parent_frame):
        for widget in parent_frame.winfo_children():
            widget_name = widget.winfo_name()
            if widget_name not in ["!frame", "!frame2", "!frame3", "!frame4", "!frame5"]:
                widget.destroy()
        
        def load_task():
            try:
                releases = []
                if app.get("releases_api"):
                    releases = self.get_app_releases(app)
                
                self.root.after(0, lambda: self.display_releases(parent_frame, app, releases))
            
            except Exception as e:
                self.root.after(0, lambda: self.show_releases_error(parent_frame, str(e)))
        
        self.add_task(load_task)
    
    def get_app_releases(self, app):
        cache_key = app["name"]
        if cache_key in self.releases_cache:
            return self.releases_cache[cache_key]
        
        try:
            if not app.get("releases_api"):
                return []
                
            response = requests.get(app["releases_api"], timeout=10)
            if response.status_code == 200:
                releases = response.json()
                if isinstance(releases, list):
                    self.releases_cache[cache_key] = releases
                    return releases
                else:
                    return []
            else:
                return []
        except Exception as e:
            print(f"Error fetching releases for {app['name']}: {e}")
            return []
    
    def display_releases(self, parent_frame, app, releases):
        for widget in parent_frame.winfo_children():
            if widget.winfo_name() == "!frame" or widget.winfo_name() == "!frame2":
                continue
            widget.destroy()
        
        if not releases:
            self.show_no_releases(parent_frame)
            return
        
        releases_frame = tk.Frame(parent_frame, bg="#000000")
        releases_frame.pack(fill="x", padx=12)
        
        for i, release in enumerate(releases[:20]):
            release_frame = tk.Frame(releases_frame, bg="#1A1A1A")
            release_frame.pack(fill="x", pady=6, ipadx=12, ipady=12)
            
            header_frame = tk.Frame(release_frame, bg="#1A1A1A")
            header_frame.pack(fill="x", pady=(0, 8))
            
            version_label = tk.Label(
                header_frame,
                text=release.get("tag_name", f"Release {i+1}"),
                font=("Lucida Console", 12, "bold"),
                bg="#1A1A1A",
                fg="#FFFFFF",
                anchor="w"
            )
            version_label.pack(side="left")
            
            if release.get("prerelease", False):
                prerelease_label = tk.Label(
                    header_frame,
                    text=f" [{self.tr['prerelease']}]",
                    font=("Lucida Console", 8, "bold"),
                    bg="#1A1A1A",
                    fg="#FFAA00",
                    anchor="w"
                )
                prerelease_label.pack(side="left", padx=(4, 0))
            
            if i == 0:
                latest_label = tk.Label(
                    header_frame,
                    text=f" [{self.tr['latest']}]",
                    font=("Lucida Console", 8, "bold"),
                    bg="#1A1A1A",
                    fg="#00FF00",
                    anchor="w"
                )
                latest_label.pack(side="left", padx=(4, 0))
            
            date_frame = tk.Frame(header_frame, bg="#1A1A1A")
            date_frame.pack(side="right")
            
            date_text = release.get("published_at", "")
            if date_text:
                try:
                    date_obj = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
                    date_formatted = date_obj.strftime("%Y-%m-%d %H:%M")
                    date_label = tk.Label(
                        date_frame,
                        text=f"{self.tr['published']}: {date_formatted}",
                        font=("Lucida Console", 7),
                        bg="#1A1A1A",
                        fg="#CCCCCC"
                    )
                    date_label.pack()
                except:
                    pass
            
            if release.get("body"):
                body_text = release["body"]
                if len(body_text) > 400:
                    body_text = body_text[:400] + "..."
                
                body_label = tk.Label(
                    release_frame,
                    text=body_text,
                    font=("Lucida Console", 8),
                    bg="#1A1A1A",
                    fg="#AAAAAA",
                    wraplength=900,
                    justify="left",
                    anchor="w"
                )
                body_label.pack(fill="x", pady=(0, 8))
            
            assets = release.get("assets", [])
            if assets:
                assets_frame = tk.Frame(release_frame, bg="#1A1A1A")
                assets_frame.pack(fill="x", pady=(0, 8))
                
                assets_label = tk.Label(
                    assets_frame,
                    text=f"{self.tr['assets']}: {len(assets)}",
                    font=("Lucida Console", 8, "bold"),
                    bg="#1A1A1A",
                    fg="#FFFFFF",
                    anchor="w"
                )
                assets_label.pack(anchor="w", pady=(0, 4))
                
                for asset in assets[:5]:
                    asset_frame = tk.Frame(assets_frame, bg="#2A2A2A")
                    asset_frame.pack(fill="x", pady=2, ipadx=8, ipady=4)
                    
                    asset_name = asset.get("name", "Unknown")
                    asset_size = asset.get("size", 0)
                    
                    size_mb = asset_size / (1024 * 1024)
                    size_text = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{asset_size / 1024:.2f} KB"
                    
                    name_label = tk.Label(
                        asset_frame,
                        text=asset_name,
                        font=("Lucida Console", 7, "bold"),
                        bg="#2A2A2A",
                        fg="#CCCCCC",
                        anchor="w"
                    )
                    name_label.pack(side="left", padx=(4, 0))
                    
                    size_label = tk.Label(
                        asset_frame,
                        text=f" ({size_text})",
                        font=("Lucida Console", 7),
                        bg="#2A2A2A",
                        fg="#888888",
                        anchor="w"
                    )
                    size_label.pack(side="left", padx=(4, 0))
                    
                    download_btn = tk.Button(
                        asset_frame,
                        text=self.tr["download"],
                        font=("Lucida Console", 7),
                        bg="#222222",
                        fg="#00AAFF",
                        relief="solid",
                        borderwidth=1,
                        padx=6,
                        pady=2,
                        cursor="hand2",
                        command=lambda url=asset.get("browser_download_url", ""): webbrowser.open(url)
                    )
                    download_btn.pack(side="right", padx=(0, 4))
            
            buttons_frame = tk.Frame(release_frame, bg="#1A1A1A")
            buttons_frame.pack(fill="x")
            
            if release.get("html_url"):
                github_btn = tk.Button(
                    buttons_frame,
                    text=self.tr["github"],
                    font=("Lucida Console", 7, "bold"),
                    bg="#222222",
                    fg="#FFFFFF",
                    relief="solid",
                    borderwidth=1,
                    padx=8,
                    pady=2,
                    cursor="hand2",
                    command=lambda url=release["html_url"]: webbrowser.open(url)
                )
                github_btn.pack(side="left", padx=(0, 4))
            
            if release.get("zipball_url"):
                source_btn = tk.Button(
                    buttons_frame,
                    text=self.tr["download"] + " (Source)",
                    font=("Lucida Console", 7),
                    bg="#222222",
                    fg="#00FF00",
                    relief="solid",
                    borderwidth=1,
                    padx=8,
                    pady=2,
                    cursor="hand2",
                    command=lambda url=release["zipball_url"]: webbrowser.open(url)
                )
                source_btn.pack(side="left", padx=(0, 4))
    
    def show_no_releases(self, parent_frame):
        for widget in parent_frame.winfo_children():
            if widget.winfo_name() == "!frame" or widget.winfo_name() == "!frame2":
                continue
            widget.destroy()
        
        no_releases_frame = tk.Frame(parent_frame, bg="#1A1A1A")
        no_releases_frame.pack(fill="x", pady=30, padx=12, ipadx=12, ipady=35)
        
        no_releases_label = tk.Label(
            no_releases_frame,
            text=self.tr["no_releases"],
            font=("Lucida Console", 10),
            bg="#1A1A1A",
            fg="#FF5555",
            justify="center"
        )
        no_releases_label.pack()
    
    def show_releases_error(self, parent_frame, error_msg):
        for widget in parent_frame.winfo_children():
            if widget.winfo_name() == "!frame" or widget.winfo_name() == "!frame2":
                continue
            widget.destroy()
        
        error_frame = tk.Frame(parent_frame, bg="#1A1A1A")
        error_frame.pack(fill="x", pady=30, padx=12, ipadx=12, ipady=25)
        
        error_label = tk.Label(
            error_frame,
            text=f"{self.tr['error']}: {error_msg}",
            font=("Lucida Console", 8),
            bg="#1A1A1A",
            fg="#FF5555",
            justify="center"
        )
        error_label.pack()
        
        retry_btn = tk.Button(
            error_frame,
            text=self.tr["refresh"],
            font=("Lucida Console", 8, "bold"),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=lambda: self.load_releases(self.current_app, parent_frame)
        )
        retry_btn.pack(pady=8)
    
    def show_detected_files(self, parent_frame, app):
        files = self.detected_files.get(app["name"], [])
        
        files_container = tk.Frame(parent_frame, bg="#000000")
        files_container.pack(fill="x", pady=(0, 15), padx=12)
        
        for file_info in files:
            file_frame = tk.Frame(files_container, bg="#1A1A1A")
            file_frame.pack(fill="x", pady=3, ipadx=10, ipady=6)
            
            type_icon = "EXE" if file_info["type"] == "exe" else "BAT" if file_info["type"] == "bat" else "PY" if file_info["type"] == "py" else "SH" if file_info["type"] == "sh" else "CMD"
            icon_label = tk.Label(
                file_frame,
                text=type_icon,
                font=("Lucida Console", 7, "bold"),
                bg="#333333",
                fg="#FFFFFF",
                padx=5,
                pady=1,
                relief="solid",
                borderwidth=1
            )
            icon_label.pack(side="left", padx=(0, 10))
            
            info_frame = tk.Frame(file_frame, bg="#1A1A1A")
            info_frame.pack(side="left", fill="both", expand=True)
            
            name_label = tk.Label(
                info_frame,
                text=file_info["name"],
                font=("Lucida Console", 8, "bold"),
                bg="#1A1A1A",
                fg="#FFFFFF",
                anchor="w"
            )
            name_label.pack(fill="x")
            
            path_text = f"Path: {file_info['rel_path']}"
            size_mb = file_info["size"] / (1024 * 1024)
            size_text = f"Size: {size_mb:.2f} MB" if size_mb >= 0.01 else f"Size: {file_info['size']} bytes"
            
            details_label = tk.Label(
                info_frame,
                text=f"{path_text} | {size_text}",
                font=("Lucida Console", 6),
                bg="#1A1A1A",
                fg="#999999",
                anchor="w"
            )
            details_label.pack(fill="x")
            
            if file_info["type"] == "py":
                edit_btn = tk.Button(
                    file_frame,
                    text="EDIT",
                    font=("Lucida Console", 7, "bold"),
                    bg="#222266",
                    fg="#FFFFFF",
                    relief="solid",
                    borderwidth=1,
                    padx=8,
                    pady=2,
                    cursor="hand2",
                    command=lambda f=file_info.copy(): self.edit_code_file(f)
                )
                edit_btn.pack(side="right", padx=(0, 6))
            
            run_btn = tk.Button(
                file_frame,
                text=self.tr["run"],
                font=("Lucida Console", 7, "bold"),
                bg="#222222",
                fg="#00FF00",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=2,
                cursor="hand2",
                command=lambda f=file_info.copy(): self.run_file(f)
            )
            run_btn.pack(side="right", padx=(0, 6))
            
            if sys.platform == "win32" and file_info["type"] in ["exe", "py"]:
                admin_btn = tk.Button(
                    file_frame,
                    text="ADMIN",
                    font=("Lucida Console", 7),
                    bg="#442222",
                    fg="#FFFFFF",
                    relief="solid",
                    borderwidth=1,
                    padx=8,
                    pady=2,
                    cursor="hand2",
                    command=lambda f=file_info.copy(): self.run_as_admin(f)
                )
                admin_btn.pack(side="right", padx=(0, 6))
            
            folder_btn = tk.Button(
                file_frame,
                text=self.tr["open_folder"],
                font=("Lucida Console", 7),
                bg="#222222",
                fg="#FFFFFF",
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=2,
                cursor="hand2",
                command=lambda f=file_info: self.open_folder(Path(f["path"]).parent)
            )
            folder_btn.pack(side="right", padx=3)
    
    def detect_app_files(self, app):
        def detect_task():
            if not os.path.exists(app["install_path"]):
                self.root.after(0, lambda: messagebox.showerror(
                    self.tr["error"],
                    f"Installation folder not found:\n{app['install_path']}"
                ))
                return
            
            files = self.find_executable_files(app["install_path"])
            
            if not files:
                self.root.after(0, lambda: messagebox.showinfo(
                    self.tr["info"],
                    f"No executable files found in:\n{app['install_path']}"
                ))
                return
            
            self.detected_files[app["name"]] = files
            self.prog_info.update_executable_files(app["name"], files)
            
            self.root.after(0, lambda: messagebox.showinfo(
                self.tr["info"],
                f"Found {len(files)} executable file(s) in {app['name']}"
            ))
            
            self.root.after(0, lambda: self.show_app_details(app))
        
        self.add_task(detect_task)
    
    def run_file(self, file_info):
        def run_task():
            try:
                file_path = file_info["path"]
                file_type = file_info["type"]
                file_name = file_info["name"]
                file_dir = os.path.dirname(file_path)
                
                print(f"DEBUG: Running {file_name} from {file_dir}")
                
                original_cwd = os.getcwd()
                
                try:
                    os.chdir(file_dir)
                    print(f"DEBUG: Changed to directory: {os.getcwd()}")
                    
                    if file_type == "dll":
                        self.root.after(0, lambda: messagebox.showinfo(
                            self.tr["info"],
                            f"DLL file {file_name} cannot be executed directly.\n\n"
                            f"File path: {file_path}"
                        ))
                        return
                    
                    if sys.platform == "win32":
                        if file_type == "exe":
                            os.system(f'"{file_name}"')
                        elif file_type in ["bat", "cmd"]:
                            os.system(f'start cmd /k "{file_name}"')
                        elif file_type == "py":
                            os.system(f'python "{file_name}"')
                        elif file_type == "ps1":
                            os.system(f'powershell -ExecutionPolicy Bypass -File "{file_name}"')
                        else:
                            os.system(f'"{file_name}"')
                    
                    elif sys.platform == "darwin":
                        if file_type in ["sh", "command"]:
                            os.chmod(file_path, 0o755)
                            os.system(f'open -a Terminal "{file_name}"')
                        elif file_type == "py":
                            os.system(f'python3 "{file_name}"')
                        else:
                            os.system(f'open "{file_name}"')
                            
                    else:
                        if file_type in ["sh"]:
                            os.chmod(file_path, 0o755)
                            os.system(f'bash "{file_name}"')
                        elif file_type == "py":
                            os.system(f'python3 "{file_name}"')
                        else:
                            os.system(f'./"{file_name}"')
                    
                    self.root.after(0, lambda: messagebox.showinfo(
                        self.tr["info"],
                        f"Starting {file_name}..."
                    ))
                        
                except Exception as inner_e:
                    raise inner_e
                finally:
                    os.chdir(original_cwd)
                    print(f"DEBUG: Returned to directory: {os.getcwd()}")
                        
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    self.tr["error"],
                    f"Failed to start {file_info['name']}:\n{str(e)}\n\n"
                    f"File path: {file_path}\n"
                    f"File type: {file_type}"
                ))
        
        self.add_task(run_task)
    
    def open_folder(self, path):
        def open_task():
            try:
                path_str = str(path)
                if sys.platform == "win32":
                    os.startfile(path_str)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path_str])
                else:
                    subprocess.Popen(["xdg-open", path_str])
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    self.tr["error"],
                    f"Failed to open folder:\n{str(e)}"
                ))
        
        self.add_task(open_task)
    
    def download_github_repo(self, app, progress_callback=None, log_callback=None):
        try:
            if log_callback:
                log_callback(f"Starting download from: {app['download_url']}")
            
            response = requests.get(app["download_url"], stream=True, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Failed to download. HTTP {response.status_code}")
            
            total_size = int(response.headers.get("content-length", 0))
            
            if log_callback:
                log_callback(f"Total size: {total_size / (1024*1024):.2f} MB")
            
            temp_zip_path = self.temp_dir / f"{app['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            downloaded = 0
            chunk_size = 8192
            
            with open(temp_zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress_callback(percent, f"Downloading... {downloaded/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB")
            
            if log_callback:
                log_callback(f"Download completed: {temp_zip_path}")
                log_callback(f"File size: {os.path.getsize(temp_zip_path) / (1024*1024):.2f} MB")
            
            return str(temp_zip_path)
        
        except Exception as e:
            if log_callback:
                log_callback(f"Download error: {str(e)}")
            raise
    
    def extract_zip_file(self, zip_path, extract_to, app, progress_callback=None, log_callback=None):
        try:
            if log_callback:
                log_callback(f"Extracting archive to: {extract_to}")
            
            os.makedirs(extract_to, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                if log_callback:
                    log_callback(f"Found {total_files} files in archive")
                
                for i, filename in enumerate(file_list):
                    try:
                        zip_ref.extract(filename, extract_to)
                        
                        if progress_callback:
                            percent = (i + 1) / total_files * 100
                            progress_callback(percent, f"Extracting... {i+1}/{total_files} files")
                    
                    except Exception as e:
                        if log_callback:
                            log_callback(f"Error extracting {filename}: {str(e)}")
            
            if log_callback:
                log_callback("Extraction completed successfully")
            
            extracted_items = os.listdir(extract_to)
            
            if len(extracted_items) == 1:
                inner_path = os.path.join(extract_to, extracted_items[0])
                if os.path.isdir(inner_path):
                    if log_callback:
                        log_callback(f"Moving files from: {inner_path}")
                    
                    for item in os.listdir(inner_path):
                        src = os.path.join(inner_path, item)
                        dst = os.path.join(extract_to, item)
                        shutil.move(src, dst)
                    
                    shutil.rmtree(inner_path)
            
            return True
        
        except Exception as e:
            if log_callback:
                log_callback(f"Extraction error: {str(e)}")
            raise
    
    def install_app(self, app):
        if sys.platform == "win32" and app["name"] in ["MUSM", "Lifus"]:
            messagebox.showwarning(
                self.tr["warning"],
                f"{app['name']} is not available for installation on Windows.\n\n"
                f"This application is only available for Linux systems."
            )
            return
        
        response = messagebox.askyesno(
            self.tr["install"],
            f"Install {app['name']}?\n\n"
            f"Application will be downloaded from GitHub and installed to:\n{app['install_path']}\n\n"
            f"Note: This will download the entire repository (~few MB)"
        )
        
        if not response:
            return
        
        progress_window = tk.Toplevel(self.root)
        progress_window.title(f"{self.tr['installing']} {app['name']}")
        progress_window.geometry("600x350")
        progress_window.configure(bg="#000000")
        progress_window.resizable(False, False)
        
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        title_label = tk.Label(
            progress_window,
            text=f"{self.tr['installing'].upper()} {app['name'].upper()}",
            font=("Lucida Console", 12, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        title_label.pack(pady=(12, 6))
        
        source_label = tk.Label(
            progress_window,
            text=f"Source: {app['download_url']}",
            font=("Lucida Console", 7),
            bg="#000000",
            fg="#CCCCCC"
        )
        source_label.pack(pady=(0, 6))
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window,
            variable=progress_var,
            maximum=100,
            length=540
        )
        progress_bar.pack(pady=6)
        
        self.status_label = tk.Label(
            progress_window,
            text=self.tr["preparing_download"],
            font=("Lucida Console", 8),
            bg="#000000",
            fg="#00FF00"
        )
        self.status_label.pack(pady=3)
        
        self.detail_label = tk.Label(
            progress_window,
            text="",
            font=("Lucida Console", 7),
            bg="#000000",
            fg="#CCCCCC"
        )
        self.detail_label.pack(pady=3)
        
        console_frame = tk.Frame(progress_window, bg="#1A1A1A")
        console_frame.pack(fill="both", expand=True, padx=35, pady=6)
        
        console_text = scrolledtext.ScrolledText(
            console_frame,
            height=5,
            bg="#1A1A1A",
            fg="#00FF00",
            font=("Lucida Console", 6),
            relief="solid",
            borderwidth=1
        )
        console_text.pack(fill="both", expand=True)
        
        def log_message(message):
            console_text.insert("end", f"> {message}\n")
            console_text.see("end")
            progress_window.update()
        
        def update_progress(percent, detail=""):
            progress_var.set(percent)
            if detail:
                self.detail_label.config(text=detail)
            progress_window.update()
        
        def real_installation():
            try:
                log_message("Starting download from GitHub...")
                self.status_label.config(text=self.tr["downloading_from_github"])
                
                zip_path = self.download_github_repo(
                    app, 
                    progress_callback=lambda p, d: update_progress(p * 0.6, d),
                    log_callback=log_message
                )
                
                log_message(f"Download completed: {zip_path}")
                
                self.status_label.config(text=self.tr["extracting_files"])
                update_progress(60, "Preparing to extract...")
                
                extract_temp_dir = self.temp_dir / f"extract_{app['name']}"
                
                self.extract_zip_file(
                    zip_path,
                    str(extract_temp_dir),
                    app,
                    progress_callback=lambda p, d: update_progress(60 + p * 0.2, d),
                    log_callback=log_message
                )
                
                log_message(f"Extraction completed to: {extract_temp_dir}")
                
                self.status_label.config(text=self.tr["copying_files"])
                update_progress(80, "Copying files to installation directory...")
                
                if os.path.exists(app["install_path"]):
                    shutil.rmtree(app["install_path"])
                
                os.makedirs(app["install_path"], exist_ok=True)
                
                for item in os.listdir(extract_temp_dir):
                    src = os.path.join(extract_temp_dir, item)
                    dst = os.path.join(app["install_path"], item)
                    
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                
                log_message(f"Files copied to: {app['install_path']}")
                
                self.status_label.config(text=self.tr["creating_launchers"])
                update_progress(90, "Creating launcher files...")
                
                self.create_launcher_files(app)
                
                self.status_label.config(text=self.tr["finalizing"])
                update_progress(95, "Updating configuration...")
                
                app["status"] = "installed"
                version_to_use = app.get("latest_version", app["version"])
                app["local_version"] = self.get_local_version(app["name"])
                
                self.prog_info.update_program_status(app["name"], "installed", app["install_path"])
                self.prog_info.update_program_version(app["name"], version_to_use.replace("v", ""))
                
                self.app_config.setdefault("installed_apps", {})[app["name"]] = {
                    "version": version_to_use.replace("v", ""),
                    "install_path": app["install_path"],
                    "install_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source_url": app["download_url"]
                }
                self.save_config()
                
                files = self.find_executable_files(app["install_path"])
                self.detected_files[app["name"]] = files
                self.prog_info.update_executable_files(app["name"], files)
                
                try:
                    if os.path.exists(zip_path):
                        os.remove(zip_path)
                    if os.path.exists(extract_temp_dir):
                        shutil.rmtree(extract_temp_dir)
                    log_message("Temporary files cleaned up")
                except:
                    pass
                
                update_progress(100, "Installation complete!")
                self.status_label.config(text=self.tr["installation_complete"])
                log_message("Installation completed successfully!")
                
                import time
                time.sleep(1)
                
                self.root.after(0, progress_window.destroy)
                
                self.root.after(0, lambda: messagebox.showinfo(
                    self.tr["success"],
                    f"{app['name']} has been installed successfully!\n\n"
                    f"Location: {app['install_path']}\n"
                    f"Files: {len(files)} executable files found\n"
                    f"Click '{self.tr['detect_files']}' to see all available executables."
                ))
                
                self.root.after(0, self.display_apps_list)
                self.root.after(0, lambda: self.show_app_details(app))
                self.root.after(0, self.update_stats)
            
            except Exception as e:
                log_message(f"ERROR: {str(e)}")
                self.status_label.config(text=self.tr["installation_failed"])
                self.detail_label.config(text=f"Error: {str(e)}")
                
                self.root.after(0, lambda: tk.Button(
                    progress_window,
                    text=self.tr["view_error_details"],
                    font=("Lucida Console", 7),
                    bg="#442222",
                    fg="#FFFFFF",
                    relief="solid",
                    borderwidth=1,
                    command=lambda: self.show_error_details(str(e), console_text.get("1.0", "end"))
                ).pack(pady=6))
        
        thread = threading.Thread(target=real_installation, daemon=True)
        thread.start()
    
    def create_launcher_files(self, app):
        if sys.platform == "win32":
            ext = ".bat"
            content = f"""@echo off
chcp 65001 >nul
title {app['name']} - Launcher
color 07

echo ========================================
echo        {app['name']}
echo ========================================
echo.
echo Installed via WMR Group Apps
echo Version: {app.get('local_version', 'unknown')}
echo Install date: {datetime.now().strftime('%Y-%m-%d')}
echo.
echo Looking for executable files...
echo.

set EXE_FOUND=0

for %%f in (*.exe) do (
    echo Found: %%f
    echo.
    echo To run: %%f
    set EXE_FOUND=1
)

for %%f in (*.bat) do (
    if not "%%f"=="%~nx0" (
        echo Found: %%f
        echo.
        echo To run: %%f
        set EXE_FOUND=1
    )
)

for %%f in (*.py) do (
    echo Found: %%f
    echo.
    echo To run: python "%%f"
    set EXE_FOUND=1
)

if %EXE_FOUND%==0 (
    echo No executable files found.
    echo.
    echo Available files in this directory:
    dir /b
)

echo.
echo ========================================
pause
"""
        elif sys.platform == "darwin":
            ext = ".command"
            content = f"""#!/bin/bash
echo "========================================"
echo "        {app['name']}"
echo "========================================"
echo ""
echo "Installed via WMR Group Apps"
echo "Version: {app.get('local_version', 'unknown')}"
echo "Install date: {datetime.now().strftime('%Y-%m-%d')}"
echo ""
echo "Looking for executable files..."
echo ""

EXE_FOUND=0

for file in *.app; do
    if [ -f "$file" ]; then
        echo "Found: $file"
        echo ""
        echo "To run: open '$file'"
        EXE_FOUND=1
    fi
done

for file in *.sh *.command; do
    if [ -f "$file" ]; then
        echo "Found: $file"
        echo ""
        echo "To run: ./'$file'"
        EXE_FOUND=1
    fi
done

for file in *.py; do
    if [ -f "$file" ]; then
        echo "Found: $file"
        echo ""
        echo "To run: python3 '$file'"
        EXE_FOUND=1
    fi
done

if [ $EXE_FOUND -eq 0 ]; then
    echo "No executable files found."
    echo ""
    echo "Available files in this directory:"
    ls -la
fi

echo ""
echo "========================================"
read -p "Press Enter to continue..."
"""
        else:
            ext = ".sh"
            content = f"""#!/bin/bash
echo "========================================"
echo "        {app['name']}"
echo "========================================"
echo ""
echo "Installed via WMR Group Apps"
echo "Version: {app.get('local_version', 'unknown')}"
echo "Install date: {datetime.now().strftime('%Y-%m-%d')}"
echo ""
echo "Looking for executable files..."
echo ""

EXE_FOUND=0

for file in *.exe *.bin; do
    if [ -f "$file" ]; then
        echo "Found: $file"
        echo ""
        echo "To run: ./'$file'"
        EXE_FOUND=1
    fi
done

for file in *.sh; do
    if [ -f "$file" ]; then
        echo "Found: $file"
        echo ""
        echo "To run: ./'$file'"
        EXE_FOUND=1
    fi
done

for file in *.py; do
    if [ -f "$file" ]; then
        echo "Found: $file"
        echo ""
        echo "To run: python3 '$file'"
        EXE_FOUND=1
    fi
done

if [ $EXE_FOUND -eq 0 ]; then
    echo "No executable files found."
    echo ""
    echo "Available files in this directory:"
    ls -la
fi

echo ""
echo "========================================"
read -p "Press Enter to continue..."
"""
        
        launcher_path = os.path.join(app["install_path"], f"LAUNCH_{app['name'].replace(' ', '_')}{ext}")
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        if sys.platform != "win32":
            os.chmod(launcher_path, 0o755)
    
    def show_error_details(self, error_message, console_log):
        error_window = tk.Toplevel(self.root)
        error_window.title(self.tr["installation_error"])
        error_window.geometry("700x400")
        error_window.configure(bg="#000000")
        
        error_label = tk.Label(
            error_window,
            text=self.tr["installation_error"],
            font=("Lucida Console", 12, "bold"),
            bg="#000000",
            fg="#FF0000"
        )
        error_label.pack(pady=12)
        
        error_text = scrolledtext.ScrolledText(
            error_window,
            bg="#1A1A1A",
            fg="#FF8888",
            font=("Lucida Console", 7),
            height=12
        )
        error_text.pack(fill="both", expand=True, padx=12, pady=6)
        
        error_info = f"""ERROR MESSAGE:
{error_message}

CONSOLE LOG:
{console_log}

TROUBLESHOOTING:
1. Check your internet connection
2. Verify GitHub URL is accessible
3. Try manual download from: {self.current_app['github_url'] if hasattr(self, 'current_app') else 'N/A'}
4. Check available disk space
5. Run as administrator if needed
"""
        
        error_text.insert("1.0", error_info)
        error_text.configure(state="disabled")
        
        close_btn = tk.Button(
            error_window,
            text=self.tr["close"],
            font=("Lucida Console", 8),
            bg="#222222",
            fg="#FFFFFF",
            relief="solid",
            borderwidth=1,
            padx=20,
            pady=6,
            command=error_window.destroy
        )
        close_btn.pack(pady=12)
    
    def update_ui_after_check(self):
        self.display_apps_list()
        if hasattr(self, "current_app") and self.current_app:
            self.show_app_details(self.current_app)
        self.update_stats()
    
    def update_app(self, app):
        if not app.get("has_update", False):
            messagebox.showinfo(self.tr["info"], self.tr["no_update"])
            return
        
        response = messagebox.askyesno(
            self.tr["update_to"],
            f"Update {app['name']} from {app['local_version']} to {app['latest_version']}?\n\n"
            f"Update information will be fetched from GitHub."
        )
        
        if not response:
            return
        
        app["local_version"] = app["latest_version"]
        app["has_update"] = False
        
        version_without_v = app["latest_version"].replace("v", "")
        self.prog_info.update_program_version(app["name"], version_without_v)
        self.prog_info.set_update_available(app["name"], False)
        
        if app["name"] in self.app_config.get("installed_apps", {}):
            self.app_config["installed_apps"][app["name"]]["version"] = version_without_v
            self.app_config["installed_apps"][app["name"]]["update_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_config()
        
        self.display_apps_list()
        self.show_app_details(app)
        self.update_stats()
        
        messagebox.showinfo(
            self.tr["success"],
            f"{app['name']} has been updated to {app['latest_version']}!"
        )
    
    def uninstall_app(self, app):
        response = messagebox.askyesno(
            self.tr["uninstall"],
            f"Are you sure you want to uninstall {app['name']}?\n\n"
            f"This will delete all files in:\n{app['install_path']}"
        )
        
        if not response:
            return
        
        def uninstall_task():
            try:
                if os.path.exists(app["install_path"]):
                    shutil.rmtree(app["install_path"])
                
                if app["name"] in self.app_config.get("installed_apps", {}):
                    del self.app_config["installed_apps"][app["name"]]
                    self.save_config()
                
                if app["name"] in self.detected_files:
                    del self.detected_files[app["name"]]
                
                app["status"] = "not_installed"
                app["local_version"] = "unknown"
                app["has_update"] = False
                
                self.prog_info.update_program_status(app["name"], "not_installed")
                self.prog_info.update_program_version(app["name"], "unknown")
                self.prog_info.set_update_available(app["name"], False)
                
                self.root.after(0, lambda: messagebox.showinfo(
                    self.tr["success"],
                    f"{app['name']} has been successfully uninstalled."
                ))
                
                self.root.after(0, lambda: self.display_apps_list())
                self.root.after(0, lambda: self.show_app_details(app))
                self.root.after(0, lambda: self.update_stats())
            
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    self.tr["error"],
                    f"Failed to uninstall {app['name']}:\n{str(e)}"
                ))
        
        self.add_task(uninstall_task)

def main():
    try:
        import tkinter
        import requests
    except ImportError as e:
        print(f"ERROR: {e}")
        print("Please install required packages:")
        print("pip install requests")
        return
    
    config = Config()
    
    root = tk.Tk()
    app = WMRGroupApps(root, config)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.resizable(True, True)
    
    root.mainloop()
