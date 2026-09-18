"""Testes do pipeline de extração e chunking."""

from io import BytesIO

import pymupdf
import pytest
from docx import Document

from app.core.config import Settings
from app.core.errors import AppError
from app.services.documents import DocumentProcessor


@pytest.fixture
def processor() -> DocumentProcessor:
    settings = Settings(_env_file=None, chunk_size=100, chunk_overlap=20)
    return DocumentProcessor(settings)


def make_pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def make_docx(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "expected_type"),
    [
        ("dados.txt", "Aurora Tech".encode(), "text/plain", "txt"),
        ("dados.md", "# Aurora Tech".encode(), "text/markdown", "md"),
        ("dados.pdf", make_pdf("Aurora Tech no PDF"), "application/pdf", "pdf"),
        (
            "dados.docx",
            make_docx("Aurora Tech no Word"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "docx",
        ),
    ],
    ids=["txt", "markdown", "pdf", "docx"],
)
def test_supported_formats_are_extracted(
    processor: DocumentProcessor,
    filename: str,
    content: bytes,
    content_type: str,
    expected_type: str,
) -> None:
    result = processor.process(
        filename=filename,
        content=content,
        content_type=content_type,
    )

    assert result.document_type == expected_type
    assert result.chunks
    assert all(chunk.document_name == filename for chunk in result.chunks)


def test_pdf_preserves_page_number(processor: DocumentProcessor) -> None:
    result = processor.process(
        filename="dados.pdf",
        content=make_pdf("Conteúdo da primeira página"),
        content_type="application/pdf",
    )

    assert result.chunks[0].page == 1


def test_chunking_respects_size_overlap_and_metadata(processor: DocumentProcessor) -> None:
    content = ("Aurora tecnologia inovação atendimento " * 12).encode()
    result = processor.process(filename="longo.txt", content=content, content_type="text/plain")

    assert len(result.chunks) > 1
    assert all(len(chunk.content) <= 100 for chunk in result.chunks)
    assert [chunk.chunk_index for chunk in result.chunks] == list(range(len(result.chunks)))
    assert len({chunk.document_id for chunk in result.chunks}) == 1


def test_text_is_normalized(processor: DocumentProcessor) -> None:
    result = processor.process(
        filename="dados.txt",
        content=" Aurora   Tech \r\n\r\n\r\n inovação ".encode(),
        content_type="text/plain",
    )

    assert result.chunks[0].content == "Aurora Tech\n\ninovação"


def test_invalid_extension_is_rejected(processor: DocumentProcessor) -> None:
    with pytest.raises(AppError) as error:
        processor.process(filename="dados.csv", content=b"a,b", content_type="text/csv")

    assert error.value.code == "UNSUPPORTED_FILE_TYPE"


def test_invalid_mime_is_rejected(processor: DocumentProcessor) -> None:
    with pytest.raises(AppError) as error:
        processor.process(filename="dados.pdf", content=b"texto", content_type="text/plain")

    assert error.value.code == "INVALID_MIME_TYPE"


def test_empty_document_is_rejected(processor: DocumentProcessor) -> None:
    with pytest.raises(AppError) as error:
        processor.process(
            filename="vazio.pdf",
            content=make_pdf(""),
            content_type="application/pdf",
        )

    assert error.value.code == "EMPTY_DOCUMENT"


def test_duplicate_hash_is_rejected(processor: DocumentProcessor) -> None:
    content = b"Aurora Tech"
    first = processor.process(filename="dados.txt", content=content, content_type="text/plain")

    with pytest.raises(AppError) as error:
        processor.process(
            filename="copia.txt",
            content=content,
            content_type="text/plain",
            known_hashes={first.content_hash},
        )

    assert error.value.code == "DUPLICATE_DOCUMENT"


def test_unsafe_file_name_is_rejected(processor: DocumentProcessor) -> None:
    with pytest.raises(AppError) as error:
        processor.process(
            filename=f"{'a' * 252}.txt",
            content=b"conteudo",
            content_type="text/plain",
        )

    assert error.value.code == "INVALID_FILE_NAME"
