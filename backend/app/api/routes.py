from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models.schemas import (
    QueryRequest, QueryResponse, DocumentUploadResponse, ErrorResponse
)
from app.services.document_service import DocumentService
from app.services.query_service import QueryService
from datetime import datetime
import time

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "timestamp": datetime.now()}

# Initialize services lazily to avoid startup errors
document_service = None
query_service = None

def get_document_service():
    global document_service
    if document_service is None:
        try:
            document_service = DocumentService()
        except Exception as e:
            print(f"Error initializing DocumentService: {e}")
            raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")
    return document_service

def get_query_service():
    global query_service
    if query_service is None:
        try:
            query_service = QueryService()
        except Exception as e:
            print(f"Error initializing QueryService: {e}")
            raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")
    return query_service

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document for Q&A"""
    start_time = time.time()
    
    try:
        # Temporary simplified version for debugging
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Basic file validation
        if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large")
        
        processing_time = time.time() - start_time
        
        # Return success response without actual processing for now
        return DocumentUploadResponse(
            document_id=f"temp-{int(time.time())}",
            filename=file.filename or "unknown",
            status="success",
            message="Document upload endpoint is working (processing temporarily disabled)",
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@router.post("/query", response_model=QueryResponse)
async def query_documents(query_request: QueryRequest):
    """Query processed documents"""
    start_time = time.time()
    
    try:
        # Get service instance
        q_service = get_query_service()
        
        result = await q_service.query(
            question=query_request.question,
            document_id=query_request.document_id,
            max_results=query_request.max_results
        )
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            processing_time=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )

@router.get("/documents")
async def list_documents():
    """List all processed documents"""
    try:
        doc_service = get_document_service()
        documents = await doc_service.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a processed document"""
    try:
        doc_service = get_document_service()
        result = await doc_service.delete_document(document_id)
        return {"message": "Document deleted successfully", "document_id": document_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
