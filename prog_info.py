import json
import os
from datetime import datetime
from pathlib import Path

class ProgramInfo:
    def __init__(self, config=None):
        self.config = config
        if config:
            self.data_dir = config.get_data_path()
        else:
            self.data_dir = Path(__file__).parent / "data"
        
        self.data_dir.mkdir(exist_ok=True)
        self.info_file = self.data_dir / "programs_info.json"
        self.default_info = {
            "last_update": datetime.now().isoformat(),
            "programs": {
                "WALMFAST": {
                    "name": "WALMFAST",
                    "current_version": "1.0.0",
                    "latest_version": "1.0.0",
                    "last_checked": None,
                    "last_updated": None,
                    "install_path": None,
                    "file_count": 0,
                    "executable_files": [],
                    "status": "not_installed",
                    "update_available": False
                },
                "Wlap-FlashTool": {
                    "name": "Wlap Flash Tool",
                    "current_version": "1.0.4.0",
                    "latest_version": "1.0.4.0",
                    "last_checked": None,
                    "last_updated": None,
                    "install_path": None,
                    "file_count": 0,
                    "executable_files": [],
                    "status": "not_installed",
                    "update_available": False
                },
                "NightAuroraZIP": {
                    "name": "NightAurora ZIP",
                    "current_version": "V1.0",
                    "latest_version": "V1.0",
                    "last_checked": None,
                    "last_updated": None,
                    "install_path": None,
                    "file_count": 0,
                    "executable_files": [],
                    "status": "not_installed",
                    "update_available": False
                },
                "deltarune-translator": {
                    "name": "Deltarune Translator",
                    "current_version": "1.0.0",
                    "latest_version": "1.0.0",
                    "last_checked": None,
                    "last_updated": None,
                    "install_path": None,
                    "file_count": 0,
                    "executable_files": [],
                    "status": "not_installed",
                    "update_available": False
                },
                "musm": {
                    "name": "MUSM",
                    "current_version": "1.0.0",
                    "latest_version": "1.0.0",
                    "last_checked": None,
                    "last_updated": None,
                    "install_path": None,
                    "file_count": 0,
                    "executable_files": [],
                    "status": "not_installed",
                    "update_available": False
                },
                "wayset": {
                    "name": "Wayset",
                    "current_version": "1.0.0",
                    "latest_version": "1.0.0",
                    "last_checked": None,
                    "last_updated": None,
                    "install_path": None,
                    "file_count": 0,
                    "executable_files": [],
                    "status": "not_installed",
                    "update_available": False
                },
                "lifus": {
                    "name": "Lifus",
                    "current_version": "1.0.0",
                    "latest_version": "1.0.0",
                    "last_checked": None,
                    "last_updated": None,
                    "install_path": None,
                    "file_count": 0,
                    "executable_files": [],
                    "status": "not_installed",
                    "update_available": False
                }
            }
        }
        self.info = self.load_info()
    
    def load_info(self):
        if self.info_file.exists():
            try:
                with open(self.info_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    return self.merge_info(self.default_info, loaded)
            except:
                return self.default_info.copy()
        return self.default_info.copy()
    
    def merge_info(self, default, loaded):
        for key in default:
            if key in loaded and isinstance(default[key], dict) and isinstance(loaded[key], dict):
                default[key] = self.merge_info(default[key], loaded[key])
            elif key in loaded:
                default[key] = loaded[key]
        return default
    
    def save_info(self):
        self.info["last_update"] = datetime.now().isoformat()
        with open(self.info_file, "w", encoding="utf-8") as f:
            json.dump(self.info, f, indent=2, ensure_ascii=False)
    
    def get_program_info(self, program_name):
        return self.info["programs"].get(program_name, {})
    
    def update_program_info(self, program_name, info):
        if program_name not in self.info["programs"]:
            self.info["programs"][program_name] = {}
        
        self.info["programs"][program_name].update(info)
        self.info["programs"][program_name]["last_updated"] = datetime.now().isoformat()
        self.save_info()
    
    def update_program_version(self, program_name, version):
        if program_name in self.info["programs"]:
            self.info["programs"][program_name]["current_version"] = version
            self.info["programs"][program_name]["last_updated"] = datetime.now().isoformat()
            self.save_info()
    
    def update_program_status(self, program_name, status, install_path=None):
        if program_name in self.info["programs"]:
            self.info["programs"][program_name]["status"] = status
            if install_path:
                self.info["programs"][program_name]["install_path"] = install_path
            elif status == "not_installed":
                self.info["programs"][program_name]["install_path"] = None
            self.save_info()
    
    def update_executable_files(self, program_name, files):
        if program_name in self.info["programs"]:
            self.info["programs"][program_name]["executable_files"] = files
            self.info["programs"][program_name]["file_count"] = len(files)
            self.save_info()
    
    def set_update_available(self, program_name, available, latest_version=None):
        if program_name in self.info["programs"]:
            self.info["programs"][program_name]["update_available"] = available
            if latest_version:
                self.info["programs"][program_name]["latest_version"] = latest_version
            self.info["programs"][program_name]["last_checked"] = datetime.now().isoformat()
            self.save_info()
    
    def get_all_programs_info(self):
        return self.info["programs"]
    
    def sync_from_installation(self, program_name, install_path):
        import os
        import shutil
        
        if not os.path.exists(install_path):
            self.update_program_status(program_name, "not_installed")
            self.update_executable_files(program_name, [])
            return
        
        files = []
        for root, dirs, file_list in os.walk(install_path):
            for file in file_list:
                if file.lower().endswith((".exe", ".bat", ".py", ".sh", ".command", ".ps1", ".cmd")):
                    files.append({
                        "name": file,
                        "path": os.path.join(root, file),
                        "size": os.path.getsize(os.path.join(root, file))
                    })
        
        if files:
            self.update_program_status(program_name, "installed", install_path)
        else:
            self.update_program_status(program_name, "partial", install_path)
            
        self.update_executable_files(program_name, files)
        
        version_file = os.path.join(install_path, "version.txt")
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                version = f.read().strip()
                self.update_program_version(program_name, version)
    
    def check_and_sync_all(self, base_install_path):
        for program_name in self.info["programs"]:
            install_path = os.path.join(base_install_path, program_name)
            self.sync_from_installation(program_name, install_path)