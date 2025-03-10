import os
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QFileDialog, QMessageBox, QAbstractItemView
from services.file_service import FileService
from views.table_builder import TableBuilder


class FileController:
    def __init__(self, ui, config_manager):
        self.ui = ui
        self.config_manager = config_manager
        self.folder_paths = {}
        self.selected_pdfs = []

        self.load_root_folder()
        self.file_service = FileService()
        self.root_folder = None

    def load_root_folder(self) -> None:
        """load the root folder at the beginning"""
        self.ui.root_directory_led.setText(self.config_manager.root_path)
        self.root_folder = self.config_manager.root_path
        self.file_service = FileService(root_folder=self.root_folder)

    def refresh_toolbox(self) -> None:
        """Refresh the toolbox while keeping the currently selected page."""
        current_index = self.ui.files_toolbox.currentIndex() if self.ui.files_toolbox.count() > 0 else -1
        current_folder = self.folder_paths.get(current_index, None) if current_index != -1 else None

        while self.ui.files_toolbox.count() > 0:
            self.ui.files_toolbox.removeItem(0)
        self.folder_paths.clear()

        root_folder = self.config_manager.root_path
        if not root_folder or not os.path.isdir(root_folder):
            QMessageBox.warning(self.ui.centralwidget, "Warning", "Root folder is not set or invalid.")
            return

        processed_folders = set()
        new_index = -1

        for subdir, _, files in os.walk(root_folder):
            folder_name = os.path.basename(subdir)
            if folder_name not in processed_folders:
                pdf_files = [f for f in files if f.lower().endswith(".pdf")]
                table = TableBuilder.create_pdf_table(
                    folder_path=subdir,
                    pdf_files=pdf_files,
                    open_callback=self.open_pdf,
                    delete_callback=self.delete_pdf
                )

                index = self.ui.files_toolbox.addItem(table, folder_name)
                self.folder_paths[index] = subdir
                processed_folders.add(folder_name)

                if subdir == current_folder:
                    new_index = index

        if new_index != -1:
            self.ui.files_toolbox.setCurrentIndex(new_index)

    def open_pdf(self, file_path) -> None:
        """Open the selected PDF file"""
        try:
            self.file_service.open_file(file_path)
        except Exception as e:
            QMessageBox.critical(self.ui.centralwidget, "Error", f"Failed to open file:\n{str(e)}")

    def delete_pdf(self, file_path) -> None:
        """Delete the selected PDF file"""
        reply = QMessageBox.question(
            self.ui.centralwidget, "Confirm Deletion",
            f"Are you sure you want to delete:\n{file_path}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.file_service.delete_file(file_path)
                QMessageBox.information(self.ui.centralwidget, "Deleted", f"File deleted:\n{file_path}")
                self.refresh_toolbox()
            except Exception as e:
                QMessageBox.critical(self.ui.centralwidget, "Error", f"Deletion failed:\n{str(e)}")

    def create_folder(self) -> None:
        """Create a new folder within the root folder"""
        folder_name = self.ui.folder_name_input.text().strip()
        try:
            self.load_root_folder()
            new_folder = self.file_service.create_folder(folder_name)
            QMessageBox.information(self.ui.centralwidget, "Folder Created", f"Created folder:\n{new_folder}")
            self.refresh_toolbox()
        except Exception as e:
            QMessageBox.critical(self.ui.centralwidget, "Error", f"Failed to create folder:\n{str(e)}")

    def open_directory(self) -> None:
        """Open the selected folder directory"""
        index = self.ui.files_toolbox.currentIndex()
        folder_path = self.folder_paths.get(index)

        if folder_path:
            try:
                self.file_service.open_file(folder_path)
            except Exception as e:
                QMessageBox.critical(self.ui.centralwidget, "Error", f"Cannot open folder:\n{str(e)}")
        else:
            QMessageBox.warning(self.ui.centralwidget, "Warning", "No folder selected.")

    def delete_directory(self) -> None:
        """Delete the selected folder"""
        index = self.ui.files_toolbox.currentIndex()
        folder_path = self.folder_paths.get(index)
        if folder_path:
            reply = QMessageBox.question(
                self.ui.centralwidget, "Confirm Folder Deletion",
                f"Delete folder and all contents?\n{folder_path}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                import shutil
                try:
                    shutil.rmtree(folder_path)
                    QMessageBox.information(self.ui.centralwidget, "Deleted", "Folder deleted.")
                    self.refresh_toolbox()
                except Exception as e:
                    QMessageBox.critical(self.ui.centralwidget, "Error", f"Failed to delete folder:\n{str(e)}")
        else:
            QMessageBox.warning(self.ui.centralwidget, "Warning", "No folder selected.")

    def get_download_path(self) -> str:
        """ Returns the path to use for downloading an article. """
        if self.ui.navigation_mode_cbox.isChecked():
            index = self.ui.files_toolbox.currentIndex()
            folder = self.folder_paths.get(index, "")
            if folder:
                return folder
            else:
                QMessageBox.warning(self.ui.centralwidget, "Path Error", "No folder selected in the toolbox.")
                return ""
        else:
            root_folder = self.ui.root_directory_led.text()
            if root_folder.strip():
                return root_folder
            else:
                folder = QFileDialog.getExistingDirectory(self.ui.centralwidget, "Select Root Folder")
                if folder:
                    self.root_folder = os.path.abspath(folder)
                    self.ui.root_directory_led.setText(self.root_folder)
                    self.select_local_root_folder()
                    return self.root_folder
                else:
                    QMessageBox.warning(self.ui.centralwidget, "Path Error", "No root folder selected.")
                    return ""

    def select_pdf_files_path(self) -> None:
        """ Determines the list of PDF files to use """
        self.ui.pdf_ptext.clear()
        if self.ui.navigation_mode_cbox.isChecked():
            index = self.ui.files_toolbox.currentIndex()
            folder = self.folder_paths.get(index, "")
            if folder:
                self.selected_pdfs = [os.path.join(folder, f)
                                      for f in os.listdir(folder)
                                      if f.lower().endswith(".pdf")]
            else:
                self.ui.pdf_ptext.appendPlainText("No folder selected in the toolbox.")
                self.selected_pdfs = []
        else:
            try:
                files, _ = QFileDialog.getOpenFileNames(self.ui.centralwidget, "Select PDF Files", "", "PDF Files (*.pdf)")
                if files:
                    self.selected_pdfs = files
            except Exception as e:
                self.ui.pdf_ptext.appendPlainText(f"Error: {e}")
        self.ui.pdf_location_lined.setText(", ".join(self.selected_pdfs))

    def select_local_root_folder(self) -> None:
        """set the root folder and add it to the config file"""
        folder_path = QFileDialog.getExistingDirectory(parent=None,caption="Select Root Folder")
        if folder_path:
            self.config_manager.root_path = folder_path
            self.config_manager.save_config()
            self.ui.root_directory_led.setText(folder_path)
            self.refresh_toolbox()

    def files_toolbox_changes(self)-> None:
        """check the mode and the current section"""
        if self.ui.navigation_mode_cbox.isChecked() and self.ui.MainFram.currentIndex() == 1:
            self.select_pdf_files_path()
        else:
            return

    def search_pdf_file(self) -> None:
        """Search for all matching PDFs and highlight their rows in `files_toolbox`."""
        self.refresh_toolbox()
        search_name = self.ui.folder_name_input.text().strip()
        if not search_name:
            QMessageBox.warning(self.ui.centralwidget, "Search Error", "Enter a file name to search.")
            return

        search_folder = self.config_manager.root_path
        if self.ui.navigation_mode_cbox.isChecked():
            index = self.ui.files_toolbox.currentIndex()
            search_folder = self.folder_paths.get(index, search_folder)

        if not search_folder or not os.path.isdir(search_folder):
            QMessageBox.warning(self.ui.centralwidget, "Search Error", "Invalid search folder.")
            return

        found_files = []
        for root, _, files in os.walk(search_folder):
            for file in files:
                if search_name.lower() in file.lower() and file.endswith(".pdf"):
                    found_files.append((root, file))

        if found_files:
            self._highlight_matching_rows(found_files)
            QMessageBox.information(self.ui.centralwidget, "Search Result", f"Found {len(found_files)} matching file(s).")
        else:
            QMessageBox.warning(self.ui.centralwidget, "Search Result", "No matching PDF found.")

    def _highlight_matching_rows(self, found_files)-> None:
        """Highlight the exact row where the matching PDFs are found."""
        for i in range(self.ui.files_toolbox.count()):
            table = self.ui.files_toolbox.widget(i)
            if table is None:
                continue

            for row in range(table.rowCount()):
                file_name_item = table.item(row, 0)
                if file_name_item and any(file_name.lower() == file_name_item.text().lower() for _, file_name in found_files):
                    file_name_item.setBackground(QBrush(QColor(255, 255, 0)))
                    file_name_item.setForeground(QBrush(QColor(0, 0, 0)))
                    table.scrollToItem(file_name_item, QAbstractItemView.ScrollHint.PositionAtCenter)



