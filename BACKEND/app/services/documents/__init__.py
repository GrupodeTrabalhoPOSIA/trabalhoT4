"""Pipeline de documentos da base de conhecimento."""

from app.services.documents.processor import DocumentProcessor
from app.services.documents.service import DocumentService

__all__ = ["DocumentProcessor", "DocumentService"]
