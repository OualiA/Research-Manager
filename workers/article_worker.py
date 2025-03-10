from pathlib import Path
from typing import Any
import nest_asyncio
from PySide6.QtCore import QThread, Signal
from habanero import Crossref
from semanticscholar import SemanticScholar
from workers.scihub import SciHub


nest_asyncio.apply()

class ArticleManager(QThread):
    result = Signal(dict)
    error = Signal(str)
    done = Signal(bool)
    finished = Signal()

    def __init__(self, download_path, article_doi=None, article_title=None):
        super().__init__()
        self.download_path = download_path
        self.article_doi = article_doi
        self.article_title = article_title

    def run(self) -> None:
        try:
            res = self.search_article()
            if res:
                self.result.emit(res)
                self.done.emit(True)
            else:
                self.error.emit("No results found.")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

    def search_article(self) -> dict[str, str | list[Any] | Any] | None:
        res = self._fetch_from_semantic_scholar()
        if not res:
            res = self._fetch_from_crossref()
        return res

    def _fetch_from_semantic_scholar(self, limit: int = 1) -> dict[str, str | list[Any] | Any] | None:
        try:
            sch = SemanticScholar()
            if self.article_doi:
                meta = sch.get_paper(self.article_doi)
            elif self.article_title:
                results = sch.search_paper(self.article_title, limit=limit)
                meta = next(iter(results), None)
                if not meta:
                    return None
            else:
                return None
            return {
                "Title": getattr(meta, "title", "N/A"),
                "Authors": [a["name"] for a in getattr(meta, "authors", [])],
                "Published Date": getattr(meta, "year", "N/A"),
                "DOI": meta.externalIds.get("DOI", "N/A") if hasattr(meta, "externalIds") else "N/A",
                "Journal": meta.journal.name if hasattr(meta, "journal") and meta.journal else "N/A",
                "ISSN": meta.get("journal", {}).get("issn", "N/A"),
                "Article URL": getattr(meta, "url", "N/A"),
                "Open Access": "Yes" if getattr(meta, "isOpenAccess", False) else "No",
                "Impact Factor": getattr(meta, "citationCount", "N/A"),
                "Source": "Semantic Scholar"
            }
        except Exception:
            return None

    def _fetch_from_crossref(self, limit: int = 1) -> dict[str, str | list[Any] | Any] | None:
        try:
            cr = Crossref()
            if self.article_doi:
                meta = cr.works(ids=self.article_doi)
                if meta.get("message"):
                    meta = meta["message"]
            elif self.article_title:
                results = cr.works(query=self.article_title, limit=limit)
                if results.get("message", {}).get("items"):
                    meta = results["message"]["items"][0]
                else:
                    return None
            else:
                return None
            return {
                "Title": meta.get("title", ["N/A"])[0],
                "Authors": [f'{a.get("family", "")}, {a.get("given", "")}' for a in meta.get("author", [])],
                "Published Date": meta.get("published-print", {}).get("date-parts", [["N/A"]])[0],
                "Publisher": meta.get("publisher", "N/A"),
                "DOI": meta.get("DOI", "N/A"),
                "Journal": meta.get("container-title", ["N/A"])[0],
                "ISSN": meta.get("ISSN", [])[0] if meta.get("ISSN", []) else "N/A",
                "Article URL": meta.get("URL", "N/A"),
                "Open Access": "Yes" if meta.get("license") else "No",
                "Impact Factor": "N/A",
                "Source": "CrossRef"
            }
        except Exception:
            return None

class SciDownloadThread(QThread):
    message = Signal(str)
    failed = Signal(str)
    success = Signal(str)
    pdf_path = Signal(str)

    def __init__(self, download_path, article_doi, article_title="Article"):
        super().__init__()
        self.download_path = download_path
        self.article_doi = article_doi
        self.article_title = article_title +".pdf"

    def run(self) -> None:
        if not self.article_doi:
            self.message.emit("Error: No DOI provided.")
            return
        if not self.download_path:
            self.message.emit("Error: No download folder specified.")
            return

        try:
            self.message.emit(f"Fetching article: {self.article_doi}")

            # Capture the initial file list before downloading
            download_dir = Path(self.download_path)
            if not download_dir.exists():
                download_dir.mkdir(parents=True, exist_ok=True)

            initial_files = set(download_dir.iterdir())  # Set of initial files in the directory

            # Execute the download
            scihub_download = SciHub().download(identifier= self.article_doi, destination=self.download_path, path= self.article_title)

            final_files = set(download_dir.iterdir())
            new_files = final_files - initial_files
            if scihub_download.get("err"):
                scihub_error = scihub_download.get("err")
                self.message.emit(scihub_error)
                self.failed.emit(f"Process Failed for:\n {scihub_error}")
            elif not new_files:
                self.message.emit(f"Failed to download article or it is already exist: {self.article_title}")
                self.failed.emit(f"Process Failed for:\n {self.article_title}")
                return

            # Get the downloaded file name
            downloaded_file = next(iter(new_files))
            self.message.emit(
                f"Download completed for: {self.article_title}\n"
                f"Saved in: {downloaded_file}")
            self.pdf_path.emit(self.download_path + "/" + self.article_title)
            self.success.emit(f"Download completed for:\n {self.article_title}")

        except Exception as e:
            self.message.emit(f"[Error] Download error: {e}")
            print(e)



