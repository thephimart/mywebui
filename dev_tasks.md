# MyWebUI Development Tasks

## Project Status

### Completed Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Config & Token-aware Chunking | ✅ Complete |
| 2.1 | MMR Re-ranking | ✅ Complete |
| 2.2 | Retrieval Benchmarking | ✅ Complete |
| 3.1 | PDF Text Extraction | ✅ Complete |
| 3.2 | PDF Image Metadata Extraction | ✅ Complete |
| 3.3 | PDF Image Bytes Extraction | ✅ Complete |
| 3.4 | VL Embedding Adapter | ✅ Complete |
| 3.5 | Mixed Text+Image Retrieval | ✅ Complete |

### Test Results
- **84 tests passing** (34 RAG + 30 PDF + 16 VL + 4 benchmarks)
- ruff clean
- mypy clean (yaml stubs warning only)

---

## Implemented Features

### RAG Core
- **Token-aware chunking**: 512 tokens, 96 overlap, tiktoken + word×1.3 fallback
- **MMR re-ranking**: Configurable λ (default 0.5)
- **Retrieval benchmarking**: Latency, recall, cosine vs MMR

### PDF Processing
- **Text extraction**: Per-page text, full text, page markers
- **Image metadata**: Page, bbox, dimensions, format
- **Image bytes**: Raw bytes extraction (PDFImageBytes)

### VL Embedding
- **BaseVLEmbeddingModel**: Abstract base class
- **OpenAICompatibleVLEmbeddingModel**: /v1/embeddings compatible
- **ImageInput**: Dataclass for image bytes + format

### Multimodal Retrieval
- **Modality enum**: TEXT, IMAGE, MIXED
- **RetrievalMode**: TEXT_ONLY, IMAGE_ONLY, HYBRID
- **Query-driven detection**: Auto-detects modality from query
- **Weighted merge**: text_weight (0.7) / image_weight (0.3)
- **Multimodal MMR**: Extended for images and hybrid

---

## Future Tasks

### Phase 3.6: Cross-Modal Similarity (Optional Enhancement)

**Goal**: Enable meaningful cross-modality similarity scoring.

**Tasks**:
- [ ] Implement `_cross_modality_similarity()` with learned joint space
- [ ] Add CLIP-style encoder for joint text-image embeddings
- [ ] Consider learned weighting instead of static 0.7/0.3

**Notes**: This is optional. Current implementation returns 0.0 for cross-modality similarity, which is a safe placeholder.

---

### Phase 4: Storage Layer Optimization

**Goal**: Separate text and image vector storage with hybrid ANN indexes.

**Tasks**:
- [ ] Add separate tables/indexes for image embeddings
- [ ] Implement hybrid ANN (Approximate Nearest Neighbor) indexes
- [ ] Add query-time budget allocation (e.g., "search 5 text, 3 images")
- [ ] Optimize for combined text+image queries

---

### Phase 5: UI & Explainability

**Goal**: Surface multimodal results with citations and explanations.

**Tasks**:
- [ ] Add image preview in retrieval results
- [ ] Implement "why this was retrieved" explanations
- [ ] Add confidence scores and relevance indicators
- [ ] Support mixed text+image result display

---

### Known Technical Debt

| Issue | Severity | Notes |
|-------|----------|-------|
| Pydantic class-based config deprecation | Low | Use ConfigDict instead |
| Asyncio event loop in tests | Low | Use pytest-asyncio properly |
| YAML stubs missing | Low | `types-PyYAML` optional |

---

## Architecture Constraints (LOCKED)

| ✅ Do | ❌ Don't |
|-------|---------|
| Chunk size 512 / overlap 96 | Add joint embeddings prematurely |
| tiktoken with fallback | Skip modality gating |
| Embedding dimension 2048 | Hardcode scoring weights |
| Config-driven settings | Mix storage with retrieval |
| MMR λ=0.5 default | Skip benchmarking |

---

## File Organization

```
src/mywebui/
├── config.py              # RAGConfig, ModalityConfig
├── core/
│   ├── models.py          # Chat, Embedding, VL models
│   ├── rag.py            # Chunking, retrieval, MMR
│   └── pdf.py            # PDF text, image extraction
tests/
├── test_rag.py           # 34 tests
├── test_pdf.py           # 30 tests
├── test_vl_embedding.py  # 16 tests
└── benchmarks/
    └── test_retrieval.py # 4 benchmark tests
```
