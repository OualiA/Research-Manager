import re
from PySide6.QtWidgets import QMessageBox, QApplication
from workers.article_worker import ArticleManager, SciDownloadThread
from views.table_builder import TableBuilder
from services.journal_db import JournalDB
from services.file_service import FileService
from controllers.zotero_controller import ZoteroController
from controllers.journal_controller import JournalController
from services.notification_service import NotificationServices


class ArticleController:
    def __init__(self, ui, config_manager):
        self.download_thread = None
        self.worker = None
        self.ui = ui
        self.config_manager = config_manager
        self.article_data = {}
        self.file_controller = None
        self.file_service = FileService()
        self.zotero_controller = ZoteroController(self.ui, self.config_manager)
        self.journal_controller = JournalController(self.ui)
        self.desktop_notification = NotificationServices()

        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.check_clipboard_for_doi)

    def search_articles(self, float_mode = False)-> None:
        self.clear_article_results()
        search_text = self.ui.article_info_led.text()
        mode = self.ui.search_mode_cbox.currentText()

        if not search_text.strip():
            if float_mode:
                self.desktop_notification.send_notification("Articles Section", "Please enter a valid DOI or Title!")
            else:
                self._append_article_log("Please enter a valid DOI or Title!")
            return
        download_path = self.file_controller.get_download_path()
        self._append_article_log(f"Fetching article via {mode}...")

        # Create and start the ArticleManager worker thread.
        self.worker = ArticleManager(
            download_path= download_path,
            article_doi=search_text if mode == "DOI" else None,
            article_title=search_text if mode != "DOI" else None
        )
        self.worker.result.connect(self._handle_article_result)
        self.worker.error.connect(lambda err: self._append_article_log(err))
        self.worker.error.connect(self._float_notifications)
        self.worker.start()
        if float_mode:
            self.worker.done.connect(lambda: self.download_article_pdf (float_mode = True))

    def download_article_pdf(self, float_mode:bool = False) -> None:
        """
        Downloads the article using the DOI and Title from the previously searched article.
        """
        self.ui.article_download_path_ledit.clear()
        self.ui.INFO_pltext.clear()

        if not self.article_data and not float_mode:
            QMessageBox.warning(self.ui.centralwidget, "Download Error", "Please search for an article first.")
            return

        # Use the injected file_controller to get the download path.
        download_path = self.file_controller.get_download_path()
        if not download_path:
            return  # Exit if no valid path is obtained.

        # Extract DOI and Title from the fetched article metadata.
        self.ui.article_download_path_ledit.setText(download_path)
        doi_text = self.article_data.get("DOI", "")
        title_text = self.sanitize_filename(self.article_data.get("Title", ""))

        if not doi_text:
            QMessageBox.warning(self.ui.centralwidget, "Download Error", "Article DOI is missing.")
            return


        self._append_article_log(f"Downloading article '{title_text}' to: {download_path}")

        # Create and start the download thread with the DOI and Title.
        self.download_thread = SciDownloadThread(
            download_path=download_path,
            article_doi=doi_text,
            article_title=title_text
        )
        self.download_thread.message.connect(self._append_article_log)
        self.download_thread.pdf_path.connect(self._open_download_pdf)

        #float node search
        if float_mode :
            self.download_thread.failed.connect(self._float_notifications)
            self.download_thread.success.connect(self._float_notifications)
        self.download_thread.start()
        self.download_thread.finished.connect(self._on_download_finished)

    def _on_download_finished(self) -> None:
        self._append_article_log("Process completed.")
        self.file_controller.refresh_toolbox()

    def _open_download_pdf(self, pdf_path: str) -> None:
        """Open the downloaded file automatically if enabled."""
        auto_open = self.ui.auto_open_pdf_cbox.isChecked()
        if auto_open == True and self.article_data:
            if pdf_path:
                self.file_service.open_file(pdf_path)
        else:
            return

    def _handle_article_result(self, article_data: dict) -> None:
        """Store article data and update the UI."""
        if not isinstance(article_data, dict):
            QMessageBox.critical(self.ui.centralwidget, "Error", "Invalid article data received.")
            return
        self.article_data = article_data
        TableBuilder.display_article_data(article_data, self.ui.articles_tree_qwidget.invisibleRootItem())
        self.ui.articles_tree_qwidget.expandAll()
        self._append_article_log("Article metadata fetched successfully!")

    def export_journal_info(self) -> None:
        """ Export the current article's journal information into the database and refresh the tree """

        self.ui.INFO_pltext.clear()
        if not self.article_data:
            QMessageBox.warning(self.ui.centralwidget, "Export Error", "No article data available. Please search for an article first.")
            return

        record = {
            "Journal": self.article_data.get("Journal", ""),
            "ISSN": self.article_data.get("ISSN", ""),
            "Open Access": self.article_data.get("Open Access", ""),
            "Journal Rank": "",
            "Publication Fee": "",
            "Site": ""
        }
        db = JournalDB()
        if db.get_journal_by_name(record["Journal"]):
            db.update_journal(record)
        else:
            db.save_journal(record)

        self.journal_controller.load_all_journals()
        self.desktop_notification.send_notification("Articles Section", "Journal information exported and loaded from the database.")

    def _append_article_log(self, message: str) -> None:
        self.ui.INFO_pltext.appendPlainText(message)

    def _float_notifications(self, message: str) -> None:
        self.desktop_notification.send_notification("Articles Section", message)

    def clear_article_results(self) -> None:
        self.ui.articles_tree_qwidget.clear()
        self.ui.INFO_pltext.clear()
        self.article_data.clear()

    def export_with_change_index(self) -> None:
        """ Export the current article's journal information into the database and change to the journals section """
        self.export_journal_info()
        self._append_article_log("Journal information exported and loaded from the database.")
        self.ui.journal_section_btn.setChecked(True)

    @staticmethod
    def sanitize_filename(text, replacement="_", max_length=255) -> str:
        """ Cleans text to be used as a safe filename. """
        text = re.sub(r'[\/:*?"<>|]', replacement, text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'_+', '_', text)
        return text[:max_length]

    def check_clipboard_for_doi(self) -> None:
        """Check if clipboard contains a DOI and autofill the fields."""
        clipboard_text = self.clipboard.text().strip()

        # DOI regex pattern
        doi_pattern = r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)"

        match = re.search(doi_pattern, clipboard_text)

        if match:
            doi = match.group(1)
            self.ui.article_info_led.setText(doi)
            self.ui.article_float_search_ledit.setText(doi)

    def send_to_zotero(self) -> None:
        library_id = self.ui.zotero_library_id_ledit.text().strip()
        api_key = self.ui.zotero_api_key_ledit.text().strip()
        library_type = self.ui.zotero_library_type_cbox.currentText().strip()

        try:
            if not library_id or not api_key:
                QMessageBox.warning(self.ui.centralwidget, "Zotero Error", "Library ID and API Key are required.")
                self.zotero_controller.highlight_missing_fields(not library_id, not api_key, False)
                return
            self.zotero_controller.save_zotero_credentials(library_id=library_id, library_type=library_type,
                                                           api_key=api_key)
            self.zotero_controller.add_to_zotero(article_data=self.article_data, library_id=library_id, library_type=library_type,
                                                           api_key=api_key)
        except Exception as e:
            QMessageBox.warning(self.ui.centralwidget, "Zotero Error",
                                f"error: {e}")

    def float_article_downloader(self) -> None:
        try:
            self.search_articles(float_mode = True)
        except Exception as e:
            QMessageBox.warning(self.ui.centralwidget, "Float Downloader Error", f"Error: {e}")