from PySide6.QtWidgets import QMessageBox
from views.table_builder import TableBuilder
from services.journal_db import JournalDB

class JournalController:
    def __init__(self, ui,  db: JournalDB = None):
        self.ui = ui
        self.db = db if db else JournalDB()  # Dependency injection
        self.is_it_empty()


    def load_all_journals(self) -> None:
        """ Load all journals from the database """
        results = self.db.fetch_journals("")
        TableBuilder.build_journal_info_table(results, self.ui.journal_tree_qwidget, delete_callback=self.delete_journal_record)
        if results:
            self._append_journal_log(f"Loaded {len(results)} journal(s) from the database.")
        else:
            self._append_journal_log("No journals in the database.")

    def delete_journal_record(self, row_item, tree) -> None:
        """ Delete the journal record corresponding to row_item from the database and remove the row. """
        journal_name = row_item.text(0).strip()
        print(journal_name)
        if not journal_name:
            QMessageBox.warning(self.ui.centralwidget, "Delete Journal", "Journal name is empty. Cannot delete.")
            return
        reply = QMessageBox.question(self.ui.centralwidget, "Delete Journal", f"Are you sure you want to delete '{journal_name}' from the database?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.get_journal_by_name(journal_name):
                self.db.delete_journal(journal_name)
                index = tree.indexOfTopLevelItem(row_item)
                if index != -1:
                    tree.takeTopLevelItem(index)
            QMessageBox.information(self.ui.centralwidget, "Delete Journal", f"Journal '{journal_name}' deleted from the database.")

        self.load_all_journals()

    def save_all_journal_changes(self) -> None:
        """ Iterate over all rows in the journal_tree_qwidget and update the database with current values. """
        journal_tree = self.ui.journal_tree_qwidget
        count = journal_tree.topLevelItemCount()
        for i in range(count):
            item = journal_tree.topLevelItem(i)
            journal_data = {
                "Journal": item.text(0),
                "ISSN": item.text(1),
                "Open Access": item.text(2),
                "Journal Rank": item.text(3),
                "Publication Fee": item.text(4),
                "Site": item.text(5)
            }
            self.db.update_journal(journal_data)
        QMessageBox.information(self.ui.centralwidget, "Save Changes", "All journal changes have been saved to the database.")
        self.load_all_journals()

    def search_journals(self) -> None:
        """ Search for journals matching the query """
        query = self.ui.journal_info_led.text().strip()
        if not query:
            QMessageBox.warning(self.ui.centralwidget, "Search Journal", "Please enter a journal name to search.")
            return
        results = self.db.fetch_journals(query)
        TableBuilder.build_journal_info_table(results, self.ui.journal_tree_qwidget, delete_callback=self.delete_journal_record)
        self.ui.INFO_journal_pltext.setPlainText(f"Found {len(results)} journal(s) matching '{query}'.")

    def add_journal(self) -> None:
        """ Add a new journal using the name from journal_add_led"""
        journal_name = self.ui.journal_add_led.text().strip()
        if not journal_name:
            QMessageBox.warning(self.ui.centralwidget, "Add Journal", "Please enter a journal name.")
            return
        if self.db.get_journal_by_name(journal_name):
            QMessageBox.information(self.ui.centralwidget, "Add Journal", f"Journal '{journal_name}' already exists in the database.")
            return
        self.db.add_journal(journal_name)
        QMessageBox.information(self.ui.centralwidget, "Add Journal", f"Journal '{journal_name}' added to the database.")
        self.ui.journal_add_led.clear()
        self.load_all_journals()

    def _append_journal_log(self, message: str) -> None:
        self.ui.INFO_journal_pltext.clear()
        self.ui.INFO_journal_pltext.appendPlainText(message)

    def is_it_empty(self) -> None:
        query = self.ui.journal_info_led.text().strip()
        if not query:
            self.load_all_journals()
            return