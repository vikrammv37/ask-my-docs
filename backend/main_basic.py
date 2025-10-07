from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
from datetime import datetime
import logging
import io
import re

# Simple FastAPI app
app = FastAPI(title="Simple RAG App", version="3.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
documents = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF"""
    try:
        import pypdf
        pdf = pypdf.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except:
        return "Error: Could not extract text from PDF"

def chunk_text(text: str) -> list:
    """Split text into chunks"""
    # Simple chunking by paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    for para in paragraphs:
        if len(para) > 800:
            # Split long paragraphs into sentences
            sentences = re.split(r'[.!?]+', para)
            current = ""
            for sentence in sentences:
                if len(current + sentence) < 800:
                    current += sentence + ". "
                else:
                    if current:
                        chunks.append(current.strip())
                    current = sentence + ". "
            if current:
                chunks.append(current.strip())
        else:
            chunks.append(para)
    
    return chunks

def find_relevant_chunks(question: str, doc_chunks: list) -> list:
    """Find chunks relevant to question"""
    question_words = set(question.lower().split())
    
    scored_chunks = []
    for chunk in doc_chunks:
        chunk_words = set(chunk.lower().split())
        overlap = len(question_words & chunk_words)
        if overlap > 0:
            score = overlap / len(question_words | chunk_words)
            scored_chunks.append((score, chunk))
    
    # Return top 3 chunks
    scored_chunks.sort(reverse=True)
    return [chunk for _, chunk in scored_chunks[:3]]

async def get_ai_answer(question: str, context: str) -> str:
    """Get answer from OpenAI"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OpenAI API key not configured"
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Answer questions based on the provided context. Be concise and helpful."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting AI response: {str(e)}"

# Routes
@app.get("/")
async def root():
    return {"message": "Simple RAG App Running!", "version": "3.0.0"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "documents": len(documents)
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Extract text
        if file.content_type == 'application/pdf':
            text = extract_pdf_text(content)
        elif file.content_type == 'text/plain':
            text = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files supported")
        
        if not text or text.startswith("Error:"):
            raise HTTPException(status_code=400, detail=f"Text extraction failed: {text}")
        
        # Create chunks
        chunks = chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="No text chunks created")
        
        # Store document
        doc_id = str(uuid.uuid4())
        documents[doc_id] = {
            "id": doc_id,
            "filename": file.filename,
            "text": text,
            "chunks": chunks,
            "uploaded": datetime.now().isoformat()
        }
        
        logger.info(f"Uploaded {file.filename}: {len(chunks)} chunks")
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "chunks": len(chunks),
            "message": f"Successfully uploaded {file.filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_docs(request: dict):
    """Query uploaded documents"""
    try:
        question = request.get("question", "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question required")
        
        if not documents:
            return {
                "answer": "Please upload a document first before asking questions.",
                "success": False
            }
        
        # Get all chunks from all documents
        all_chunks = []
        for doc in documents.values():
            all_chunks.extend(doc["chunks"])
        
        # Find relevant chunks
        relevant_chunks = find_relevant_chunks(question, all_chunks)
        
        if not relevant_chunks:
            return {
                "answer": "I couldn't find relevant information to answer your question.",
                "success": False
            }
        
        # Create context
        context = "\n\n".join(relevant_chunks)
        
        # Get AI answer
        answer = await get_ai_answer(question, context)
        
        return {
            "answer": answer,
            "success": True,
            "sources_used": len(relevant_chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_docs():
    """List uploaded documents"""
    docs = []
    for doc in documents.values():
        docs.append({
            "id": doc["id"],
            "filename": doc["filename"], 
            "chunks": len(doc["chunks"]),
            "uploaded": doc["uploaded"]
        })
    return {"documents": docs, "count": len(docs)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
