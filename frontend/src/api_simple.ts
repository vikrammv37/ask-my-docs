import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Simple API client
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Upload document
export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  console.log('Uploading to:', `${API_BASE_URL}/upload`);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

// Query documents
export const queryDocuments = async (question: string) => {
  const response = await api.post('/query', { question });
  return response.data;
};

// Get documents list
export const getDocuments = async () => {
  const response = await api.get('/documents');
  return response.data;
};

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};
