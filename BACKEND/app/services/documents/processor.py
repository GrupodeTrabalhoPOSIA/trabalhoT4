"""Validação, normalização e chunking de documentos."""

import hashlib
import re
import unicodedata
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.documents import DocumentChunk, ProcessedDocument
from app.services.documents.extractors import EXTRACTORS

ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
}


class DocumentProcessor:
    """Converte um arquivo válido em chunks determinísticos e rastreáveis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def process(
        self,
        *,
        filename: str,
        content: bytes,
        content_type: str | None,
        known_hashes: set[str] | None = None,
    ) -> ProcessedDocument:
        extension = Path(filename).suffix.lower()
        self._validate_file(
            filename=filename,
            extension=extension,
            content=content,
            content_type=content_type,
        )

        content_hash = hashlib.sha256(content).hexdigest()
        if known_hashes and content_hash in known_hashes:
            raise AppError(
                status_code=409,
                code="DUPLICATE_DOCUMENT",
                message="Este documento já existe na base de conhecimento.",
            )

        sections = EXTRACTORS[extension].extract(content)
        normalized_sections = [
            (self.normalize_text(section.content), section.page) for section in sections
        ]
        normalized_sections = [section for section in normalized_sections if section[0]]
        if not normalized_sections:
            raise AppError(
                status_code=422,
                code="EMPTY_DOCUMENT",
                message="O documento não possui texto extraível.",
            )

        document_id = str(uuid5(NAMESPACE_URL, content_hash))
        chunks: list[DocumentChunk] = []
        chunk_index = 0
        for text, page in normalized_sections:
            for chunk_content in self.split_text(text):
                chunk_id = str(uuid5(NAMESPACE_URL, f"{document_id}:{chunk_index}"))
                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=document_id,
                        document_name=Path(filename).name,
                        document_type=extension.removeprefix("."),
                        content=chunk_content,
                        chunk_index=chunk_index,
                        page=page,
                    )
                )
                chunk_index += 1

        return ProcessedDocument(
            id=document_id,
            name=Path(filename).name,
            document_type=extension.removeprefix("."),
            content_hash=content_hash,
            file_size=len(content),
            chunks=chunks,
        )

    def _validate_file(
        self,
        *,
        filename: str,
        extension: str,
        content: bytes,
        content_type: str | None,
    ) -> None:
        if len(filename) > 255 or "\x00" in filename:
            raise AppError(
                status_code=422,
                code="INVALID_FILE_NAME",
                message="O nome do arquivo é inválido.",
            )
        if not filename.strip() or extension not in EXTRACTORS:
            raise AppError(
                status_code=415,
                code="UNSUPPORTED_FILE_TYPE",
                message="Formato não suportado. Use PDF, TXT, Markdown ou DOCX.",
            )
        if not content:
            raise AppError(
                status_code=422,
                code="EMPTY_FILE",
                message="O arquivo enviado está vazio.",
            )
        if len(content) > self.settings.max_upload_size_mb * 1024 * 1024:
            raise AppError(
                status_code=413,
                code="FILE_TOO_LARGE",
                message=f"O arquivo deve ter no máximo {self.settings.max_upload_size_mb} MB.",
            )
        normalized_mime = (content_type or "application/octet-stream").split(";", 1)[0].lower()
        if normalized_mime not in ALLOWED_MIME_TYPES[extension]:
            raise AppError(
                status_code=415,
                code="INVALID_MIME_TYPE",
                message="O conteúdo do arquivo não corresponde ao formato informado.",
            )

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normaliza Unicode e espaços preservando limites de parágrafo."""
        normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n")
        normalized = re.sub(r"[\t\f\v ]+", " ", normalized)
        normalized = re.sub(r" *\n *", "\n", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    def split_text(self, text: str) -> list[str]:
        """Divide texto por caracteres, preferindo fronteiras de palavras."""
        if len(text) <= self.settings.chunk_size:
            return [text]

        chunks: list[str] = []
        start = 0
        text_length = len(text)
        while start < text_length:
            proposed_end = min(start + self.settings.chunk_size, text_length)
            end = proposed_end
            if proposed_end < text_length:
                boundary = text.rfind(" ", start + self.settings.chunk_size // 2, proposed_end)
                if boundary > start:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_length:
                break
            start = max(end - self.settings.chunk_overlap, start + 1)

        return chunks
