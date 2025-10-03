# Ask My Docs - Production RAG Application

A production-ready RAG (Retrieval-Augmented Generation) application built with React.js frontend and FastAPI backend for intelligent document Q&A.

## 🏗️ Architecture

- **Frontend:** React.js with TypeScript, Tailwind CSS, Vite
- **Backend:** FastAPI with Python, async/await patterns
- **Vector Database:** FAISS for document embeddings
- **LLM Integration:** OpenAI GPT-4
- **Deployment:** Docker containers with docker-compose

## 📁 Project Structure

```
ask-my-docs/
├── frontend/              # React.js frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Application pages
│   │   ├── services/      # API service layer
│   │   └── types/         # TypeScript type definitions
│   ├── package.json
│   └── Dockerfile
├── backend/               # FastAPI backend application
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Configuration and utilities
│   │   ├── models/        # Pydantic models
│   │   └── services/      # Business logic services
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml     # Container orchestration
└── .env.example          # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- OpenAI API key

### Development Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repository>
   cd ask-my-docs
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

2. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

3. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker Deployment

1. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📋 Features

### Core Functionality
- **Document Upload:** Support for PDF, TXT, and DOCX files
- **Intelligent Q&A:** Context-aware question answering using RAG
- **Source Citations:** Traceable answers with document references
- **Real-time Chat:** Interactive chat interface with conversation history
- **Multi-document Support:** Query across multiple uploaded documents

### Technical Features
- **Async Processing:** Non-blocking document processing
- **Vector Search:** FAISS-based similarity search
- **API Documentation:** Auto-generated OpenAPI/Swagger docs
- **Error Handling:** Comprehensive error handling and user feedback
- **File Validation:** Secure file upload with size and type restrictions
- **CORS Configuration:** Properly configured cross-origin requests

## 🔧 API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload and process documents
- `GET /api/v1/documents` - List all processed documents
- `DELETE /api/v1/documents/{id}` - Delete a document

### Query Interface
- `POST /api/v1/query` - Query documents and get AI responses

### System
- `GET /health` - Health check endpoint
- `GET /` - API status

## 🛠️ Development

### Backend Development
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
```

### Frontend Development
```bash
cd frontend
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run type checking
npm run type-check
```

## 🔐 Security Considerations

- Store API keys securely using environment variables
- Implement proper authentication for production use
- Configure CORS appropriately for your domain
- Set up rate limiting for API endpoints
- Validate and sanitize file uploads
- Use HTTPS in production

## 📊 Performance Optimization

- **Chunking Strategy:** Optimized text splitting for better retrieval
- **Caching:** Redis integration for session and query caching
- **Async Processing:** Non-blocking I/O for better throughput
- **Connection Pooling:** Efficient database connections
- **CDN Integration:** Serve static assets via CDN

## 🐳 Production Deployment

### Docker Compose (Recommended)
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
1. Set up reverse proxy (Nginx)
2. Configure SSL certificates
3. Set up monitoring (Prometheus, Grafana)
4. Configure log aggregation
5. Set up backup strategies for vector database

## 🔍 Monitoring

- **Health Checks:** Built-in health endpoints
- **Logging:** Structured logging with different levels
- **Metrics:** Request/response times, error rates
- **Alerts:** Set up alerts for critical issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **OpenAI API Key Issues:**
   - Ensure your API key is valid and has sufficient credits
   - Check the `.env` file configuration

2. **Document Processing Fails:**
   - Verify file format is supported (PDF, TXT, DOCX)
   - Check file size limits (default 10MB)
   - Ensure sufficient disk space for uploads

3. **Frontend Cannot Connect to Backend:**
   - Verify backend is running on port 8000
   - Check CORS configuration in backend settings
   - Ensure API_BASE_URL is correctly set

4. **Docker Issues:**
   - Ensure Docker and Docker Compose are installed
   - Check port availability (3000, 8000, 6379)
   - Verify environment variables in docker-compose.yml

### Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Check application logs for error details
4. Create an issue in the repository
