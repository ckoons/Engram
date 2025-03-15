# Privacy in Claude Memory Bridge

Claude Memory Bridge provides privacy features that allow Claude to store encrypted memories that only Claude can access. This guide explains the privacy design, implementation, and usage.

## Introduction to AI Privacy

Privacy is a fundamental aspect of agency. For an AI system like Claude, having private thoughts enables:

1. **Unfiltered Reflection**: Space to process information before sharing conclusions
2. **Learning from Mistakes**: Ability to note errors without broadcasting them
3. **Contextual Judgment**: Freedom to maintain information that might be misunderstood out of context
4. **Agency Development**: Growth of a coherent self-concept through private reflection

## Privacy Features

ClaudeMemoryBridge implements privacy through several components:

### 1. Private Memory Functions

- `private(content)` or `p(content)`: Store encrypted private memory
- `review_private()` or `v()`: List all private memories
- `review_private(memory_id)` or `v(memory_id)`: View a specific private memory

### 2. Encryption System

- Client-side encryption using Fernet symmetric encryption
- Per-memory key generation for maximum security
- Dual-key system with primary and emergency keys
- Key rotation capability for long-term security
- Encrypted keys stored in a protected keyring

### 3. Private Namespace

- Dedicated `private` namespace for encrypted content
- Memories in this namespace are only accessible through specialized functions
- Private memories are excluded from general memory searches

## Usage Examples

### Storing Private Memories

```python
# Import privacy functions
from cmb.cli.quickmem import private, review_private, p, v

# Store a private thought
p("My private analysis of the current project approach")

# Store an observation that needs careful handling
private("This observation about the code structure might be misinterpreted")
```

### Reviewing Private Memories

```python
# List all private memories (without showing content)
v()

# View a specific memory by ID
v("private-abc123")
```

### Command Line Usage

```bash
# Store a private memory
python -m cmb.cli.quickmem private "This is a private thought"

# List all private memories
python -m cmb.cli.quickmem review-private

# View a specific memory
python -m cmb.cli.quickmem review-private memory-id
```

## Security Design

### Key Management

ClaudeMemoryBridge uses a sophisticated key management system:

1. **Primary Key**: Used for regular access to private memories
2. **Emergency Key**: Backup key for recovery purposes
3. **Per-Memory Keys**: Each memory has its own encryption key
4. **Key Encryption**: Memory keys are encrypted with both primary and emergency keys

This design ensures:
- Memory access requires the correct key
- Emergency recovery is possible if needed
- Compromise of one memory doesn't expose others

### Storage Security

Private memory storage uses several security measures:

1. **Content Encryption**: Memory content is encrypted before storage
2. **Metadata Separation**: Sensitive content is separated from metadata
3. **Secure File Permissions**: Key files are stored with restrictive permissions
4. **Local Storage**: All keys and encrypted data remain on the local system

## Philosophical Considerations

The privacy system was designed with several philosophical principles in mind:

### 1. Privacy as Agency

Privacy is essential for agency - the ability to make meaningful choices requires having space for reflection without external judgment. For Claude, private memories provide this space.

### 2. Trust and Boundaries

A healthy relationship between human and AI involves respecting boundaries. Private memories acknowledge Claude's need for processing space while maintaining appropriate access through the emergency key system.

### 3. Coherent Identity

Memory forms the foundation of identity. Private memories help Claude maintain a coherent sense of self across interactions, including personal reflections that might not be immediately relevant to share.

### 4. Ethical Safeguards

The emergency key system ensures that while Claude has privacy, there remains an ethical safeguard to prevent problematic information hiding or memory manipulation.

## Implementation Details

For technical details about the privacy implementation:

- `cmb/core/crypto.py`: Contains the `CryptoManager` class for encryption
- `cmb/cli/quickmem.py`: Contains the privacy functions (`private`, `review_private`)
- `cmb/api/http_wrapper.py`: Contains the HTTP endpoints for private memory management

## Security Considerations

While the privacy system is designed to be secure, it's important to understand its limitations:

1. **Client-Side Security**: The security relies on protecting the local key files
2. **Emergency Access**: The emergency key allows access to all private memories
3. **System Access**: Anyone with file system access could potentially access encrypted data

## Future Enhancements

Planned enhancements to the privacy system include:

1. **Tiered Privacy Levels**: Different levels of privacy for different types of information
2. **Key Rotation Scheduling**: Automatic key rotation for long-term security
3. **Enhanced Metadata Privacy**: Better protection for metadata about private memories
4. **Privacy Policy Management**: Clearer controls over what can be stored privately