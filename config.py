import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "config.json"
        self.default_config = {
            "app": {
                "version": "1.1.3",
                "last_check": None,
                "auto_update": True,
                "language": None,
                "theme": "black_white"
            },
            "paths": {
                "install_dir": "install",
                "downloads_dir": "downloads",
                "temp_dir": "temp",
                "data_dir": "data"
            },
            "updater": {
                "repo_url": "https://api.github.com/repos/WMR-Group/WMR-GROUP-APPS/releases/latest",
                "update_file_url": "https://raw.githubusercontent.com/WMR-Group/WMR-GROUP-APPS/main/update.txt",
                "changelog_url": "https://raw.githubusercontent.com/WMR-Group/WMR-GROUP-APPS/main/changelog.txt",
                "check_interval": 86400,
                "enabled": True
            },
            "ui": {
                "window_size": "1400x800",
                "font_family": "Lucida Console",
                "font_size": 10,
                "sound_effects": True
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    return self.merge_configs(self.default_config, loaded)
            except:
                return self.default_config.copy()
        return self.default_config.copy()
    
    def merge_configs(self, default, loaded):
        for key in default:
            if key in loaded and isinstance(default[key], dict) and isinstance(loaded[key], dict):
                default[key] = self.merge_configs(default[key], loaded[key])
            elif key in loaded:
                default[key] = loaded[key]
        return default
    
    def save_config(self):
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split(".")
        config = self.config
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def get_language(self):
        lang = self.get("app.language")
        if not lang:
            import locale
            try:
                system_lang = locale.getdefaultlocale()[0]
                if system_lang and "ru" in system_lang.lower():
                    lang = "ru"
                else:
                    lang = "en"
            except:
                lang = "en"
            self.set("app.language", lang)
        return lang
    
    def get_install_path(self):
        path = Path(self.get("paths.install_dir"))
        if not path.is_absolute():
            path = self.base_dir / path
        return path
    
    def get_downloads_path(self):
        path = Path(self.get("paths.downloads_dir"))
        if not path.is_absolute():
            path = self.base_dir / path
        return path
    
    def get_temp_path(self):
        path = Path(self.get("paths.temp_dir"))
        if not path.is_absolute():
            path = self.base_dir / path
        return path
    
    def get_data_path(self):
        path = Path(self.get("paths.data_dir", "data"))
        if not path.is_absolute():
            path = self.base_dir / path
        return path
    
    def get_sound_effects(self):
        return self.get("ui.sound_effects", True)
    
    def set_sound_effects(self, enabled):
        self.set("ui.sound_effects", enabled)