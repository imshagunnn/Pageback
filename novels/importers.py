import re
from pathlib import Path


def _split_text(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    sections = re.split(r"(?im)(?=^(?:chapter|part|book)\s+[\wivxlcdm-]+\b.*$)", text)
    sections = [section.strip() for section in sections if section.strip()]
    if len(sections) > 1:
        return sections
    words = text.split()
    return [" ".join(words[start:start + 8000]) for start in range(0, len(words), 8000)]


def extract_book_chapters(uploaded_file) -> list[str]:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix in {".txt", ".md"}:
        return _split_text(uploaded_file.read().decode("utf-8"))
    if suffix == ".pdf":
        from pypdf import PdfReader

        pages = []
        for page in PdfReader(uploaded_file).pages:
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(text)
        return [page for page in pages if page]
    if suffix == ".epub":
        from bs4 import BeautifulSoup
        from ebooklib import ITEM_DOCUMENT, epub

        book = epub.read_epub(uploaded_file)
        chapters = []
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            text = BeautifulSoup(item.get_content(), "html.parser").get_text(" ", strip=True)
            if text:
                chapters.append(text)
        return chapters
    raise ValueError("Unsupported book format.")