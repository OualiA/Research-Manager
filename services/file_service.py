import os
from pathlib import Path
import subprocess
import platform

class FileService:
    def __init__(self, root_folder=""):
        self.root_folder = Path(root_folder).resolve() if root_folder else None
        #self.root_folder = root_folder
    @staticmethod
    def open_file(file_path: str) -> None:
        file_path = Path(file_path)  # Convert to pathlib Path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        system = platform.system()
        if system == "Windows":
            os.startfile(str(file_path))
        elif system == "Darwin":
            subprocess.Popen(["open", str(file_path)])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", str(file_path)])
        else:
            raise RuntimeError("Unsupported OS")

    @staticmethod
    def delete_file(file_path: str) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        Path(file_path).unlink()

    def create_folder(self, folder_name: str) -> Path:
        if not self.root_folder or not self.root_folder.is_dir():
            raise ValueError("Invalid root directory configuration")
        sanitized = self._sanitize_folder_name(folder_name)
        target = self.root_folder / sanitized
        if target.exists():
            raise FileExistsError(f"Folder already exists: {sanitized}")
        target.mkdir(parents=True, exist_ok=False)
        return target

    @staticmethod
    def _sanitize_folder_name(name: str) -> str:
        invalid = r'\/:*?"<>|'
        return name.translate({ord(c): '_' for c in invalid}).strip().rstrip('.')
