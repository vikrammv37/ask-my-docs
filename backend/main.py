from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
import uvicorn
import os
import tempfile
import uuid
from datetime import datetime
from typing import List, Dict, Any
import logging

# Simple imports for RAG implementation
try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain.schema import Document
    import openai
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"LangChain not available: {e}")
    LANGCHAIN_AVAILABLE = False

import PyPDF2
import io

# Initialize FastAPI app
app = FastAPI(
    title="Ask My Docs API",
    description="RAG-based document Q&A system",
    version="1.0.0"
)

# Add CORS middleware - Fix for Netlify frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://askyourdocs.netlify.app",  # Production frontend
        "http://localhost:3000",            # Dev frontend
        "http://localhost:5173",            # Vite dev server
        "*"                                 # Allow all for debugging
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global storage for documents and vector store
document_store = {}
vector_store = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using PyPDF2"""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        logger.info(f"PDF has {len(pdf_reader.pages)} pages")
        
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            logger.info(f"Page {i+1} extracted {len(page_text)} characters")
            text += page_text + "\n"
            
        logger.info(f"Total PDF text extracted: {len(text)} characters")
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return f"PDF extraction failed: {str(e)}"

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks"""
    if LANGCHAIN_AVAILABLE:
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            return text_splitter.split_text(text)
        except:
            pass
    
    # Fallback simple chunking
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1  # +1 for space
        
        if current_length >= chunk_size:
            chunks.append(" ".join(current_chunk))
            # Keep some overlap
            overlap_words = current_chunk[-20:] if len(current_chunk) > 20 else current_chunk
            current_chunk = overlap_words
            current_length = sum(len(w) + 1 for w in overlap_words)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

async def get_openai_response(question: str, context: str) -> str:
    """Get response from OpenAI using the context"""
    try:
        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        
        if LANGCHAIN_AVAILABLE:
            try:
                # Use LangChain if available
                llm = ChatOpenAI(
                    model="gpt-4",
                    temperature=0,
                    openai_api_key=api_key
                )
                
                prompt = f"""Answer the question based on the following context. If the answer cannot be found in the context, say "I cannot find the answer in the provided documents."

Context: {context}

Question: {question}

Answer:"""
                
                response = llm.predict(prompt)
                return response
            except Exception as e:
                logger.error(f"LangChain error: {e}")
        
        # Fallback to direct OpenAI API call
        import openai
        openai.api_key = api_key
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that answers questions based on provided context. If you cannot find the answer in the context, say so clearly."
                },
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nQuestion: {question}"
                }
            ],
            temperature=0,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"Error getting AI response: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Ask My Docs API is running!"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "2.0.0", 
        "deployment": "rag-implemented",
        "documents_loaded": len(document_store),
        "langchain_available": LANGCHAIN_AVAILABLE
    }

@app.get("/check-env")
async def check_environment():
    """Check environment variables and OpenAI key status"""
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    
    return {
        "openai_key_set": len(openai_key) > 0,
        "openai_key_length": len(openai_key),
        "openai_key_preview": openai_key[:8] + "..." if len(openai_key) > 8 else "NOT SET",
        "port": os.environ.get("PORT", "NOT SET"),
        "environment": os.environ.get("ENVIRONMENT", "NOT SET"),
        "python_path": os.environ.get("PYTHONPATH", "NOT SET")
    }

@app.get("/test-simple")  
async def test_simple():
    return {"message": "Simple endpoint working", "status": "ok"}

@app.get("/test-cors")
async def test_cors(request: Request):
    """Test CORS headers are working"""
    return Response(
        content='{"message": "CORS test successful"}',
        media_type="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "X-Test-Header": "CORS-Working"
        }
    )

@app.get("/api/v1/test-route")
async def test_route():
    return {"message": "This route is working!", "timestamp": "2025-03-10"}

@app.get("/debug-routes")
async def debug_all_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({"path": route.path, "methods": list(route.methods)})
    return {"available_routes": routes}

@app.get("/api/v1/documents")
async def list_documents():
    """List all uploaded documents"""
    documents = []
    for doc_id, doc_info in document_store.items():
        documents.append({
            "document_id": doc_id,
            "filename": doc_info["filename"],
            "upload_time": doc_info["upload_time"],
            "chunk_count": len(doc_info["chunks"]),
            "text_length": len(doc_info["content"])
        })
    return {"documents": documents, "total_count": len(documents)}

@app.get("/api/v1/debug/documents")
async def debug_documents():
    """Debug endpoint to check document store details"""
    debug_info = []
    for doc_id, doc_info in document_store.items():
        debug_info.append({
            "document_id": doc_id,
            "filename": doc_info["filename"],
            "upload_time": doc_info["upload_time"],
            "chunk_count": len(doc_info["chunks"]),
            "text_length": len(doc_info["content"]),
            "text_preview": doc_info["content"][:500] + "..." if len(doc_info["content"]) > 500 else doc_info["content"],
            "first_chunk_preview": doc_info["chunks"][0][:200] + "..." if doc_info["chunks"] and len(doc_info["chunks"][0]) > 200 else (doc_info["chunks"][0] if doc_info["chunks"] else "No chunks")
        })
    return {
        "document_store_keys": list(document_store.keys()),
        "total_documents": len(document_store),
        "documents_detail": debug_info
    }

# Direct route registration (simpler, more reliable)
@app.options("/api/v1/documents/upload")
async def upload_options():
    """Handle CORS preflight for upload endpoint"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document for Q&A"""
    try:
        # Validate file type
        allowed_types = {
            'application/pdf': ['.pdf'],
            'text/plain': ['.txt'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/msword': ['.doc']
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload PDF, TXT, DOC, or DOCX files."
            )
        
        # Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
            
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        # Process the document
        start_time = datetime.now()
        document_id = str(uuid.uuid4())
        
        # Extract text based on file type
        text_content = ""
        
        if file.content_type == 'application/pdf':
            text_content = extract_text_from_pdf(content)
        elif file.content_type == 'text/plain':
            text_content = content.decode('utf-8')
        elif file.content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            # For DOCX files - basic implementation
            try:
                import docx
                doc_file = io.BytesIO(content)
                doc = docx.Document(doc_file)
                text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            except:
                text_content = "Could not extract text from Word document. Please try converting to PDF or TXT format."
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the document")
        
        # Chunk the text
        chunks = chunk_text(text_content)
        
        # Store document information
        document_store[document_id] = {
            "filename": file.filename,
            "content": text_content,
            "chunks": chunks,
            "upload_time": datetime.now().isoformat()
        }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Processed document {file.filename}: {len(chunks)} chunks, {len(text_content)} chars")
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "success", 
            "message": f"Document processed successfully. Created {len(chunks)} text chunks.",
            "processing_time": processing_time,
            "chunks_created": len(chunks),
            "text_length": len(text_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@app.post("/api/v1/query")
async def query_documents(query_request: dict):
    """Query processed documents using RAG"""
    try:
        question = query_request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        if not document_store:
            return {
                "answer": "No documents have been uploaded yet. Please upload a document first.",
                "sources": [],
                "confidence": 0.0,
                "processing_time": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        start_time = datetime.now()
        
        # Simple similarity search - find relevant chunks
        all_chunks = []
        chunk_sources = []
        
        for doc_id, doc_info in document_store.items():
            for i, chunk in enumerate(doc_info["chunks"]):
                all_chunks.append(chunk.lower())
                chunk_sources.append({
                    "document_id": doc_id,
                    "filename": doc_info["filename"],
                    "chunk_index": i,
                    "content": chunk
                })
        
        # Simple keyword-based relevance scoring
        question_words = set(question.lower().split())
        chunk_scores = []
        
        for i, chunk in enumerate(all_chunks):
            chunk_words = set(chunk.split())
            # Calculate overlap score
            overlap = len(question_words.intersection(chunk_words))
            total_words = len(question_words.union(chunk_words))
            similarity_score = overlap / total_words if total_words > 0 else 0
            chunk_scores.append((similarity_score, i))
        
        # Get top 3 most relevant chunks
        chunk_scores.sort(reverse=True)
        top_chunks = chunk_scores[:3]
        
        # Build context from top chunks
        context_parts = []
        sources_used = []
        
        for score, idx in top_chunks:
            if score > 0.1:  # Minimum relevance threshold
                source = chunk_sources[idx]
                context_parts.append(source["content"])
                sources_used.append({
                    "document_id": source["document_id"],
                    "filename": source["filename"],
                    "chunk_index": source["chunk_index"],
                    "content": source["content"][:200] + "..." if len(source["content"]) > 200 else source["content"],
                    "relevance_score": score
                })
        
        if not context_parts:
            return {
                "answer": "I couldn't find relevant information in the uploaded documents to answer your question.",
                "sources": [],
                "confidence": 0.0,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
        
        context = "\n\n".join(context_parts)
        
        # Get AI response
        ai_answer = await get_openai_response(question, context)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "answer": ai_answer,
            "sources": sources_used,
            "confidence": min(top_chunks[0][0] * 2, 1.0) if top_chunks else 0.0,  # Normalize confidence
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )

# Routes are now registered directly on the app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT", "development") == "development"
    )
