# Multimodal Retrieval

## Query Types

| Query | Embedding Model | Process |
|-------|-----------------|---------|
| Text | Text embedding | Query → embed → similarity search |
| Image | Image embedding | Upload → embed → similarity search |
| Mixed | Both | Separate searches → merge scores |

## Retrieval Process

1. Receive query (text or image)
2. Determine modality
3. Generate embedding using appropriate model
4. Execute similarity search (cosine) with ACL filter
5. Merge results if multiple modalities
6. Return chunks with source attribution

## Score Merging

When mixing modalities:
- Normalize scores to [0, 1]
- Weight by modality (configurable, default 0.5/0.5)
- Rerank by combined score

## Source Attribution

Each retrieved chunk includes:
- Document title
- Document ID
- Chunk index
- Similarity score

Displayed in UI as clickable citations.

## Libraries

- **Vector search**: sqlite-vec
- **Image embeddings**: Configured image embedding model
