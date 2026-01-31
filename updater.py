import requests
import json
import os
import sys
import subprocess
import tempfile
import zipfile
import shutil
from datetime import datetime
from pathlib import Path
import threading
from config import Config

class Updater:
    def __init__(self, config=None):
        self.config = config or Config()
        self.repo_url = self.config.get("updater.repo_url")
        self.base_dir = Path(__file__).parent
    
    def check_for_updates(self):
        try:
            response = requests.get(self.repo_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").lstrip("v")
                latest_date = data.get("published_at", "")
                
                current_version = self.config.get("app.version", "1.0.1")
                last_check = self.config.get("app.last_check")
                
                if self.compare_versions(latest_version, current_version) > 0:
                    return {
                        "available": True,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "release_date": latest_date,
                        "download_url": data.get("html_url", ""),
                        "assets": data.get("assets", []),
                        "changelog": data.get("body", "")
                    }
            
            return {"available": False}
        
        except Exception as e:
            print(f"Update check failed: {e}")
            return {"available": False}
    
    def compare_versions(self, v1, v2):
        def parse_version(v):
            parts = v.replace("v", "").split(".")
            result = []
            for part in parts:
                try:
                    result.append(int(part))
                except:
                    result.append(0)
            return result
        
        v1_parts = parse_version(v1)
        v2_parts = parse_version(v2)
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_part = v1_parts[i] if i < len(v1_parts) else 0
            v2_part = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1_part > v2_part:
                return 1
            elif v1_part < v2_part:
                return -1
        
        return 0
    
    def download_update(self, download_url, progress_callback=None):
        try:
            if progress_callback:
                progress_callback(0, "Starting download...")
            
            response = requests.get(download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            temp_dir = Path(tempfile.gettempdir()) / "wmr_update"
            temp_dir.mkdir(exist_ok=True)
            
            zip_path = temp_dir / "update.zip"
            
            downloaded = 0
            chunk_size = 8192
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress_callback(percent, f"Downloading... {downloaded/(1024*1024):.1f} MB")
            
            if progress_callback:
                progress_callback(100, "Download complete")
            
            return zip_path
        
        except Exception as e:
            print(f"Download failed: {e}")
            return None
    
    def apply_update(self, zip_path):
        try:
            extract_dir = Path(tempfile.gettempdir()) / "wmr_update_extract"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            for item in extract_dir.iterdir():
                if item.is_dir():
                    for file in item.rglob("*"):
                        if file.is_file():
                            rel_path = file.relative_to(item)
                            target_path = self.base_dir / rel_path
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file, target_path)
            
            self.config.set("app.version", self.get_latest_version())
            self.config.set("app.last_check", datetime.now().isoformat())
            
            shutil.rmtree(extract_dir)
            os.remove(zip_path)
            
            return True
        
        except Exception as e:
            print(f"Update apply failed: {e}")
            return False
    
    def get_latest_version(self):
        try:
            response = requests.get(self.repo_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("tag_name", "").lstrip("v")
        except:
            pass
        return self.config.get("app.version", "1.0.1")
    
    def run_update_check(self, callback=None):
        def check():
            result = self.check_for_updates()
            if callback:
                callback(result)
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()