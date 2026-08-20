from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile

from novels.importers import extract_book_chapters, extract_book_structure


def test_text_import_detects_story_sections_without_page_splitting():
    upload = SimpleUploadedFile(
        "book.txt",
        b"FIRST NIGHT\nThe narrator meets Nastenka.\n\nSECOND NIGHT\nThey speak again.",
    )

    sections = extract_book_chapters(upload)

    assert [section.title for section in sections] == ["First Night", "Second Night"]
    assert [section.content_type for section in sections] == ["section", "section"]


def test_pdf_pages_with_three_story_headings_create_three_sections(monkeypatch):
    class FakeReader:
        def __init__(self, _uploaded_file):
            self.pages = [
                SimpleNamespace(extract_text=lambda: "CHAPTER I\nOpening events."),
                SimpleNamespace(extract_text=lambda: "More of chapter one.\n\nCHAPTER II\nThe conflict begins."),
                SimpleNamespace(extract_text=lambda: "CHAPTER III\nThe section closes."),
                SimpleNamespace(extract_text=lambda: "A continuation page without a heading."),
            ]

    monkeypatch.setattr("pypdf.PdfReader", FakeReader)
    upload = SimpleUploadedFile("book.pdf", b"not a real pdf")

    sections = extract_book_chapters(upload)

    assert len(sections) == 3
    assert [section.title for section in sections] == ["Chapter I", "Chapter Ii", "Chapter Iii"]
    assert sections[0].source_page_start == 1
    assert sections[1].source_page_start == 2
    assert sections[2].source_page_start == 3
    assert "continuation page" in sections[2].content


def test_pdf_without_story_headings_becomes_one_section(monkeypatch):
    class FakeReader:
        def __init__(self, _uploaded_file):
            self.pages = [
                SimpleNamespace(extract_text=lambda: "Title page and contents."),
                SimpleNamespace(extract_text=lambda: "Body text."),
                SimpleNamespace(extract_text=lambda: "More body text."),
            ]

    monkeypatch.setattr("pypdf.PdfReader", FakeReader)
    upload = SimpleUploadedFile("book.pdf", b"not a real pdf")

    sections = extract_book_chapters(upload)

    assert len(sections) == 1
    assert sections[0].title == "Section 1"
    assert sections[0].content_type == "section"
    assert "More body text" in sections[0].content


def test_epub_embedded_cover_is_extracted(monkeypatch):
    from novels import importers

    class FakeImage:
        def get_name(self):
            return "images/book-cover.jpg"

        def get_content(self):
            return b"embedded-cover"

    class FakeBook:
        def get_metadata(self, namespace, name):
            assert (namespace, name) == ("OPF", "cover")
            return [("cover", {"content": "cover-image"})]

        def get_item_with_id(self, item_id):
            assert item_id == "cover-image"
            return FakeImage()

        def get_items_of_type(self, _item_type):
            return [FakeImage()]

    monkeypatch.setattr("ebooklib.epub.read_epub", lambda _file: FakeBook())
    upload = SimpleUploadedFile("book.epub", b"not a real epub")

    cover = importers.extract_book_cover(upload)

    assert cover.name == "book-cover.jpg"
    assert cover.read() == b"embedded-cover"


def test_text_without_cover_uses_fallback_path():
    from novels.importers import extract_book_cover

    upload = SimpleUploadedFile("book.txt", b"Text only")

    assert extract_book_cover(upload) is None


def test_markdown_prologue_chapters_and_epilogue_are_story_sections():
    upload = SimpleUploadedFile(
        "book.md",
        b"# Contents\n\n# Prologue\nA beginning.\n\n## Chapter One\nThe story starts.\n\n# Epilogue\nThe ending.",
    )

    sections = extract_book_chapters(upload)

    assert [section.title for section in sections] == ["Prologue", "Chapter One", "Epilogue"]


def test_named_structural_headings_are_detected_without_matching_prose():
    upload = SimpleUploadedFile(
        "book.txt",
        b"Chapter: The Departure\nThe journey begins.\n\nThis ordinary sentence should not split.\n\nNight - The Return\nThe journey ends.",
    )

    sections = extract_book_chapters(upload)

    assert [section.title for section in sections] == ["Chapter: The Departure", "Night - The Return"]


def test_duplicate_headings_are_validated_without_duplicate_sections():
    upload = SimpleUploadedFile(
        "book.txt",
        b"Chapter 1\nSame text.\n\nChapter 1\nSame text.\n\nChapter 2\nDifferent text.",
    )

    sections = extract_book_chapters(upload)

    assert len(sections) == 2
    assert [section.title for section in sections] == ["Chapter 1", "Chapter 2"]


def test_epub_spine_excludes_toc_and_front_matter(monkeypatch):
    class FakeItem:
        def __init__(self, item_id, name, html):
            self.item_id = item_id
            self.name = name
            self.html = html

        def get_id(self):
            return self.item_id

        def get_name(self):
            return self.name

        def get_content(self):
            return self.html.encode()

    items = [
        FakeItem("cover", "cover.xhtml", "<html><title>Copyright</title><p>Copyright 2020</p></html>"),
        FakeItem("toc", "toc.xhtml", "<html><h1>Table of Contents</h1><a>Chapter 1</a></html>"),
        FakeItem("body", "body.xhtml", "<html><h1>Chapter 1</h1><p>Story content.</p></html>"),
    ]

    class FakeBook:
        spine = [("cover", "yes"), ("toc", "yes"), ("body", "yes")]

        def get_items_of_type(self, _item_type):
            return items

    monkeypatch.setattr("ebooklib.epub.read_epub", lambda _file: FakeBook())
    upload = SimpleUploadedFile("book.epub", b"fake")

    summary = extract_book_structure(upload)

    assert summary.toc_detected is True
    assert summary.front_matter_detected is True
    assert [section.title for section in summary.sections] == ["Chapter 1"]
    assert summary.sections[0].content == "Story content."


def test_epub_multiple_chapters_inside_one_xhtml(monkeypatch):
    class FakeItem:
        def get_id(self):
            return "body"

        def get_name(self):
            return "body.xhtml"

        def get_content(self):
            return b"<html><h1>Chapter 1</h1><p>One.</p><h2>The Departure</h2><p>Two.</p></html>"

    class FakeBook:
        spine = [("body", "yes")]

        def get_items_of_type(self, _item_type):
            return [FakeItem()]

    monkeypatch.setattr("ebooklib.epub.read_epub", lambda _file: FakeBook())
    upload = SimpleUploadedFile("book.epub", b"fake")

    sections = extract_book_chapters(upload)

    assert [section.title for section in sections] == ["Chapter 1", "The Departure"]


def test_epub_one_xhtml_per_chapter_uses_structural_titles(monkeypatch):
    class FakeItem:
        def __init__(self, item_id, title, content):
            self.item_id = item_id
            self.title = title
            self.content = content

        def get_id(self):
            return self.item_id

        def get_name(self):
            return f"{self.item_id}.xhtml"

        def get_content(self):
            return f"<html><title>{self.title}</title><p>{self.content}</p></html>".encode()

    items = [FakeItem("one", "Chapter 1", "One."), FakeItem("two", "Chapter 2", "Two.")]

    class FakeBook:
        spine = [("one", "yes"), ("two", "yes")]

        def get_items_of_type(self, _item_type):
            return items

    monkeypatch.setattr("ebooklib.epub.read_epub", lambda _file: FakeBook())
    upload = SimpleUploadedFile("book.epub", b"fake")

    sections = extract_book_chapters(upload)

    assert [section.title for section in sections] == ["Chapter 1", "Chapter 2"]


def test_epub_part_and_chapter_hierarchy_is_preserved(monkeypatch):
    class FakeItem:
        def get_id(self):
            return "body"

        def get_name(self):
            return "body.xhtml"

        def get_content(self):
            return b"<html><h1>Part I</h1><h2>Chapter 1</h2><p>Story.</p></html>"

    class FakeBook:
        spine = [("body", "yes")]

        def get_items_of_type(self, _item_type):
            return [FakeItem()]

    monkeypatch.setattr("ebooklib.epub.read_epub", lambda _file: FakeBook())
    upload = SimpleUploadedFile("book.epub", b"fake")

    sections = extract_book_chapters(upload)

    assert [section.title for section in sections] == ["Chapter 1"]
    assert sections[0].content_type == "chapter"
    assert sections[0].parent_title == "Part I"