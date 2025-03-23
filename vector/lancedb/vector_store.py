#!/usr/bin/env python
"""
LanceDB vector store implementation for Engram memory system.
This provides similar functionality to the FAISS vector store
but uses LanceDB for better cross-platform performance.
"""

import os
import json
import time
import logging
import numpy as np
import pyarrow as pa
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import lancedb

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("lancedb_vector_store")

# Add Engram to path for imports
ENGRAM_DIR = str(Path(__file__).parent.parent.parent)
import sys
if ENGRAM_DIR not in sys.path:
    sys.path.insert(0, ENGRAM_DIR)
    logger.debug(f"Added {ENGRAM_DIR} to Python path")

# Import simple embedding generator
try:
    from vector.test.simple_embedding import SimpleEmbedding
    logger.info("Using simple embedding generator")
except ImportError:
    logger.warning("Simple embedding module not found, creating local copy")
    
    # Create a local copy of SimpleEmbedding
    class SimpleEmbedding:
        """
        A simple embedding generator using TF-IDF like approach.
        This is NOT meant to be a production-grade embedding system,
        but rather a demonstration of embedding generation without
        dependencies on libraries that may have NumPy version conflicts.
        """
        
        def __init__(self, vector_size: int = 128, seed: int = 42):
            """
            Initialize the simple embedding generator
            
            Args:
                vector_size: Dimension of the generated embeddings
                seed: Random seed for reproducibility
            """
            self.vector_size = vector_size
            self.seed = seed
            self.vocab: Dict[str, np.ndarray] = {}
            self.rng = np.random.RandomState(seed)
            
        def _tokenize(self, text: str) -> List[str]:
            """
            Simple tokenization by splitting on non-alphanumeric characters
            and converting to lowercase
            """
            import re
            text = text.lower()
            tokens = re.findall(r'\b\w+\b', text)
            return tokens
        
        def _get_or_create_token_vector(self, token: str) -> np.ndarray:
            """Generate a stable vector for a token"""
            if token not in self.vocab:
                # Generate a stable random vector for this token
                # We use the hash of the token to seed the random generator
                # This ensures the same token always gets the same vector
                token_hash = hash(token) % 2**32
                token_rng = np.random.RandomState(token_hash)
                self.vocab[token] = token_rng.randn(self.vector_size).astype(np.float32)
            return self.vocab[token]
        
        def encode(self, texts: Union[str, List[str]], 
                normalize: bool = True) -> np.ndarray:
            """
            Encode text(s) into fixed-size vectors using a simple TF-IDF
            like approach with random vectors for words.
            
            Args:
                texts: Text or list of texts to encode
                normalize: Whether to normalize the vectors to unit length
                
            Returns:
                Numpy array of embeddings with shape (n_texts, vector_size)
            """
            if isinstance(texts, str):
                texts = [texts]
                
            result = np.zeros((len(texts), self.vector_size), dtype=np.float32)
            
            for i, text in enumerate(texts):
                tokens = self._tokenize(text)
                if not tokens:
                    continue
                    
                # Create the embedding by averaging token vectors
                token_vectors = np.stack([self._get_or_create_token_vector(t) for t in tokens])
                
                # Apply TF component (token frequency)
                token_counts = {}
                for token in tokens:
                    token_counts[token] = token_counts.get(token, 0) + 1
                
                # Calculate embedding as weighted average of token vectors
                embedding = np.zeros(self.vector_size, dtype=np.float32)
                for token, count in token_counts.items():
                    # Higher weight for tokens that appear less frequently in this document
                    # (similar to TF-IDF concept, but very simplified)
                    weight = 1.0 / (1.0 + np.log(count))
                    embedding += weight * self._get_or_create_token_vector(token)
                
                # Store the result
                result[i] = embedding
            
            # Normalize if requested
            if normalize:
                norms = np.linalg.norm(result, axis=1, keepdims=True)
                # Avoid division by zero
                norms = np.maximum(norms, 1e-10)
                result = result / norms
                
            return result
        
        def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
            """Calculate cosine similarity between two embeddings"""
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

class VectorStore:
    """
    A vector store implementation using LanceDB for high-performance similarity search.
    Works well on Apple Silicon and CUDA-enabled hardware.
    """
    
    def __init__(self, 
                data_path: str = "vector_data", 
                dimension: int = 128,
                use_gpu: bool = False) -> None:
        """
        Initialize the vector store
        
        Args:
            data_path: Directory to store vector database
            dimension: Dimension of the vectors to store
            use_gpu: Whether to use GPU acceleration if available
        """
        self.data_path = data_path
        self.dimension = dimension
        self.use_gpu = use_gpu
        self.embedding = SimpleEmbedding(vector_size=dimension)
        self.metadata_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.db = None
        
        # Create data directory if it doesn't exist
        os.makedirs(data_path, exist_ok=True)
        
        # Initialize LanceDB
        try:
            # Make sure the directory exists first
            os.makedirs(data_path, exist_ok=True)
            
            # Connect to LanceDB
            # Use URI format for consistency and better path handling
            db_uri = f"file://{os.path.abspath(data_path)}"
            self.db = lancedb.connect(db_uri)
            logger.info(f"LanceDB initialized at {data_path}")
            logger.info(f"LanceDB version: {lancedb.__version__}")
            logger.info(f"PyArrow version: {pa.__version__}")
            logger.info(f"NumPy version: {np.__version__}")
            
            # Verify connection by listing tables
            _ = self.db.table_names()
            
            if use_gpu:
                # Check if GPU support is available
                try:
                    import torch
                    if torch.cuda.is_available():
                        logger.info(f"GPU support available: {torch.cuda.get_device_name(0)}")
                    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        logger.info(f"Apple Metal support available")
                    else:
                        logger.warning("No GPU support available for torch, using CPU")
                        self.use_gpu = False
                except ImportError:
                    logger.warning("PyTorch not available, using CPU mode")
                    self.use_gpu = False
            
        except Exception as e:
            logger.error(f"Failed to initialize LanceDB: {e}")
            logger.error(f"Attempted to connect to: {data_path}")
            # Retry with a simpler approach as fallback
            try:
                self.db = lancedb.connect(data_path)
                logger.info(f"LanceDB initialized with fallback approach")
                _ = self.db.table_names()  # Verify connection
            except Exception as retry_error:
                logger.error(f"Fallback initialization also failed: {retry_error}")
                self.db = None
    
    def _get_schema(self) -> pa.Schema:
        """Get PyArrow schema for the table"""
        return pa.schema([
            pa.field("id", pa.int64()),
            pa.field("text", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), self.dimension)),
            pa.field("timestamp", pa.float64()),
            # Metadata fields will be added dynamically
        ])
    
    def _get_metadata_path(self, compartment: str) -> str:
        """Get the path for storing a compartment's metadata cache"""
        return os.path.join(self.data_path, f"{compartment}_metadata.json")
    
    def _load_metadata_cache(self, compartment: str) -> None:
        """Load metadata cache from disk"""
        metadata_path = self._get_metadata_path(compartment)
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    self.metadata_cache[compartment] = json.load(f)
                logger.info(f"Loaded metadata cache for '{compartment}' with {len(self.metadata_cache[compartment])} items")
            except Exception as e:
                logger.error(f"Failed to load metadata cache for '{compartment}': {e}")
                self.metadata_cache[compartment] = []
        else:
            self.metadata_cache[compartment] = []
    
    def _save_metadata_cache(self, compartment: str) -> None:
        """Save metadata cache to disk"""
        if compartment not in self.metadata_cache:
            return
            
        metadata_path = self._get_metadata_path(compartment)
        try:
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata_cache[compartment], f)
            logger.info(f"Saved metadata cache for '{compartment}'")
        except Exception as e:
            logger.error(f"Failed to save metadata cache for '{compartment}': {e}")
    
    def create_compartment(self, compartment: str) -> bool:
        """Create a new compartment (table in LanceDB)"""
        if not self.db:
            logger.error("Database not initialized")
            return False
            
        try:
            # Check if table already exists
            try:
                table_names = self.db.table_names()
                if compartment in table_names:
                    logger.info(f"Compartment '{compartment}' already exists")
                    # Load metadata cache if not already loaded
                    if compartment not in self.metadata_cache:
                        self._load_metadata_cache(compartment)
                    return True
            except Exception as e:
                logger.warning(f"Error checking existing tables: {e}")
                # Proceed with creation attempt
                
            # Create a minimal table with required fields
            empty_table = pa.Table.from_pydict(
                {
                    "id": [0],
                    "text": ["initialization placeholder"],
                    "vector": [[0.0] * self.dimension],
                    "timestamp": [time.time()]
                }
            )
            
            # First try to open the table to see if it exists
            try:
                self.db.open_table(compartment)
                logger.info(f"Table '{compartment}' exists but wasn't listed")
                exists = True
            except:
                exists = False
                
            if not exists:
                # Create the table
                try:
                    self.db.create_table(compartment, empty_table)
                    logger.info(f"Created new compartment '{compartment}'")
                except Exception as create_err:
                    logger.error(f"Error creating table: {create_err}")
                    # If table creation failed due to existing table, we can still proceed
                    if "already exists" not in str(create_err):
                        raise
            
            # Initialize metadata cache with the placeholder
            self.metadata_cache[compartment] = [{
                "id": 0,
                "text": "initialization placeholder",
                "timestamp": time.time(),
                "placeholder": True
            }]
            self._save_metadata_cache(compartment)
            
            return True
        except Exception as e:
            logger.error(f"Failed to create compartment '{compartment}': {e}")
            return False
    
    def get_compartments(self) -> List[str]:
        """Get all compartment names"""
        if not self.db:
            logger.error("Database not initialized")
            return []
            
        try:
            return self.db.table_names()
        except Exception as e:
            logger.error(f"Failed to get compartments: {e}")
            return []
    
    def add(self, compartment: str, texts: List[str],
            metadatas: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add texts and their metadata to the vector store
        
        Args:
            compartment: The compartment to add to
            texts: The texts to add
            metadatas: Optional metadata associated with each text
            
        Returns:
            List of IDs assigned to the added texts
        """
        if not self.db:
            logger.error("Database not initialized")
            # Try to reinitialize the database
            try:
                # Make sure the directory exists
                os.makedirs(self.data_path, exist_ok=True)
                # Try to connect again
                self.db = lancedb.connect(os.path.abspath(self.data_path))
                logger.info(f"Successfully reinitialized database at {self.data_path}")
            except Exception as e:
                logger.error(f"Failed to reinitialize database: {e}")
                return []
                
        if not texts:
            return []
            
        # Ensure metadata is provided for each text
        if metadatas is None:
            metadatas = [{} for _ in texts]
        elif len(metadatas) != len(texts):
            raise ValueError(f"Number of texts ({len(texts)}) and metadata ({len(metadatas)}) must match")
            
        try:
            # Create compartment if it doesn't exist
            # Since get_compartments might fail if DB connection is unstable,
            # we'll try to create it directly and handle any errors
            try:
                if compartment not in self.get_compartments():
                    self.create_compartment(compartment)
            except Exception as e:
                logger.warning(f"Error checking compartments: {e}")
                # Try to create it anyway
                self.create_compartment(compartment)
                
            # Load metadata cache if not already loaded
            if compartment not in self.metadata_cache:
                self._load_metadata_cache(compartment)
                
            # Convert texts to embeddings
            embeddings = self.embedding.encode(texts)
            
            # Current count in the index
            start_id = 1  # Start from 1 since 0 is the placeholder
            if compartment in self.metadata_cache and self.metadata_cache[compartment]:
                start_id = max(item["id"] for item in self.metadata_cache[compartment]) + 1
                
            # Generate IDs
            ids = list(range(start_id, start_id + len(texts)))
            
            # Prepare data for LanceDB
            timestamp = time.time()
            data = {
                "id": ids,
                "text": texts,
                "vector": embeddings.tolist(),
                "timestamp": [timestamp] * len(texts)
            }
            
            # Add metadata fields - create empty fields for all possible metadata keys
            all_keys = set()
            for meta in metadatas:
                all_keys.update(meta.keys())
                
            # Add each metadata field with appropriate values for each record
            for key in all_keys:
                data[key] = [meta.get(key, None) for meta in metadatas]
                
            # Create Arrow table
            table = pa.Table.from_pydict(data)
            
            # Add to LanceDB
            try:
                db_table = self.db.open_table(compartment)
                db_table.add(table)
            except Exception as table_err:
                logger.error(f"Failed to add to table: {table_err}")
                # Try to create the table first if it doesn't exist or has schema issues
                if "Table does not exist" in str(table_err) or "schema mismatch" in str(table_err).lower():
                    logger.info(f"Creating table '{compartment}' with new schema")
                    try:
                        self.db.create_table(compartment, table)
                    except Exception as create_err:
                        logger.error(f"Failed to create table: {create_err}")
                        # Still keep track in metadata cache even if DB operation failed
                        # This allows us to have some fallback functionality
                        self.metadata_cache[compartment] = self.metadata_cache.get(compartment, [])
                        for i, (text, meta) in enumerate(zip(texts, metadatas)):
                            entry = {
                                "id": ids[i],
                                "text": text,
                                "timestamp": timestamp,
                                **meta
                            }
                            self.metadata_cache[compartment].append(entry)
                        self._save_metadata_cache(compartment)
                        return ids
                else:
                    raise
            
            # Add to metadata cache
            for i, (text, meta) in enumerate(zip(texts, metadatas)):
                entry = {
                    "id": ids[i],
                    "text": text,
                    "timestamp": timestamp,
                    **meta
                }
                self.metadata_cache[compartment].append(entry)
                
            # Save metadata cache
            self._save_metadata_cache(compartment)
            
            logger.info(f"Added {len(texts)} texts to compartment '{compartment}'")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add texts to compartment '{compartment}': {e}")
            # Fallback to metadata-only operation if database failed
            try:
                # Generate IDs and save to metadata cache only
                start_id = 1
                if compartment in self.metadata_cache and self.metadata_cache[compartment]:
                    start_id = max(item["id"] for item in self.metadata_cache[compartment]) + 1
                ids = list(range(start_id, start_id + len(texts)))
                
                # Initialize cache for this compartment if needed
                self.metadata_cache[compartment] = self.metadata_cache.get(compartment, [])
                
                # Add metadata entries
                timestamp = time.time()
                for i, (text, meta) in enumerate(zip(texts, metadatas)):
                    entry = {
                        "id": ids[i],
                        "text": text,
                        "timestamp": timestamp,
                        **meta
                    }
                    self.metadata_cache[compartment].append(entry)
                    
                # Save metadata cache
                self._save_metadata_cache(compartment)
                
                logger.warning(f"Added {len(texts)} texts to metadata cache only (DB operation failed)")
                return ids
            except Exception as fallback_err:
                logger.error(f"Fallback metadata-only operation also failed: {fallback_err}")
                return []
    
    def save(self, compartment: str) -> bool:
        """
        Save the compartment explicitly (forces an immediate flush)
        """
        if not self.db:
            logger.error("Database not initialized")
            return False
            
        try:
            if compartment not in self.get_compartments():
                logger.warning(f"Compartment '{compartment}' doesn't exist, nothing to save")
                return False
                
            # LanceDB auto-saves, but we can force a metadata cache save
            self._save_metadata_cache(compartment)
            
            # Optional: compact the table
            try:
                db_table = self.db.open_table(compartment)
                db_table.compact()
                logger.info(f"Compacted compartment '{compartment}'")
            except Exception as e:
                logger.warning(f"Failed to compact compartment '{compartment}': {e}")
                
            logger.info(f"Saved compartment '{compartment}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save compartment '{compartment}': {e}")
            return False
    
    def text_search(self, query: str, compartment: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for text matches in the vector store
        
        Args:
            query: The search query
            compartment: The compartment to search in
            top_k: Number of results to return
            
        Returns:
            List of matching documents with metadata and scores
        """
        if not self.db:
            logger.error("Database not initialized")
            return []
            
        try:
            if compartment not in self.get_compartments():
                logger.warning(f"Compartment '{compartment}' doesn't exist")
                return []
                
            # Load metadata cache if not already loaded
            if compartment not in self.metadata_cache:
                self._load_metadata_cache(compartment)
                
            # Convert to lowercase for case-insensitive matching
            query_lower = query.lower()
            
            results = []
            for entry in self.metadata_cache[compartment]:
                if query_lower in entry["text"].lower():
                    # Format the result
                    results.append({
                        "id": entry["id"],
                        "text": entry["text"],
                        "score": 1.0,  # Exact match gets perfect score
                        "metadata": {k: v for k, v in entry.items() 
                                    if k not in ["id", "text", "timestamp"]}
                    })
                
                if len(results) >= top_k:
                    break
                    
            return results
            
        except Exception as e:
            logger.error(f"Failed to search in compartment '{compartment}': {e}")
            return []
    
    def vector_search(self, query: str, compartment: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar texts using vector similarity
        
        Args:
            query: The search query
            compartment: The compartment to search in
            top_k: Number of results to return
            
        Returns:
            List of matching documents with metadata and scores
        """
        if not self.db:
            logger.error("Database not initialized")
            return []
            
        try:
            if compartment not in self.get_compartments():
                logger.warning(f"Compartment '{compartment}' doesn't exist")
                return []
                
            # Create query embedding
            query_embedding = self.embedding.encode(query)[0].tolist()
            
            # Use LanceDB for vector search
            try:
                db_table = self.db.open_table(compartment)
                
                # Skip the placeholder record (id=0) in search
                search_query = db_table.search(query_embedding)
                
                # Check if the table is empty (except for placeholder)
                table_empty = len(db_table.to_pandas()) <= 1
                if table_empty:
                    logger.warning(f"Compartment '{compartment}' is empty (has only placeholder)")
                    return []
                    
                # Get search results and then filter out placeholder with pandas
                search_results = search_query.limit(top_k + 1).to_pandas()
                search_results = search_results[search_results["id"] != 0].head(top_k)
                
                # If no results (could happen if only placeholder exists)
                if search_results.empty:
                    return []
                
                # Format results
                results = []
                for _, row in search_results.iterrows():
                    # Get metadata
                    metadata = {k: v for k, v in row.items() 
                               if k not in ["id", "text", "vector", "timestamp", "_distance"]}
                    
                    # Calculate score (convert distance to similarity score)
                    # LanceDB returns L2 distance, so we convert to a similarity score
                    # where 1.0 is most similar and 0.0 is least similar
                    max_distance = 10.0  # Arbitrary max distance to normalize
                    score = max(0.0, 1.0 - (row["_distance"] / max_distance))
                    
                    # Add to results
                    results.append({
                        "id": int(row["id"]),
                        "text": row["text"],
                        "score": score,
                        "metadata": metadata
                    })
                    
                return results
            except Exception as table_err:
                logger.error(f"Table search error: {table_err}")
                # If the table exists but is empty/corrupted, use metadata cache as fallback
                if compartment in self.metadata_cache and len(self.metadata_cache[compartment]) > 1:
                    logger.warning(f"Using metadata cache as fallback for '{compartment}'")
                    non_placeholder = [item for item in self.metadata_cache[compartment] if item.get("id", 0) != 0]
                    return [{
                        "id": item["id"],
                        "text": item["text"],
                        "score": 0.5,  # Arbitrary score for fallback results
                        "metadata": {k: v for k, v in item.items() 
                                    if k not in ["id", "text", "timestamp"]}
                    } for item in non_placeholder[:top_k]]
                return []
            
        except Exception as e:
            logger.error(f"Failed to perform vector search in compartment '{compartment}': {e}")
            return []
    
    def get_by_id(self, memory_id: int, compartment: str) -> Optional[Dict[str, Any]]:
        """
        Get a memory by its ID
        
        Args:
            memory_id: The ID of the memory
            compartment: The compartment to look in
            
        Returns:
            The memory if found, None otherwise
        """
        if not self.db:
            logger.error("Database not initialized")
            return None
            
        try:
            if compartment not in self.get_compartments():
                logger.warning(f"Compartment '{compartment}' doesn't exist")
                return None
                
            # Load metadata cache if not already loaded
            if compartment not in self.metadata_cache:
                self._load_metadata_cache(compartment)
                
            # Look in metadata cache first for faster retrieval
            for entry in self.metadata_cache[compartment]:
                if entry["id"] == memory_id:
                    return {
                        "id": entry["id"],
                        "text": entry["text"],
                        "metadata": {k: v for k, v in entry.items() 
                                    if k not in ["id", "text", "timestamp"]}
                    }
                    
            # Not found in cache, query the database
            db_table = self.db.open_table(compartment)
            result = db_table.to_pandas(filter=f"id = {memory_id}")
            
            if len(result) > 0:
                row = result.iloc[0]
                return {
                    "id": int(row["id"]),
                    "text": row["text"],
                    "metadata": {k: v for k, v in row.items() 
                               if k not in ["id", "text", "vector", "timestamp"]}
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get memory by ID in compartment '{compartment}': {e}")
            return None
    
    def delete(self, compartment: str) -> bool:
        """Delete a compartment and its files"""
        if not self.db:
            logger.error("Database not initialized")
            return False
            
        try:
            if compartment not in self.get_compartments():
                logger.warning(f"Compartment '{compartment}' doesn't exist")
                return False
                
            # Delete the table
            self.db.drop_table(compartment)
            
            # Delete metadata cache
            if compartment in self.metadata_cache:
                del self.metadata_cache[compartment]
                
            # Delete metadata cache file
            metadata_path = self._get_metadata_path(compartment)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                
            logger.info(f"Deleted compartment '{compartment}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete compartment '{compartment}': {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Create a vector store
    store = VectorStore(data_path="./test_vector_data", dimension=64)
    
    # Add some texts to the "test" compartment
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Vector search allows semantic matching of text",
        "Python is a popular programming language for data science",
        "LanceDB is a vector database built on Apache Arrow"
    ]
    metadatas = [
        {"category": "phrase", "source": "common"},
        {"category": "definition", "source": "ml"},
        {"category": "technology", "source": "search"},
        {"category": "technology", "source": "programming"},
        {"category": "technology", "source": "database"}
    ]
    
    store.add("test", texts, metadatas)
    
    # Text search
    print("Text search results for 'vector':")
    results = store.text_search("vector", "test", top_k=3)
    for i, result in enumerate(results):
        print(f"  {i+1}. [{result['score']:.2f}] {result['text']}")
        print(f"     Metadata: {result['metadata']}")
    
    # Vector search
    print("\nVector search results for 'How do I find similar documents?':")
    results = store.vector_search("How do I find similar documents?", "test", top_k=3)
    for i, result in enumerate(results):
        print(f"  {i+1}. [{result['score']:.2f}] {result['text']}")
        print(f"     Metadata: {result['metadata']}")
    
    # Get by ID
    if results:
        memory_id = results[0]["id"]
        print(f"\nGet memory by ID {memory_id}:")
        memory_result = store.get_by_id(memory_id, "test")
        print(f"  Text: {memory_result['text']}")
        print(f"  Metadata: {memory_result['metadata']}")
    
    # Save the compartment
    store.save("test")
    
    # List compartments
    print(f"\nCompartments: {store.get_compartments()}")