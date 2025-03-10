from PySide6.QtWidgets import QMessageBox
from pyzotero import zotero

class ZoteroController:
    def __init__(self, ui, config_manager):
        self.ui = ui
        self.config_manager = config_manager

    def add_to_zotero(self, article_data,library_id,library_type, api_key ) -> None:
        """Add the current article to Zotero using saved credentials."""
        # Connect to Zotero
        zot = zotero.Zotero(library_id, library_type, api_key)

        # Get article metadata
        if not article_data:
            QMessageBox.warning(self.ui.centralwidget, "Zotero Error", "No article data available.")
            return

        doi = article_data.get("DOI", "").strip()
        title = article_data.get("Title", "Unknown Title").strip()
        authors = article_data.get("Authors", [])
        journal = article_data.get("Journal", "Unknown Journal").strip()

        if not doi:
            QMessageBox.warning(self.ui.centralwidget, "Zotero Error", "No DOI found for the article.")
            return

        item = {
            "itemType": "journalArticle",
            "title": title,
            "creators": [{"creatorType": "author", "lastName": a.split(",")[0], "firstName": a.split(",")[-1]} for a in
                         authors],
            "publicationTitle": journal,
            "DOI": doi
        }

        try:
            zot.create_items([item])
            QMessageBox.information(self.ui.centralwidget, "Success", f"Article '{title}' added to Zotero.")
        except Exception as e:
            QMessageBox.critical(self.ui.centralwidget, "Zotero Error", f"Failed to add article to Zotero:\n{e}")

    def load_zotero_credentials(self) -> None:
        """Load Zotero credentials into UI fields if available, else highlight missing fields."""
        library_id = self.config_manager.library_id
        library_type = self.config_manager.library_type
        api_key = self.config_manager.api_key

        self.ui.zotero_library_id_ledit.setText(library_id if library_id else "")
        self.ui.zotero_api_key_ledit.setText(api_key if api_key else "")
        self.ui.zotero_library_type_cbox.setCurrentText(library_type if library_type else "user")

    def highlight_missing_fields(self, id_missing, key_missing, type_missing) -> None:
        """Highlight fields with missing credentials."""
        red_color = "border-bottom: 2px solid red; background-color: #ffd6d6;"
        normal_color = ""

        self.ui.zotero_library_id_ledit.setStyleSheet(red_color if id_missing else normal_color)
        self.ui.zotero_api_key_ledit.setStyleSheet(red_color if key_missing else normal_color)
        self.ui.zotero_library_type_cbox.setStyleSheet(red_color if type_missing else normal_color)

    def save_zotero_credentials(self, library_id:str, api_key:str, library_type:str) -> None:
        self.config_manager.set_zotero_credentials(library_id, library_type, api_key)
        self.highlight_missing_fields(False, False, False)
