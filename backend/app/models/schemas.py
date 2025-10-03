from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
    processing_time: float

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    document_id: Optional[str] = None
    max_results: int = Field(default=4, ge=1, le=10)

class SourceDocument(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    confidence: float
    processing_time: float
    timestamp: datetime

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
