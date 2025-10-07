import React, { useState, useEffect } from 'react';
import FileUpload from '../components/FileUpload';
import ChatInterface from '../components/ChatInterface';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import { documentService } from '../services/api';

const HomePage: React.FC = () => {
  const [currentDocumentId, setCurrentDocumentId] = useState<string | undefined>();
  const [currentFilename, setCurrentFilename] = useState<string>('');

  // Check for existing documents on component mount
  useEffect(() => {
    const checkExistingDocuments = async () => {
      try {
        const documents = await documentService.listDocuments();
        if (documents && documents.length > 0) {
          // Use the most recent document
          const latestDoc = documents[0];
          setCurrentDocumentId(latestDoc.document_id);
          setCurrentFilename(latestDoc.filename);
        } else {
          // Clear any stale frontend state
          setCurrentDocumentId(undefined);
          setCurrentFilename('');
        }
      } catch (error) {
        console.error('Failed to check existing documents:', error);
        // Clear stale state on error
        setCurrentDocumentId(undefined);
        setCurrentFilename('');
      }
    };

    checkExistingDocuments();
  }, []);

  const handleUploadSuccess = (documentId: string, filename: string) => {
    setCurrentDocumentId(documentId);
    setCurrentFilename(filename);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <DocumentTextIcon className="h-10 w-10 text-primary-600" />
            <h1 className="text-4xl font-bold text-gray-900">Ask My Docs</h1>
          </div>
          <p className="text-lg text-gray-600">
            Upload documents and ask questions using AI-powered search
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Panel - Upload */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Upload Document
              </h2>
              <FileUpload onUploadSuccess={handleUploadSuccess} />
            </div>

            {currentFilename && (
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Current Document
                </h3>
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <DocumentTextIcon className="h-5 w-5 text-green-600" />
                  <span className="text-green-800 font-medium">
                    {currentFilename}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Chat */}
          <div className="card h-[600px]">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Ask Questions
            </h2>
            <ChatInterface documentId={currentDocumentId} />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-500">
          <p>
            Powered by OpenAI GPT-4 and LangChain • Built with FastAPI and React
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
