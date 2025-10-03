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

# Initialize services
document_service = DocumentService()
query_service = QueryService()

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document for Q&A"""
    start_time = time.time()
    
    try:
        # Validate file
        if not document_service.validate_file(file):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type or size"
            )
        
        # Process document
        result = await document_service.process_document(file)
        processing_time = time.time() - start_time
        
        return DocumentUploadResponse(
            document_id=result["document_id"],
            filename=file.filename,
            status="success",
            message="Document processed successfully",
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
        result = await query_service.query(
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
        documents = await document_service.list_documents()
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
        result = await document_service.delete_document(document_id)
        return {"message": "Document deleted successfully", "document_id": document_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
