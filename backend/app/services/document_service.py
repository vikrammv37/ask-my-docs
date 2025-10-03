import os
import uuid
import aiofiles
from typing import Dict, List, Any
from fastapi import UploadFile, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.core.config import settings
import json
from datetime import datetime

class DocumentService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.vector_db_path = settings.VECTOR_DB_PATH
        
        # Only initialize embeddings if API key is provided
        if settings.OPENAI_API_KEY:
            self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        else:
            self.embeddings = None
            
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.documents_metadata = {}
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.vector_db_path, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file"""
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            return False
        
        # Check file size (this is approximate, real size check needs to read file)
        return True
    
    async def process_document(self, file: UploadFile) -> Dict[str, Any]:
        """Process uploaded document and create embeddings"""
        if not self.embeddings:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
        document_id = str(uuid.uuid4())
        
        # Save uploaded file
        file_path = os.path.join(self.upload_dir, f"{document_id}_{file.filename}")
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Load and process document
        if file.filename.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            pages = loader.load()
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Split documents
        docs = self.text_splitter.split_documents(pages)
        
        # Add metadata
        for i, doc in enumerate(docs):
            doc.metadata.update({
                "document_id": document_id,
                "filename": file.filename,
                "chunk_id": i,
                "source": f"Page {doc.metadata.get('page', i+1)}"
            })
        
        # Create vector store
        vector_store = FAISS.from_documents(docs, self.embeddings)
        vector_store_path = os.path.join(self.vector_db_path, document_id)
        vector_store.save_local(vector_store_path)
        
        # Save document metadata
        metadata = {
            "document_id": document_id,
            "filename": file.filename,
            "file_path": file_path,
            "vector_store_path": vector_store_path,
            "created_at": datetime.now().isoformat(),
            "chunk_count": len(docs)
        }
        
        metadata_path = os.path.join(self.vector_db_path, f"{document_id}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        return {
            "document_id": document_id,
            "chunk_count": len(docs)
        }
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all processed documents"""
        documents = []
        
        for filename in os.listdir(self.vector_db_path):
            if filename.endswith('_metadata.json'):
                metadata_path = os.path.join(self.vector_db_path, filename)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    documents.append(metadata)
        
        return documents
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a processed document"""
        try:
            # Remove vector store
            vector_store_path = os.path.join(self.vector_db_path, document_id)
            if os.path.exists(vector_store_path):
                import shutil
                shutil.rmtree(vector_store_path)
            
            # Remove metadata
            metadata_path = os.path.join(self.vector_db_path, f"{document_id}_metadata.json")
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
    
    def get_vector_store(self, document_id: str):
        """Load vector store for a document"""
        if not self.embeddings:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
        vector_store_path = os.path.join(self.vector_db_path, document_id)
        if not os.path.exists(vector_store_path):
            raise HTTPException(status_code=404, detail="Document not found")
        
        return FAISS.load_local(vector_store_path, self.embeddings, allow_dangerous_deserialization=True)
