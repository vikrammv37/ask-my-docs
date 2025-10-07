from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
import os
import uuid
from datetime import datetime
from typing import List, Dict
import logging
import io
import re

# Initialize FastAPI app
app = FastAPI(
    title="Ask My Docs API - Simple RAG",
    description="Basic RAG-based document Q&A system",
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://askyourdocs.netlify.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global storage for documents
document_store = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf_simple(file_content: bytes) -> str:
    """Simple PDF text extraction using pypdf"""
    try:
        import pypdf
        pdf_file = io.BytesIO(file_content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        text = ""
        
        logger.info(f"PDF has {len(pdf_reader.pages)} pages")
        for i, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += page_text + "\n"
            logger.info(f"Page {i+1}: extracted {len(page_text)} characters")
        
        logger.info(f"Total PDF text: {len(text)} characters")
        return text.strip()
        
    except ImportError:
        logger.error("pypdf not available")
        return "PDF processing not available - please install pypdf"
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return f"PDF extraction failed: {str(e)}"

def simple_chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """Simple text chunking by sentences and paragraphs"""
    if not text.strip():
        return []
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If chunks are still too big, split by sentences
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= chunk_size:
            final_chunks.append(chunk)
        else:
            sentences = re.split(r'[.!?]+', chunk)
            temp_chunk = ""
            for sentence in sentences:
                if len(temp_chunk) + len(sentence) < chunk_size:
                    temp_chunk += sentence + ". "
                else:
                    if temp_chunk:
                        final_chunks.append(temp_chunk.strip())
                    temp_chunk = sentence + ". "
            if temp_chunk:
                final_chunks.append(temp_chunk.strip())
    
    return [chunk for chunk in final_chunks if chunk.strip()]

def calculate_similarity(question: str, chunk: str) -> float:
    """Calculate simple word overlap similarity"""
    question_words = set(question.lower().split())
    chunk_words = set(chunk.lower().split())
    
    if not question_words or not chunk_words:
        return 0.0
    
    intersection = question_words.intersection(chunk_words)
    union = question_words.union(chunk_words)
    
    return len(intersection) / len(union) if union else 0.0

async def get_openai_answer(question: str, context: str) -> str:
    """Get answer from OpenAI API"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Based on the following context, answer the question. If the answer cannot be found in the context, say "I cannot find this information in the provided documents."

Context:
{context}

Question: {question}

Answer:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using cheaper model for testing
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"Error getting AI response: {str(e)}"

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.1.0",
        "deployment": "simple-rag",
        "documents_loaded": len(document_store)
    }

# Document upload
@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Extract text
        text_content = ""
        if file.content_type == 'application/pdf':
            text_content = extract_text_from_pdf_simple(content)
        elif file.content_type == 'text/plain':
            text_content = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files supported")
        
        if not text_content or text_content.startswith("PDF extraction failed"):
            raise HTTPException(status_code=400, detail=f"Could not extract text: {text_content}")
        
        # Create chunks
        chunks = simple_chunk_text(text_content)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No text chunks created")
        
        # Store document
        document_store[document_id] = {
            "id": document_id,
            "filename": file.filename,
            "content": text_content,
            "chunks": chunks,
            "upload_time": datetime.now().isoformat()
        }
        
        logger.info(f"Stored document {file.filename}: {len(chunks)} chunks, {len(text_content)} chars")
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "success",
            "message": f"Document processed: {len(chunks)} chunks created",
            "chunks_created": len(chunks),
            "text_length": len(text_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Query documents
@app.post("/api/v1/query") 
async def query_documents(query_data: dict):
    """Query documents with RAG"""
    try:
        question = query_data.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question required")
        
        if not document_store:
            return {
                "answer": "No documents uploaded yet. Please upload a document first.",
                "sources": [],
                "confidence": 0.0,
                "processing_time": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        
        start_time = datetime.now()
        
        # Find relevant chunks
        all_chunks = []
        for doc_id, doc_info in document_store.items():
            for i, chunk in enumerate(doc_info["chunks"]):
                similarity = calculate_similarity(question, chunk)
                all_chunks.append({
                    "similarity": similarity,
                    "chunk": chunk,
                    "document_id": doc_id,
                    "filename": doc_info["filename"],
                    "chunk_index": i
                })
        
        # Sort by similarity and get top chunks
        all_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        top_chunks = all_chunks[:3]
        
        # Filter chunks with minimum similarity
        relevant_chunks = [c for c in top_chunks if c["similarity"] > 0.1]
        
        if not relevant_chunks:
            return {
                "answer": "I couldn't find relevant information in the uploaded documents to answer your question.",
                "sources": [],
                "confidence": 0.0,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
        
        # Build context
        context = "\n\n".join([c["chunk"] for c in relevant_chunks])
        
        # Get AI answer
        ai_answer = await get_openai_answer(question, context)
        
        # Prepare sources
        sources = []
        for c in relevant_chunks:
            sources.append({
                "document_id": c["document_id"],
                "filename": c["filename"], 
                "chunk_index": c["chunk_index"],
                "content": c["chunk"][:200] + "..." if len(c["chunk"]) > 200 else c["chunk"],
                "relevance_score": c["similarity"]
            })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "answer": ai_answer,
            "sources": sources,
            "confidence": relevant_chunks[0]["similarity"] if relevant_chunks else 0.0,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# List documents
@app.get("/api/v1/documents")
async def list_documents():
    """List uploaded documents"""
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

# Debug endpoint
@app.get("/api/v1/debug/documents")
async def debug_documents():
    """Debug document storage"""
    debug_info = []
    for doc_id, doc_info in document_store.items():
        debug_info.append({
            "document_id": doc_id,
            "filename": doc_info["filename"],
            "text_preview": doc_info["content"][:300] + "..." if len(doc_info["content"]) > 300 else doc_info["content"],
            "chunk_count": len(doc_info["chunks"]),
            "first_chunk": doc_info["chunks"][0][:200] + "..." if doc_info["chunks"] else "No chunks"
        })
    
    return {
        "total_documents": len(document_store),
        "document_details": debug_info
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
