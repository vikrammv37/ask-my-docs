export interface Document {
  document_id: string;
  filename: string;
  created_at: string;
  chunk_count: number;
}

export interface SourceDocument {
  content: string;
  source: string;
  page?: number;
  score: number;
}

export interface QueryRequest {
  question: string;
  document_id?: string;
  max_results?: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceDocument[];
  confidence: number;
  processing_time: number;
  timestamp: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
  processing_time: number;
}

export interface ApiError {
  error: string;
  message: string;
  timestamp: string;
}
