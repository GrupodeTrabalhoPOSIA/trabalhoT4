/** Documento apresentado na base de conhecimento. */
export interface KnowledgeDocument {
  id: string;
  name: string;
  type: 'pdf' | 'txt' | 'md' | 'docx';
  chunkCount: number;
  size: number;
  createdAt: string;
}

/** Contrato recebido dos endpoints FastAPI de documentos. */
export interface DocumentApiResponse {
  id: string;
  name: string;
  document_type: 'pdf' | 'txt' | 'md' | 'docx';
  chunk_count: number;
  file_size: number;
  created_at: string;
}

/** Texto persistido no backend, sem embeddings. */
export interface DocumentContentResponse {
  id: string;
  chunks: { content: string; chunk_index: number; page: number | null }[];
}

/** Mensagem transitória exibida após uma ação. */
export interface DocumentFeedback {
  kind: 'success' | 'error';
  message: string;
}
