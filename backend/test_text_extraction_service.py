# Tests for TextExtractionService
# Framework: pytest

import pathlib
import io
import pytest
from backend.text_extraction_service import TextExtractionService, ExtractionError

@pytest.fixture
def service():
    return TextExtractionService()

@pytest.fixture
def text_file(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Hello world")
    return p

@pytest.fixture
def pdf_file(tmp_path):
    p = tmp_path / "sample.pdf"
    # write minimal PDF header; actual content is stubbed in tests
    p.write_bytes(b"%PDF-1.4\n%EOF\n")
    return p

@pytest.fixture
def image_file(tmp_path):
    p = tmp_path / "image.png"
    # write minimal PNG header; actual content is stubbed in tests
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    return p

@pytest.fixture
def empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("")
    return p

@pytest.fixture
def corrupt_pdf_bytes():
    return io.BytesIO(b"not a pdf file")

# Happy-path tests for plain text files
@pytest.mark.parametrize("content", ["Hello world", "123", "Multiline\nText"])
def test_extract_plain_text(service, tmp_path, content):
    p = tmp_path / "doc.txt"
    p.write_text(content)
    assert service.extract(p) == content

def test_extract_with_text_file_fixture(service, text_file):
    assert service.extract(text_file) == "Hello world"

# Stub PDF extraction logic
def test_extract_pdf(monkeypatch, service, tmp_path):
    p = tmp_path / "dummy.pdf"
    p.write_bytes(b"%PDF-1.4 dummy")
    monkeypatch.setattr(service, "_extract_pdf", lambda path: "PDF content")
    assert service.extract(p) == "PDF content"

# Stub image extraction logic
def test_extract_image(monkeypatch, service, tmp_path):
    p = tmp_path / "dummy.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(service, "_extract_image", lambda path: "Image text")
    assert service.extract(p) == "Image text"

# Edge-case tests
def test_empty_file_returns_empty_string(service, empty_file):
    assert service.extract(empty_file) == ""

def test_unsupported_extension_raises_error(service, tmp_path):
    p = tmp_path / "file.exe"
    p.write_bytes(b"binary")
    with pytest.raises(ExtractionError):
        service.extract(p)

def test_corrupt_pdf_raises_error(monkeypatch, service, tmp_path):
    p = tmp_path / "bad.pdf"
    p.write_bytes(b"not a valid pdf")
    # stub to raise on corrupt PDF
    def fail_pdf(path):
        raise ExtractionError("Corrupt PDF")
    monkeypatch.setattr(service, "_extract_pdf", fail_pdf)
    with pytest.raises(ExtractionError):
        service.extract(p)

def test_large_file_does_not_crash(service, tmp_path):
    content = "a" * 10**6
    p = tmp_path / "large.txt"
    p.write_text(content)
    result = service.extract(p)
    assert len(result) == len(content)

# Ensure any open resources are cleaned up
@pytest.fixture(autouse=True)
def cleanup_service(service):
    yield service
    if hasattr(service, "close"):
        service.close()