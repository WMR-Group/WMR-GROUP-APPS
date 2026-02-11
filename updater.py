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
        self.update_file_url = self.config.get("updater.update_file_url")
        self.changelog_url = self.config.get("updater.changelog_url")
        self.base_dir = Path(__file__).parent
    
    def check_for_updates(self):
        try:
            current_version = self.config.get("app.version", "1.1.3").replace("v", "")
            
            try:
                response = requests.get(self.repo_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data.get("tag_name", "").replace("v", "")
                    latest_date = data.get("published_at", "")
                    
                    if self.compare_versions(latest_version, current_version) > 0:
                        return {
                            "available": True,
                            "current_version": current_version,
                            "latest_version": latest_version,
                            "release_date": latest_date,
                            "download_url": data.get("html_url", ""),
                            "assets": data.get("assets", []),
                            "changelog": data.get("body", ""),
                            "source": "github_release"
                        }
            except:
                pass
            
            try:
                response = requests.get(self.update_file_url, timeout=10)
                if response.status_code == 200:
                    latest_version = response.text.strip().replace("v", "")
                    
                    if latest_version and self.compare_versions(latest_version, current_version) > 0:
                        changelog = ""
                        try:
                            changelog_response = requests.get(self.changelog_url, timeout=10)
                            if changelog_response.status_code == 200:
                                changelog = changelog_response.text
                        except:
                            pass
                        
                        return {
                            "available": True,
                            "current_version": current_version,
                            "latest_version": latest_version,
                            "release_date": datetime.now().isoformat(),
                            "download_url": f"https://github.com/WMR-Group/WMR-GROUP-APPS/releases/latest",
                            "assets": [],
                            "changelog": changelog,
                            "source": "update_file"
                        }
                else:
                    return {"available": False, "message": "Update file not found on server"}
            except:
                return {"available": False, "message": "Failed to check for updates"}
            
            return {"available": False}
        
        except Exception as e:
            print(f"Update check failed: {e}")
            return {"available": False, "message": str(e)}
    
    def compare_versions(self, v1, v2):
        def parse_version(v):
            if not v:
                return [0, 0, 0]
            parts = v.replace("v", "").split(".")
            result = []
            for part in parts[:3]:
                try:
                    result.append(int(part))
                except:
                    result.append(0)
            while len(result) < 3:
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
            
            if "github.com" in download_url and "/releases/" in download_url:
                api_url = download_url.replace("github.com", "api.github.com/repos").replace("/releases/latest", "/releases/latest")
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        assets = data.get("assets", [])
                        if assets:
                            for asset in assets:
                                if asset.get("name", "").endswith(".zip"):
                                    download_url = asset.get("browser_download_url", download_url)
                                    break
                except:
                    pass
            
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
                    update_folder = item
                    break
            else:
                update_folder = extract_dir
            
            for root, dirs, files in os.walk(update_folder):
                for file in files:
                    if file.endswith(".py") or file.endswith(".txt") or file.endswith(".json") or file.endswith(".bat") or file.endswith(".sh"):
                        src_path = Path(root) / file
                        rel_path = src_path.relative_to(update_folder)
                        target_path = self.base_dir / rel_path
                        
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        try:
                            shutil.copy2(src_path, target_path)
                        except Exception as e:
                            print(f"Error copying {src_path} to {target_path}: {e}")
            
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
            response = requests.get(self.update_file_url, timeout=10)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        try:
            response = requests.get(self.repo_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("tag_name", "").replace("v", "")
        except:
            pass
        
        return self.config.get("app.version", "1.1.3").replace("v", "")
    
    def run_update_check(self, callback=None):
        def check():
            result = self.check_for_updates()
            if callback:
                callback(result)
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    def get_changelog(self):
        try:
            response = requests.get(self.changelog_url, timeout=10)
            if response.status_code == 200:
                return response.text
        except:
            pass
        
        try:
            changelog_path = self.base_dir / "changelog.txt"
            if changelog_path.exists():
                with open(changelog_path, "r", encoding="utf-8") as f:
                    return f.read()
        except:
            pass
        
        return "Changelog not available."