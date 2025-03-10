from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QPushButton, QHBoxLayout, \
    QTreeWidgetItem, QMessageBox, QTreeWidget, QSizePolicy
from PySide6.QtCore import Qt, QUrl
import os

class TableBuilder:
#######################################################################################################################
# File Manager Section
#######################################################################################################################
    @staticmethod
    def create_pdf_table(folder_path: str, pdf_files: list, open_callback, delete_callback) -> QTableWidget:
        """Create the Table"""
        row_count = max(1, len(pdf_files))
        table = QTableWidget(row_count, 2)
        table.setHorizontalHeaderLabels(["File Name", "Actions"])
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setDefaultSectionSize(40)

        if not pdf_files:
            TableBuilder._create_empty_table_message(table)
            return table

        for row, file_name in enumerate(pdf_files):
            file_path = os.path.join(folder_path, file_name)
            TableBuilder._add_file_row(table, row, file_name, file_path, open_callback, delete_callback)
        return table

    @classmethod
    def display_article_data(cls, article_data: dict, parent: QTreeWidgetItem, prefix: str = "") -> None:
        """ display article metadata in a QTreeWidget. """
        for key, value in article_data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                item = QTreeWidgetItem(parent, [key])
                cls.display_article_data(value, item, full_key)
            elif isinstance(value, list):
                item = QTreeWidgetItem(parent, [key])
                for idx, elem in enumerate(value):
                    cls.display_article_data({f"{idx + 1}": elem}, item, full_key)
            else:
                QTreeWidgetItem(parent, [key, str(value)])

    @staticmethod
    def _add_file_row(table, row, file_name, file_path, open_callback, delete_callback)-> None:
        """Add PDF files to the Tree"""
        item = QTableWidgetItem(file_name)
        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 0, item)
        btn_widget = TableBuilder._create_action_buttons(file_path, open_callback, delete_callback)
        table.setCellWidget(row, 1, btn_widget)

    @staticmethod
    def _create_action_buttons(file_path, open_callback, delete_callback)-> None:
        """Add actions buttons to the Tree"""
        btn_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        open_btn = QPushButton("📂 Open")
        open_btn.setToolTip("Open file")
        open_btn.clicked.connect(lambda: open_callback(file_path))
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(open_btn)
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setToolTip("Delete file")
        delete_btn.clicked.connect(lambda: delete_callback(file_path))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(delete_btn)
        btn_widget.setLayout(layout)
        return btn_widget

    @staticmethod
    def _create_empty_table_message(table)-> None:
        """Empty Table for the empty folders"""
        item = QTableWidgetItem("No PDFs Found")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(0, 0, item)
        table.setSpan(0, 0, 1, 2)
        table.setEnabled(False)
#######################################################################################################################
#Journale Section
#######################################################################################################################
    @staticmethod
    def build_journal_info_table(journals: list, journal_tree: QTreeWidget, delete_callback=None) -> None:
        """Populate the journal_tree with a list of journal records."""
        journal_tree.clear()
        journal_tree.setColumnCount(7)
        journal_tree.setHeaderLabels([
            "Journal Name", "ISSN", "Open Access", "Journal Rank", "Publication Fee", "Site", "Actions"
        ])
        journal_tree.header().setVisible(True)

        for record in journals:
            if len(record) < 6:
                continue
            item = QTreeWidgetItem([
                record[0],
                record[1],
                record[2],
                record[3],
                record[4],
                record[5],
                ""
            ])

            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            journal_tree.addTopLevelItem(item)
            actions_widget = TableBuilder._create_actions_widget(item, journal_tree, delete_callback)
            journal_tree.setItemWidget(item, 6, actions_widget)

        # Set column widths.
        TableBuilder._setup_journal_tree_columns(journal_tree)

    @staticmethod
    def _create_actions_widget(row_item: QTreeWidgetItem, tree: QTreeWidget, delete_callback=None) -> QWidget:
        """Add the actions buttons to the Tree"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda: TableBuilder._open_journal_site(row_item))
        layout.addWidget(open_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if delete_callback:
            delete_btn.clicked.connect(lambda: delete_callback(row_item, tree))
        else:
            delete_btn.clicked.connect(lambda: TableBuilder._default_delete(row_item, tree))
        layout.addWidget(delete_btn)

        widget.setLayout(layout)
        return widget

    @staticmethod
    def _open_journal_site(row_item: QTreeWidgetItem) -> None:
        """Open the journal site or search for it"""
        site_text = row_item.text(5).strip()
        if site_text:
            if not (site_text.startswith("http://") or site_text.startswith("https://")):
                site_text = "http://" + site_text
            QDesktopServices.openUrl(QUrl(site_text))
        else:
            issn = row_item.text(1).strip()
            jn = row_item.text(0).strip()
            try:
                if issn == "N/A":
                    search_url = f"https://www.google.com/search?q={jn} + journal"
                else:
                    search_url = f"https://www.google.com/search?q={issn} + journal"
                QDesktopServices.openUrl(QUrl(search_url))

            except Exception:
                QMessageBox.information(None, "Open Journal", "No site or ISSN available to open.")

    @staticmethod
    def _default_delete(row_item: QTreeWidgetItem, tree: QTreeWidget)-> None:
        """Delete journal from the database and the Tree"""
        reply = QMessageBox.question(
            None, "Delete Journal Entry",
            "Are you sure you want to delete this journal entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            index = tree.indexOfTopLevelItem(row_item)
            if index != -1:
                tree.takeTopLevelItem(index)

    @staticmethod
    def _setup_journal_tree_columns(journal_tree: QTreeWidget ) -> None:
        """Setup tree widget columns."""
        header = journal_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        journal_tree.setSortingEnabled(True)
        journal_tree.setColumnWidth(6, 80)

#######################################################################################################################
#PDFs Section
#######################################################################################################################
    @staticmethod
    def add_result_to_tree(results_tree: QTreeWidget,
                           matched_results: list,
                           highlighted_results: list,
                           file_path: str,
                           file_name: str,
                           page_num: int,
                           content: str,
                           result_type: str) -> None:
        """ Add a PDF search result to the results_tree. """

        TableBuilder._setup_tree_columns(results_tree)
        results_tree.setUpdatesEnabled(False)
        try:
            parent = TableBuilder.get_or_create_parent_item(results_tree, file_name, file_path)
            page_item = None
            for i in range(parent.childCount()):
                if parent.child(i).text(1) == str(page_num):
                    page_item = parent.child(i)
                    break
            if not page_item:
                page_item = QTreeWidgetItem(parent, ["", str(page_num), "", ""])
                page_item.setExpanded(False)
            match_num = page_item.childCount() + 1
            match_item = QTreeWidgetItem(page_item)
            match_item.setText(0, f"Match {match_num}")
            match_item.setText(1, str(page_num))
            match_item.setText(2, content)
            match_item.setData(0, Qt.ItemDataRole.UserRole, file_path)

            copied_text = f"{content}. ({file_name})"
            # Create an actions' widget.
            btn_widget = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            copy_btn = QPushButton("📋")
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # copy to the clipboard.
            copy_btn.clicked.connect(lambda: TableBuilder.copy_item_text(copied_text))
            layout.addWidget(copy_btn)
            btn_widget.setLayout(layout)
            results_tree.setItemWidget(match_item, 3, btn_widget)

            if result_type == "Highlight":
                highlighted_results.append([file_name, page_num, content, file_path])
            else:
                matched_results.append([file_name, page_num, content, file_path])

            match_item.setToolTip(2, content)
        finally:
            results_tree.setUpdatesEnabled(True)
            results_tree.viewport().update()

    @staticmethod
    def get_or_create_parent_item(results_tree: QTreeWidget, file_name: str, file_path: str) -> QTreeWidgetItem:
        """ Retrieve an existing parent item for a given file_name or create a new one."""
        for i in range(results_tree.topLevelItemCount()):
            item = results_tree.topLevelItem(i)
            if item.text(0) == file_name:
                return item
        # If not found, create a new top-level item.
        parent = QTreeWidgetItem(results_tree, [file_name])
        parent.setExpanded(False)
        parent.setData(0, Qt.ItemDataRole.UserRole, file_path)
        # Create an actions widget with an Open button.
        btn_widget = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        open_btn = QPushButton("Open")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda: os.startfile(file_path))
        btn_layout.addWidget(open_btn)
        btn_widget.setLayout(btn_layout)
        results_tree.setItemWidget(parent, 3, btn_widget)
        return parent

    @staticmethod
    def copy_item_text(text: str) -> None:
        """ Copy the provided text to the clipboard. """
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    @staticmethod
    def _setup_tree_columns(results_tree: QTreeWidget,) -> None:
        """Setup tree widget columns."""
        header = results_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        results_tree.setColumnWidth(0, 200)
        results_tree.setColumnWidth(3, 120)
        results_tree.setSortingEnabled(True)