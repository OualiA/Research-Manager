import os

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import QTimer
from services.config_manager import ConfigManager
from services.file_service import FileService
from views.MainUI import Ui_MainWindow



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


        self.config_manager = ConfigManager()
        self.config_manager.load_config()
        self.file_service = FileService()


        # Delay imports to avoid circular dependencies
        from controllers.file_controller import FileController
        from controllers.pdf_search_controller import PDFSearchController
        from controllers.article_controller import ArticleController
        from controllers.journal_controller import JournalController
        from controllers.zotero_controller import ZoteroController


        # Instantiate Controllers
        self.file_controller = FileController(self.ui, self.config_manager)
        self.article_controller = ArticleController(self.ui, self.config_manager)
        self.pdf_search_controller = PDFSearchController(self.ui)
        self.journal_controller = JournalController(self.ui)
        self.zotero_controller = ZoteroController(self.ui, self.config_manager)

        # Inject file_controller where needed
        self.article_controller.file_controller = self.file_controller
        self.pdf_search_controller.file_controller = self.file_controller

        # DOI listener
        self.article_controller.check_clipboard_for_doi()
        self.zotero_controller.load_zotero_credentials()

        # Load initial stylesheet
        self._apply_stylesheet(self.config_manager.theme)


        # Adjust UI based on screen resolution
        self._adjust_ui_for_resolution()

        # start the signals and the initial state
        self._connect_signals()
        self._load_initial_state()

    def _connect_signals(self) -> None:
        # Navigation signals
        self.ui.article_section_btn.toggled.connect(lambda: self.ui.MainFram.setCurrentIndexAnimated(0))
        self.ui.article_icon_section_btn.toggled.connect(lambda: self.ui.MainFram.setCurrentIndexAnimated(0))
        self.ui.pdf_section_btn.toggled.connect(lambda: self.ui.MainFram.setCurrentIndexAnimated(1))
        self.ui.pdf_icon_section_btn.toggled.connect(lambda: self.ui.MainFram.setCurrentIndexAnimated(1))
        self.ui.journal_section_btn.toggled.connect(lambda: self.ui.MainFram.setCurrentIndexAnimated(2))
        self.ui.journal_icon_section_btn.clicked.connect(lambda: self.ui.MainFram.setCurrentIndexAnimated(2))
        self.ui.file_section_btn.toggled.connect(
            lambda: self.ui.dockWidget.show() if self.ui.file_section_btn.isChecked() else self.ui.dockWidget.close())
        self.ui.file_icon_section_btn.toggled.connect(
            lambda: self.ui.dockWidget.show() if self.ui.file_icon_section_btn.isChecked() else self.ui.dockWidget.close())

        # File operations
        self.ui.refrech_toolbox_btn.clicked.connect(self.file_controller.refresh_toolbox)
        self.ui.open_directory_btn.clicked.connect(self.file_controller.open_directory)
        self.ui.delete_directory_btn.clicked.connect(self.file_controller.delete_directory)
        self.ui.create_file_btn.clicked.connect(self.file_controller.create_folder)
        self.ui.pdf_file_search_btn.clicked.connect(self.file_controller.search_pdf_file)
        self.ui.folder_name_input.textEdited.connect(
            lambda: self.file_controller.refresh_toolbox() if not self.ui.folder_name_input.text().strip() else None)

        # root folder selection
        self.ui.article_locat_btn.clicked.connect(self.file_controller.select_local_root_folder)

        # Articles section :
        self.ui.article_search_btn.clicked.connect(self.article_controller.search_articles)
        self.ui.article_download_btn.clicked.connect(self.article_controller.download_article_pdf)
        self.ui.export_journal_info_btn.clicked.connect(self.article_controller.export_with_change_index)
        self.ui.articles_downloader_mode_btn.toggled.connect(self.float_downloader)
        self.ui.article_info_led.textEdited.connect(lambda : self.article_controller.clear_article_results() if not self.ui.journal_info_led.text().strip() else None)

        # PDFs section :
        self.ui.fetch_pdf_btn.clicked.connect(self.pdf_search_controller.start_search)
        self.ui.extract_text_btn.clicked.connect(self.pdf_search_controller.export_results)
        self.ui.pdf_files_btn.clicked.connect(self.file_controller.select_pdf_files_path)
        self.ui.files_toolbox.currentChanged.connect(self.file_controller.files_toolbox_changes)
        self.ui.navigation_mode_cbox.stateChanged.connect(self.file_controller.files_toolbox_changes)
        self.ui.fetch_pdf_mode_cbox.currentTextChanged.connect(self.pdf_search_controller.initial_stat)
        self.ui.Fetch_pdf_led.textEdited.connect(
            lambda: self.pdf_search_controller.clear_pdfs_results() if not self.ui.Fetch_pdf_led.text().strip() else None)

        # Journals Section :
        self.ui.journal_search_btn.clicked.connect(self.journal_controller.search_journals)
        self.ui.journal_add_btn.clicked.connect(self.journal_controller.add_journal)
        self.ui.journal_save_btn.clicked.connect(self.journal_controller.save_all_journal_changes)
        self.ui.journal_info_led.textEdited.connect( self.journal_controller.is_it_empty)

        # change language:
        self.ui.change_lang_iconm_cbox.currentTextChanged.connect(self.language_changed)
        self.ui.change_lang_cbox.currentTextChanged.connect(self.language_changed)

        #Connect Zotero buttons:
        self.ui.zotero_add_btn.clicked.connect(self.article_controller.send_to_zotero)
        self.ui.zotero_float_add_btn.clicked.connect(self.article_controller.send_to_zotero)

        #Float Downloader :
        self.ui.article_float_download_btn.clicked.connect(self.article_controller.float_article_downloader)
        self.ui.article_float_export_btn.clicked.connect(self.article_controller.export_journal_info)

        # Connect buttons to theme modes
        self.ui.them_change_btn.toggled.connect(self._toggle_theme)

        # Open the github page
        self.ui.info_btn.clicked.connect(self._open_github)

    def _load_initial_state(self) -> None:
        self.ui.root_directory_led.setText(self.config_manager.root_path)
        self.ui.FullMenuFrame.hide()
        self.ui.MainFram.setCurrentIndex(0)
        QTimer.singleShot(100, self.file_controller.refresh_toolbox)
        self.journal_controller.load_all_journals()
        self._last_cbox_selected()
        self._theme_btn_status()

    def language_changed(self, lang:str) -> None:
        """Handle language change."""
        self.config_manager.set_last_selected_text(lang)
        self.ui.change_lang_iconm_cbox.currentTextChanged['QString'].connect(self.ui.change_lang_cbox.setCurrentText)
        self.ui.change_lang_cbox.currentTextChanged['QString'].connect(self.ui.change_lang_iconm_cbox.setCurrentText)
        self.ui.translations(lang)

    def articles_downloader_mode(self) -> None:
        self.ui.search_mode_cbox.currentTextChanged['QString'].connect(self.ui.article_float_search_mode_cbox.setCurrentText)
        self.ui.article_float_search_mode_cbox.currentTextChanged['QString'].connect(self.ui.search_mode_cbox.setCurrentText)

    def float_downloader(self) -> None:
        articles_mode = self.ui.articles_downloader_mode_btn
        if articles_mode.isChecked():
            self.ui.downloaded_dockwidget.show()
        else:
            self.ui.downloaded_dockwidget.close()

    def _toggle_theme(self) -> None:
        """Switches between dark and light mode."""
        checked = self.ui.them_change_btn.isChecked()
        if checked:
            selected_theme = "dark"
        else:
            selected_theme ="light"

        self.config_manager.set_theme(selected_theme)
        self._apply_stylesheet(selected_theme)

    def _theme_btn_status(self):
        status = True if self.config_manager.theme == "dark" else False
        self.ui.them_change_btn.setChecked(status)

    def _last_cbox_selected(self) -> None:

        if self.config_manager.last_selected_text:
            index = self.ui.change_lang_cbox.findText(self.config_manager.last_selected_text)
            if index != -1:
                self.ui.change_lang_cbox.setCurrentIndex(index)
                self.ui.change_lang_iconm_cbox.setCurrentIndex(index)

    def _apply_stylesheet(self, mode:str) -> None:
        """Loads and applies the selected theme stylesheet."""
        styles = {
            "dark": self.config_manager.resource_path("utils/Themes/dark_stylesheet.css"),
            "light": self.config_manager.resource_path("utils/Themes/light_stylesheet.css")
        }
        file_path = styles.get(mode, styles["light"])
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                self.setStyleSheet(file.read())
        else:
            print(f"Error: Stylesheet not found at {file_path}")

    def _adjust_ui_for_resolution(self) -> None:
        """Dynamically adjusts the UI size and font based on screen resolution."""
        screen = QApplication.primaryScreen().geometry()
        width, height = screen.width(), screen.height()

        scale_factor = min(width / 1920, height / 1080)  # Normalize based on Full HD resolution

        base_font_size = 12  # Default font size
        new_font_size = int(base_font_size * scale_factor)

        font = QFont("Arial", new_font_size)
        QApplication.setFont(font)

        # Adjust UI elements
        self.ui.centralwidget.setStyleSheet(f"QWidget {{ font-size: {new_font_size}px; }}")

    @staticmethod
    def _open_github() -> None:
        import webbrowser
        webbrowser.open("https://github.com/OualiA")