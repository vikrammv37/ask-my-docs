from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
import uvicorn
import os

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

# We'll define routes directly in this file to avoid import issues

@app.get("/")
async def root():
    return {"message": "Ask My Docs API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.3", "deployment": "router-fix"}

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

# Create a router for API v1 routes
api_v1_router = APIRouter(prefix="/api/v1")

@api_v1_router.options("/documents/upload")
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

@api_v1_router.post("/documents/upload")
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
        
        # For now, just return success without actual processing
        # TODO: Implement actual document processing with LangChain
        
        import time
        import uuid
        
        document_id = str(uuid.uuid4())
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "success", 
            "message": "Document uploaded successfully",
            "processing_time": 0.5
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@api_v1_router.post("/query")
async def query_documents(query_request: dict):
    """Query processed documents"""
    try:
        question = query_request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
            
        # For now, return a mock response
        # TODO: Implement actual RAG query processing
        
        import time
        from datetime import datetime
        
        return {
            "answer": f"This is a mock response to your question: '{question}'. The actual RAG functionality will be implemented once document processing is working.",
            "sources": [
                {
                    "document_id": "temp_doc",
                    "filename": "sample.pdf",
                    "page": 1,
                    "content": "Sample source content"
                }
            ],
            "confidence": 0.85,
            "processing_time": 0.3,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )

# Register the API v1 router
app.include_router(api_v1_router)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT", "development") == "development"
    )
