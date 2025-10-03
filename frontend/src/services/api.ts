import axios from 'axios';
import type { Document, QueryRequest, QueryResponse, DocumentUploadResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
console.log('API_BASE_URL:', API_BASE_URL); // Debug log

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

console.log('Full API Base URL:', `${API_BASE_URL}/api/v1`); // Debug log

// Request interceptor for auth token (if needed)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const documentService = {
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  async listDocuments(): Promise<Document[]> {
    const response = await api.get('/documents');
    return response.data.documents;
  },

  async deleteDocument(documentId: string): Promise<void> {
    await api.delete(`/documents/${documentId}`);
  },
};

export const queryService = {
  async queryDocuments(query: QueryRequest): Promise<QueryResponse> {
    const response = await api.post('/query', query);
    return response.data;
  },
};

export const healthService = {
  async checkHealth(): Promise<{ status: string; version: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};
