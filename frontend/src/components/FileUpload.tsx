import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';
import { documentService } from '../services/api';
import toast from 'react-hot-toast';

interface FileUploadProps {
  onUploadSuccess: (documentId: string, filename: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    
    try {
      const response = await documentService.uploadDocument(file);
      toast.success('Document uploaded successfully!');
      onUploadSuccess(response.document_id, response.filename);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'}
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} disabled={uploading} />
        
        <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        
        {uploading ? (
          <div className="space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-600">Processing document...</p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop the document here' : 'Upload a document'}
            </p>
            <p className="text-sm text-gray-500">
              Drag and drop a PDF, TXT, or DOCX file here, or click to browse
            </p>
            <p className="text-xs text-gray-400">
              Maximum file size: 10MB
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
