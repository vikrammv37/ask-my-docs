import React, { useState } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { queryService } from '../services/api';
import toast from 'react-hot-toast';
import type { QueryResponse, SourceDocument } from '../types';

interface ChatInterfaceProps {
  documentId?: string;
}

interface ChatMessage {
  id: string;
  question: string;
  answer: string;
  sources: SourceDocument[];
  timestamp: Date;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ documentId }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const currentQuery = query;
    setQuery('');
    setLoading(true);

    try {
      const response: QueryResponse = await queryService.queryDocuments({
        question: currentQuery,
        document_id: documentId,
        max_results: 4
      });

      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        question: currentQuery,
        answer: response.answer,
        sources: response.sources,
        timestamp: new Date()
      };

      setMessages(prev => [newMessage, ...prev]);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Input */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your documents..."
            className="input-field flex-1"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary flex items-center gap-2 px-6"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <PaperAirplaneIcon className="h-4 w-4" />
            )}
            Ask
          </button>
        </div>
      </form>

      {/* Chat Messages */}
      <div className="flex-1 space-y-6 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-12">
            <p>Upload a document and start asking questions!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="card">
              <div className="space-y-4">
                <div>
                  <p className="font-semibold text-gray-900 mb-2">
                    Q: {message.question}
                  </p>
                  <p className="text-gray-700 leading-relaxed">
                    A: {message.answer}
                  </p>
                </div>
                
                {message.sources.length > 0 && (
                  <div className="border-t pt-4">
                    <details className="group">
                      <summary className="cursor-pointer font-medium text-sm text-gray-600 hover:text-gray-900">
                        📚 View Sources ({message.sources.length})
                      </summary>
                      <div className="mt-3 space-y-2">
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="bg-gray-50 p-3 rounded text-sm">
                            <p className="font-medium text-gray-900 mb-1">
                              {source.source}
                            </p>
                            <p className="text-gray-600">
                              {source.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
                
                <p className="text-xs text-gray-400">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
