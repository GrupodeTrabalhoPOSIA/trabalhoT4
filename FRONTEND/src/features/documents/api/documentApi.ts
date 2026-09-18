import { apiRequest } from '@/services';
import type {
  DocumentApiResponse,
  DocumentContentResponse,
  KnowledgeDocument,
} from '@/features/documents/types/document';

function toKnowledgeDocument(document: DocumentApiResponse): KnowledgeDocument {
  return {
    id: document.id,
    name: document.name,
    type: document.document_type,
    chunkCount: document.chunk_count,
    size: document.file_size,
    createdAt: document.created_at,
  };
}

export async function listDocuments(signal?: AbortSignal): Promise<KnowledgeDocument[]> {
  const documents = await apiRequest<DocumentApiResponse[]>('/documents', { signal });
  return documents.map(toKnowledgeDocument);
}

export async function uploadDocument(file: File): Promise<KnowledgeDocument> {
  const formData = new FormData();
  formData.append('file', file);
  const document = await apiRequest<DocumentApiResponse>('/documents', {
    method: 'POST',
    body: formData,
  });
  return toKnowledgeDocument(document);
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiRequest<void>(`/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
  });
}

export function getDocumentContent(
  documentId: string,
  signal?: AbortSignal,
): Promise<DocumentContentResponse> {
  return apiRequest<DocumentContentResponse>(
    `/documents/${encodeURIComponent(documentId)}/content`,
    { signal },
  );
}
