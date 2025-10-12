"""Embeddings-based vendor knowledge memory."""
from typing import List, Dict, Any, Optional
import hashlib
from pathlib import Path
from config.settings import settings


class VendorKnowledgeBase:
    """Embeddings-based knowledge base for vendor categorization history."""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the knowledge base.
        
        Args:
            persist_directory: Directory to persist embeddings data
        """
        if persist_directory is None:
            persist_directory = "./chroma_data"
        
        self.persist_directory = persist_directory
        self.collection_name = "vendor_categorizations"
        
        # Initialize based on vector backend setting
        if settings.vector_backend == "chroma":
            self._init_chroma()
        else:
            self._init_faiss()
    
    def _init_chroma(self):
        """Initialize ChromaDB client."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            self.client = chromadb.Client(ChromaSettings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Vendor categorization history"}
            )
            
            self.backend = "chroma"
        except ImportError:
            print("ChromaDB not available, falling back to FAISS")
            self._init_faiss()
    
    def _init_faiss(self):
        """Initialize FAISS in-memory store."""
        self.backend = "faiss"
        self.memory = []  # Simple in-memory list as fallback
        print("Using in-memory FAISS fallback")
    
    def add_categorization(
        self,
        counterparty: str,
        description: str,
        account: str,
        category: str,
        txn_id: Optional[str] = None
    ):
        """
        Add a categorization to the knowledge base.
        
        Args:
            counterparty: Vendor/counterparty name
            description: Transaction description
            account: Assigned account
            category: Category
            txn_id: Optional transaction ID
        """
        # Create a document from the transaction
        doc_text = f"{counterparty} {description}"
        
        metadata = {
            "counterparty": counterparty,
            "description": description,
            "account": account,
            "category": category,
        }
        
        if txn_id:
            metadata["txn_id"] = txn_id
        
        # Generate a unique ID
        doc_id = hashlib.md5(f"{counterparty}{description}{account}".encode()).hexdigest()[:16]
        
        if self.backend == "chroma":
            try:
                self.collection.add(
                    documents=[doc_text],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
            except Exception as e:
                print(f"Failed to add to ChromaDB: {e}")
        else:
            # FAISS fallback
            self.memory.append({
                "id": doc_id,
                "text": doc_text,
                "metadata": metadata
            })
    
    def find_similar(
        self,
        counterparty: str,
        description: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar past categorizations.
        
        Args:
            counterparty: Vendor/counterparty name
            description: Transaction description
            n_results: Number of similar results to return
            
        Returns:
            List of similar categorizations with metadata
        """
        query_text = f"{counterparty} {description}"
        
        if self.backend == "chroma":
            try:
                results = self.collection.query(
                    query_texts=[query_text],
                    n_results=min(n_results, self.collection.count())
                )
                
                if not results or not results['metadatas']:
                    return []
                
                # Format results
                similar = []
                for i, metadata in enumerate(results['metadatas'][0]):
                    similar.append({
                        'counterparty': metadata.get('counterparty', ''),
                        'account': metadata.get('account', ''),
                        'category': metadata.get('category', ''),
                        'distance': results['distances'][0][i] if 'distances' in results else 0.0
                    })
                
                return similar
            except Exception as e:
                print(f"Failed to query ChromaDB: {e}")
                return []
        else:
            # FAISS fallback - simple string matching
            matches = []
            query_lower = query_text.lower()
            
            for item in self.memory:
                if counterparty.lower() in item['text'].lower():
                    matches.append({
                        'counterparty': item['metadata']['counterparty'],
                        'account': item['metadata']['account'],
                        'category': item['metadata']['category'],
                        'distance': 0.0
                    })
            
            return matches[:n_results]
    
    def get_historical_mappings(
        self,
        counterparty: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get historical counterparty -> account mappings.
        
        Args:
            counterparty: Optional filter by counterparty
            
        Returns:
            List of mappings
        """
        if self.backend == "chroma":
            try:
                # Get all items from collection
                results = self.collection.get()
                
                if not results or not results['metadatas']:
                    return []
                
                mappings = []
                for metadata in results['metadatas']:
                    if counterparty and metadata.get('counterparty', '').lower() != counterparty.lower():
                        continue
                    
                    mappings.append({
                        'counterparty': metadata.get('counterparty', ''),
                        'account': metadata.get('account', '')
                    })
                
                return mappings
            except Exception as e:
                print(f"Failed to get mappings from ChromaDB: {e}")
                return []
        else:
            # FAISS fallback
            mappings = []
            for item in self.memory:
                meta = item['metadata']
                if counterparty and meta['counterparty'].lower() != counterparty.lower():
                    continue
                
                mappings.append({
                    'counterparty': meta['counterparty'],
                    'account': meta['account']
                })
            
            return mappings
    
    def clear(self):
        """Clear all data from the knowledge base."""
        if self.backend == "chroma":
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Vendor categorization history"}
                )
            except Exception as e:
                print(f"Failed to clear ChromaDB: {e}")
        else:
            self.memory = []


# Global instance
vendor_kb = VendorKnowledgeBase()

