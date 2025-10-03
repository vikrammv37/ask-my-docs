from typing import Dict, List, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from app.core.config import settings
from app.services.document_service import DocumentService
from app.models.schemas import SourceDocument

class QueryService:
    def __init__(self):
        # Only initialize if API key is provided
        if settings.OPENAI_API_KEY:
            self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            self.llm = ChatOpenAI(
                model="gpt-4",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0
            )
        else:
            self.embeddings = None
            self.llm = None
        self.document_service = DocumentService()
    
    async def query(
        self, 
        question: str, 
        document_id: Optional[str] = None,
        max_results: int = 4
    ) -> Dict[str, Any]:
        """Query documents and get answer"""
        if not self.llm or not self.embeddings:
            raise Exception("OpenAI API key not configured")
            
        if document_id:
            # Query specific document
            vector_store = self.document_service.get_vector_store(document_id)
        else:
            # Query all documents (combine vector stores)
            vector_store = await self._get_combined_vector_store()
        
        # Create retriever
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": max_results}
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # Get answer
        result = qa_chain.invoke({"query": question})
        
        # Process sources
        sources = []
        for doc in result.get("source_documents", []):
            sources.append(SourceDocument(
                content=doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                source=doc.metadata.get("source", "Unknown"),
                page=doc.metadata.get("page"),
                score=0.8  # Placeholder score
            ))
        
        return {
            "answer": result["result"],
            "sources": sources,
            "confidence": self._calculate_confidence(result)
        }
    
    async def _get_combined_vector_store(self):
        """Combine all vector stores for global search"""
        documents = await self.document_service.list_documents()
        
        if not documents:
            raise Exception("No documents found")
        
        # For now, just return the first document's vector store
        # In production, you'd want to properly combine multiple vector stores
        first_doc = documents[0]
        return self.document_service.get_vector_store(first_doc["document_id"])
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate confidence score based on result quality"""
        # Placeholder confidence calculation
        # In production, you'd implement proper scoring based on:
        # - Retrieval scores
        # - Answer length and coherence
        # - Source document relevance
        return 0.85
