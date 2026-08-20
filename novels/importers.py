import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from django.core.files.base import ContentFile


@dataclass
class ImportedSection:
    content: str
    title: str = ""
    source_page_start: int | None = None
    source_page_end: int | None = None
    content_type: str = "chapter"
    parent_title: str = ""


@dataclass
class ImportSummary:
    format: str
    sections: list[ImportedSection]
    front_matter_detected: bool = False
    toc_detected: bool = False
    cover_detected: bool = False
    confidence: str = "low"


_ORDINALS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|"
    "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth"
    "|[0-9]+|[ivxlcdm]+"
)
_STRUCTURAL_LABELS = r"chapter|part|book|night|nights|day|days|act|section"
_HEADING_RE = re.compile(
    rf"(?im)^[ \t]*(?:#+[ \t]+)?(?P<label>"
    rf"__PAGEBACK_HEADING__[ \t]+[^\n]+"
    rf"|"
    rf"(?:{_STRUCTURAL_LABELS})[ \t]+(?:{_ORDINALS})"
    rf"|(?:{_ORDINALS})[ \t]+(?:night|nights|day|days)"
    rf"|(?:{_STRUCTURAL_LABELS})[ \t]*[:.-][ \t]*[A-Za-z][^\n]*"
    rf"|(?:prologue|epilogue|introduction|afterword|preface)"
    rf")[ \t]*(?:[-:.)][ \t]*.*)?[ \t]*$"
)
_FRONT_MATTER_RE = re.compile(r"(?i)\b(copyright|table of contents|contents|dedication|publication data|all rights reserved)\b")


def extract_book_cover(uploaded_file) -> ContentFile | None:
    """Return a local embedded cover when the source exposes one reliably."""
    suffix = Path(uploaded_file.name).suffix.lower()
    uploaded_file.seek(0)
    if suffix == ".epub":
        from ebooklib import ITEM_IMAGE, epub

        book = epub.read_epub(uploaded_file)
        cover_id = None
        for _, metadata in book.get_metadata("OPF", "cover"):
            cover_id = metadata.get("content")
            if cover_id:
                break
        image_items = list(book.get_items_of_type(ITEM_IMAGE))
        candidates = image_items
        if cover_id:
            cover_item = book.get_item_with_id(cover_id)
            candidates = [cover_item] if cover_item else image_items
        else:
            candidates = [item for item in image_items if "cover" in item.get_name().lower()] or image_items
        if candidates:
            item = candidates[0]
            return ContentFile(item.get_content(), name=Path(item.get_name()).name)
    elif suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(uploaded_file)
        if reader.pages:
            first_page = reader.pages[0]
            text = (first_page.extract_text() or "").strip()
            images = getattr(first_page, "images", [])
            if images and len(text) < 500:
                image = images[0]
                return ContentFile(image.data, name=image.name)
    return None


def _page_for_offset(offset: int, page_ranges: list[tuple[int, int]]) -> int:
    for page_number, (page_start, page_end) in enumerate(page_ranges, start=1):
        if page_start <= offset <= page_end:
            return page_number
    return len(page_ranges)


def _heading_sections(text: str, *, page_ranges: list[tuple[int, int]] | None = None) -> list[ImportedSection]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return []

    sections = []
    pending_parent = ""
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        title = re.sub(r"^__PAGEBACK_HEADING__\s*", "", match.group("label").strip())
        title = re.sub(r"^#+\s*", "", title).strip()
        title_words = title.lower().split()
        known_labels = {"chapter", "part", "book", "night", "nights", "day", "days", "act", "section", "prologue", "epilogue", "introduction", "afterword", "preface"}
        known_ordinals = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"}
        if title_words and (title_words[0] in known_labels or title_words[0] in known_ordinals or title_words[-1] in {"night", "nights", "day", "days"}):
            title = title.title()
        else:
            title = title.strip()
        first_word = title.lower().split()[0] if title else "section"
        if first_word in {"part", "book"} and not content:
            pending_parent = title
            continue
        if not content:
            continue
        page_start = page_end = None
        if page_ranges:
            page_start = _page_for_offset(match.start(), page_ranges)
            page_end = _page_for_offset(max(start, end - 1), page_ranges)
        content_type = {
            "chapter": "chapter",
            "part": "part",
            "book": "book",
        }.get(first_word, "section")
        sections.append(
            ImportedSection(
                content=content,
                title=title,
                source_page_start=page_start,
                source_page_end=page_end,
                content_type=content_type,
                parent_title=pending_parent,
            )
        )
        pending_parent = ""
    return sections


def _validate_sections(sections: list[ImportedSection]) -> list[ImportedSection]:
    validated = []
    seen = set()
    for section in sections:
        content = re.sub(r"\s+", " ", section.content).strip()
        title = section.title.strip() or f"Section {len(validated) + 1}"
        if not content:
            continue
        key = (title.casefold(), content.casefold())
        if key in seen:
            continue
        seen.add(key)
        section.content = content
        section.title = title
        validated.append(section)
    return validated


def _fallback_section(text: str) -> list[ImportedSection]:
    text = text.strip()
    return [ImportedSection(content=text, title="Section 1", content_type="section")] if text else []


def _remove_front_matter(text: str, sections: list[ImportedSection]) -> tuple[str, bool]:
    if not sections:
        return text, False
    prefix = text[: text.find(sections[0].title)] if sections[0].title else ""
    detected = bool(prefix and _FRONT_MATTER_RE.search(prefix))
    return (text[text.find(sections[0].title):] if detected else text), detected


def _summary(format_name: str, sections: list[ImportedSection], *, front_matter=False, toc=False, cover=False, confidence="low") -> ImportSummary:
    return ImportSummary(
        format=format_name,
        sections=sections,
        front_matter_detected=front_matter,
        toc_detected=toc,
        cover_detected=cover,
        confidence=confidence,
    )


def _parse_text_document(text: str, format_name: str) -> ImportSummary:
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return _summary(format_name, [])
    sections = _heading_sections(text)
    if sections:
        confidence = "high" if len(sections) >= 2 else "medium"
        sections = _validate_sections(sections)
        return _summary(format_name, sections, front_matter=bool(_FRONT_MATTER_RE.search(text[: max(0, text.find(sections[0].title))])), confidence=confidence)
    return _summary(format_name, _fallback_section(text), confidence="low")


def _extract_pdf_structure(uploaded_file) -> ImportSummary:
    from pypdf import PdfReader

    page_texts = [(page.extract_text() or "").strip() for page in PdfReader(uploaded_file).pages]
    page_texts = [text for text in page_texts if text]
    full_text = "\n\n".join(page_texts)
    page_ranges = []
    cursor = 0
    for page_text in page_texts:
        page_ranges.append((cursor, cursor + len(page_text)))
        cursor += len(page_text) + 2
    sections = _heading_sections(full_text, page_ranges=page_ranges)
    if sections:
        return _summary("pdf", _validate_sections(sections), confidence="high" if len(sections) > 1 else "medium")
    return _summary("pdf", _fallback_section(full_text), confidence="low")


def _epub_document_is_navigation(item, text: str) -> bool:
    name = item.get_name().lower()
    lowered = text.lower()
    return any(marker in name for marker in ("toc", "nav", "contents")) or "table of contents" in lowered


class _XhtmlTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.heading_lines = []
        self._heading = False
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading = True
            self._buffer = []

    def handle_endtag(self, tag):
        if self._heading and tag.lower() in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            value = " ".join("".join(self._buffer).split())
            if value:
                self.heading_lines.append(value)
                self.lines.append(value)
            self._heading = False
            self._buffer = []

    def handle_data(self, data):
        value = " ".join(data.split())
        if not value:
            return
        if self._heading:
            self._buffer.append(value)
        else:
            self.lines.append(value)


def _epub_document_text(item) -> tuple[str, bool]:
    parser = _XhtmlTextParser()
    parser.feed(item.get_content().decode("utf-8", errors="replace"))
    text = "\n".join(
        f"__PAGEBACK_HEADING__ {line}" if line in parser.heading_lines else line
        for line in parser.lines
    )
    return text, _epub_document_is_navigation(item, text)


def _extract_epub_structure(uploaded_file) -> ImportSummary:
    from ebooklib import ITEM_DOCUMENT, epub

    book = epub.read_epub(uploaded_file)
    documents = {item.get_id(): item for item in book.get_items_of_type(ITEM_DOCUMENT)}
    spine_ids = [entry[0] if isinstance(entry, tuple) else entry for entry in book.spine]
    ordered = [documents[item_id] for item_id in spine_ids if item_id in documents]
    ordered.extend(item for item in documents.values() if item not in ordered)
    content_parts = []
    toc_detected = False
    front_matter_detected = False
    for item in ordered:
        text, is_navigation = _epub_document_text(item)
        if not text.strip():
            continue
        if is_navigation:
            toc_detected = True
            continue
        if not content_parts and _FRONT_MATTER_RE.search(text[:1000]):
            front_matter_detected = True
            continue
        content_parts.append(text)
    combined = "\n\n".join(content_parts)
    sections = _heading_sections(combined)
    if sections:
        sections = _validate_sections(sections)
    else:
        sections = _fallback_section(combined)
    confidence = "high" if len(sections) > 1 and any(section.title for section in sections) else "low"
    return _summary("epub", sections, front_matter=front_matter_detected, toc=toc_detected, confidence=confidence)


def extract_book_structure(uploaded_file) -> ImportSummary:
    suffix = Path(uploaded_file.name).suffix.lower()
    uploaded_file.seek(0)
    if suffix in {".txt", ".md"}:
        return _parse_text_document(uploaded_file.read().decode("utf-8"), suffix[1:])
    if suffix == ".pdf":
        return _extract_pdf_structure(uploaded_file)
    if suffix == ".epub":
        return _extract_epub_structure(uploaded_file)
    raise ValueError("Unsupported book format.")


def extract_book_chapters(uploaded_file) -> list[ImportedSection]:
    """Compatibility API returning only validated story sections."""
    return extract_book_structure(uploaded_file).sections