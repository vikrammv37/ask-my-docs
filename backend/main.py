from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
import uvicorn
import os

# Try to import routes and settings, but don't fail if they have issues
api_router = None
try:
    from app.api.routes import router as api_router
    from app.core.config import settings
    print("Successfully imported routes and settings")
except Exception as e:
    print(f"Failed to import routes or settings: {e}")
    api_router = None

# Initialize FastAPI app
app = FastAPI(
    title="Ask My Docs API",
    description="RAG-based document Q&A system",
    version="1.0.0"
)

# Add CORS middleware - Permissive for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes only if successfully imported
if api_router:
    app.include_router(api_router, prefix="/api/v1")
    print("API routes registered successfully")
else:
    print("API routes not registered due to import failure")

@app.get("/")
async def root():
    return {"message": "Ask My Docs API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/v1/debug")
async def debug_routes():
    return {"message": "API routes are working", "available_routes": ["/api/v1/debug", "/api/v1/test", "/api/v1/documents/upload"]}

@app.post("/api/v1/documents/upload")
async def upload_document_temp(file: UploadFile = File(...)):
    """Temporary upload endpoint for testing"""
    try:
        return {
            "status": "success",
            "message": "File received successfully",
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size if hasattr(file, 'size') else "unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT", "development") == "development"
    )
