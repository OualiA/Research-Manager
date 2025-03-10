import os
import fitz
import re
import time
import gc
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication

class PDFSearchWorker(QThread):
    progress = Signal(str, int, int)
    result = Signal(str, str, int, str, str)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, file_paths, mode_search, search_text=None):
        super().__init__()
        self.file_paths = file_paths
        self.mode_search = mode_search
        self.search_text = search_text.strip() if search_text else None
        self.running = False
        self.match_count = 0
        self.result_buffer = []
        self.last_flush = time.time()
        self.clean_patterns = [
            (re.compile(r'(\d)\s+([A-Za-z])'), r'\1 \2'),
            (re.compile(r'([A-Za-z])\s+(\d)'), r'\1 \2'),
            (re.compile(r'([=+\-])\s+'), r'\1 '),
            (re.compile(r'\s+([=+\-])'), r' \1'),
            (re.compile(r'\(\s+'), r'('),
            (re.compile(r'\s+\)'), r')'),
            (re.compile(r'\s+'), ' '),
            (re.compile(r'[^\x20-\x7E]'), '')
        ]
        if self.search_text:
            self.clean_patterns.append(
                (re.compile(r'\b({})\b'.format(re.escape(self.search_text)), re.IGNORECASE), r'**\1**')
            )

    def run(self):
        self.started.emit()
        self.running = True
        total = len(self.file_paths)
        try:
            for idx, file_path in enumerate(self.file_paths):
                time.sleep(0.2)
                if not self.running:
                    break
                QApplication.processEvents()
                self.process_file(file_path)
                if idx % 1 == 0:
                    percent = int((idx + 1) / total * 100)
                    self.progress.emit(f"Processing {idx+1}/{total}", self.match_count, percent)
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")
        finally:
            if self.result_buffer:
                for res in self.result_buffer:
                    self.result.emit(*res)
                self.result_buffer.clear()
            self.finished.emit()

    def process_file(self, file_path):

        if not os.path.exists(file_path):
            self.error_occurred.emit(f"File not found: {file_path}")
            return
        file_name = os.path.basename(file_path)
        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                if not self.running:
                    return
                QApplication.processEvents()
                if self.mode_search == "Matched Text":
                    self.process_text_matches(page, page_num, file_path, file_name)
                else:
                    self.process_highlights(page, page_num, file_path, file_name)
                if page_num % 2 == 0:
                    QApplication.processEvents()
                    gc.collect()
            doc.close()
        except Exception as e:
            self.error_occurred.emit(f"Error in {file_name}: {str(e)}")

    def process_text_matches(self, page, page_num, file_path, file_name):
        text = page.get_text("text", sort=True)
        if not self.search_text or not text:
            return
        matches = list(re.finditer(re.escape(self.search_text), text, re.IGNORECASE))
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            cleaned = self.clean_sentence(context)
            excerpt = self.highlight_match(cleaned, match.group())
            self.result.emit(file_path, file_name, page_num, excerpt, "Matched Text")
            self.match_count += 1

    def process_highlights(self, page, page_num, file_path, file_name):
        for highlight in self.extract_highlighted_text(page):
            self.result.emit(file_path, file_name, page_num, highlight, "Highlight")
            self.match_count += 1

    @staticmethod
    def highlight_match(text, term):
        return re.sub(re.escape(term), r'<b>\g<0></b>', text, flags=re.IGNORECASE)

    def extract_highlighted_text(self, page):
        highlights = []
        for annot in page.annots():
            if annot.type[0] == 8:
                try:
                    quads = annot.vertices
                    if len(quads) < 4:
                        continue
                    full_text = []
                    for i in range(0, len(quads), 4):
                        if i + 3 >= len(quads):
                            continue
                        quad = quads[i:i+4]
                        rect = fitz.Quad(quad).rect
                        txt = page.get_text("text", clip=rect).strip()
                        if txt:
                            full_text.append(txt)
                    if full_text:
                        htext = " ".join(full_text).strip()
                        comment = annot.info.get("content", "").strip()
                        if comment:
                            highlights.append(f"{comment}: {htext}")
                        else:
                            highlights.append(htext)
                except Exception as e:
                    self.error_occurred.emit(f"Highlight error: {str(e)}")
        return highlights

    def clean_sentence(self, sentence):
        for pattern, repl in self.clean_patterns:
            sentence = pattern.sub(repl, sentence)
        return sentence.strip()
