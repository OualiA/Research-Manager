import sqlite3
from sqlite3 import Connection
from typing import Any


class JournalDB:
    def __init__(self, db_path="journals.db"):
        self.db_path = db_path
        self._create_table()

    def _get_connection(self) -> Connection:
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_name TEXT UNIQUE,
                issn TEXT,
                open_access TEXT,
                journal_rank TEXT,
                publication_fee TEXT,
                site TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save_journal(self, journal_data: dict) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO journals (journal_name, issn, open_access, journal_rank, publication_fee, site)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            journal_data.get("Journal", ""),
            journal_data.get("ISSN", ""),
            journal_data.get("Open Access", ""),
            journal_data.get("Journal Rank", ""),
            journal_data.get("Publication Fee", ""),
            journal_data.get("Site", "")
        ))
        conn.commit()
        conn.close()

    def get_journal_by_name(self, journal_name: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM journals WHERE journal_name = ?", (journal_name,))
        result = cursor.fetchone()
        conn.close()
        return result

    def update_journal(self, journal_data: dict) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE journals
            SET issn = ?,
                open_access = ?,
                journal_rank = ?,
                publication_fee = ?,
                site = ?
            WHERE journal_name = ?
        ''', (
            journal_data.get("ISSN", ""),
            journal_data.get("Open Access", ""),
            journal_data.get("Journal Rank", ""),
            journal_data.get("Publication Fee", ""),
            journal_data.get("Site", ""),
            journal_data.get("Journal", "")
        ))
        conn.commit()
        conn.close()

    def fetch_journals(self, query: str) -> list[Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT journal_name, issn, open_access, journal_rank, publication_fee, site FROM journals WHERE journal_name LIKE ?", (f"%{query}%",))
        results = cursor.fetchall()
        conn.close()
        return results

    def add_journal(self, journal_name: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO journals (journal_name, issn, open_access, journal_rank, publication_fee, site)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (journal_name, "", "", "", "", ""))
        conn.commit()
        conn.close()

    def delete_journal(self, journal_name: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM journals WHERE journal_name = ?", (journal_name,))
        conn.commit()
        conn.close()
