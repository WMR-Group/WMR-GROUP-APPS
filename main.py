import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loading_screen import LoadingScreen
from language_selector import LanguageSelector
from app_store import main as app_store_main
from config import Config

def start_app():
    config = Config()
    
    loading_screen = LoadingScreen()
    
    def close_loading_and_start():
        loading_screen.close()
        app_store_main()
    
    loading_screen.root.after(2000, close_loading_and_start)
    loading_screen.run()

def main():
    config = Config()
    language = config.get("app.language")
    
    if not language:
        selector = LanguageSelector(start_app)
        selector.run()
    else:
        start_app()

if __name__ == "__main__":
    main()