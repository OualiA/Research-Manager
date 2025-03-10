import json
import os
import logging

CONFIG_PATH = "utils/config.json"
class ConfigManager:
    def __init__(self, config_file=CONFIG_PATH):

        self.theme = None
        self.config_file = self.resource_path(config_file)
        self.root_path = None
        self.last_selected_text = "en_US"

        # Zotero Credentials
        self.library_id = None
        self.library_type = "user"
        self.api_key = None

        self.load_config()

    @staticmethod
    def resource_path(relative_path:str)-> str:
        """ Get the absolute path to a resource, works for dev and PyInstaller """
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def load_config(self) -> None:
        """Load settings from config.json"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.root_path = config.get("root_path", "")
                    self.last_selected_text = config.get("last_selected_text", "")

                    # Load Zotero credentials
                    self.library_id = config.get("library_id", "")
                    self.library_type = config.get("library_type", "user")
                    self.api_key = config.get("api_key", "")

                    # theme changes
                    self.theme = config.get("theme", "")


        except Exception as e:
            logging.error(f"Failed to load config: {e}")

    def save_config(self) -> None:
        """Save settings to config.json"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "root_path": self.root_path,
                    "last_selected_text": self.last_selected_text,
                    "library_id": self.library_id,
                    "library_type": self.library_type,
                    "api_key": self.api_key,
                    "theme": self.theme
                }, f, indent=6)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def set_last_selected_text(self, text) -> None:
        """Save last selected ComboBox item"""
        self.last_selected_text = text
        self.save_config()

    def set_zotero_credentials(self, library_id, library_type, api_key) -> None:
        """Set and save Zotero credentials"""
        self.library_id = library_id
        self.library_type = library_type
        self.api_key = api_key
        self.save_config()


    def set_theme(self, text) -> None:
        """Save last selected ComboBox item"""
        self.theme = text
        self.save_config()


