# LanceDB Vector Store

This directory contains the refactored implementation of the LanceDB Vector Store for Engram memory system. The system was previously implemented as a single monolithic file (`vector_store.py`) but has now been refactored into a more modular structure for better maintainability and extensibility.

## Directory Structure

- **base/**: Core implementation 
  - `store.py`: Main VectorStore class implementation
  
- **embedding/**: Embedding generation
  - `simple.py`: Simple embedding generator for when advanced models aren't available
  
- **operations/**: CRUD operations for vector store compartments
  - `crud.py`: Implementation of create, read, update, and delete operations
  
- **search/**: Search functionality
  - `text.py`: Text-based search implementation
  - `vector.py`: Vector similarity search implementation
  
- **utils/**: Utility functions
  - `logging.py`: Logging configuration and utility functions
  - `metadata.py`: Metadata cache management

## Backward Compatibility

The original `vector_store.py` file now serves as a compatibility layer, importing and re-exporting the VectorStore and SimpleEmbedding classes from the new structure. This ensures that existing code using the LanceDB Vector Store will continue to work without modification.

## Usage

The API remains the same as before. Here's a simple example:

```python
from vector.lancedb.vector_store import VectorStore

# Create a vector store
store = VectorStore(data_path="./vector_data", dimension=128)

# Add some texts to a compartment
texts = ["The quick brown fox jumps over the lazy dog", "Vector search enables semantic matching"]
metadatas = [{"source": "example1"}, {"source": "example2"}]
store.add("example_compartment", texts, metadatas)

# Search for similar texts
results = store.vector_search("How do semantic search systems work?", "example_compartment", top_k=3)
for result in results:
    print(f"[{result['score']:.2f}] {result['text']}")
    print(f"Metadata: {result['metadata']}")
```

## Key Features

- **Vector Similarity Search**: Fast and efficient vector-based similarity search
- **Text Search**: Simple text-based search for exact matches
- **Metadata Support**: Full support for arbitrary metadata with each text entry
- **Cross-Platform**: Works well on both CPU and GPU environments
- **Fallback Mechanisms**: Graceful degradation with metadata-only operations if database operations fail
- **Automatic Initialization**: Automatic compartment creation and database initialization