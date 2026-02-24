# Knowledge Base & RAG (`docs.db`)

> **Note**: Document embeddings live in the shared `docs.db`. Memory/summary embeddings live in per-user `history.db`.

## Libraries

- **ORM**: SQLAlchemy 2.0 (async)
- **Vectors**: sqlite-vec
- **Tokenizer**: tokenizers (Rust-based, primary), tiktoken (optional, OpenAI-compatible only)

## Documents Table

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | UUID | Primary key |
| `owner` | UUID | Foreign key to users |
| `visibility` | enum | `public`, `restricted`, `private` |
| `allowed_users` | JSON | Array of user IDs |
| `allowed_roles` | JSON | Array of roles |
| `categories` | JSON | Array of category strings |
| `source` | string | Original filename/URL |
| `hash` | string | SHA256 of content |
| `title` | string | Document title |
| `created_at` | timestamp | Creation time |
| `updated_at` | timestamp | Last modification |

## ACL Rule (Hard Rule)

A document is visible iff:

```
visibility == public
OR owner == user
OR user ∈ allowed_users
OR user.role ∈ allowed_roles
```

**Invisible documents:**

- Do not appear in UI
- Do not participate in RAG
- Are never embedded
- Are never summarized

---

# Chunks & Multimodal Embeddings

## Chunks Table

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | UUID | Primary key |
| `doc_id` | UUID | Foreign key to documents |
| `modality` | enum | `text`, `image`, `audio`, `video` |
| `text` | text | Extracted text (nullable for non-text) |
| `media_ref` | string | Path to media file (nullable) |
| `chunk_index` | int | Position in document |
| `token_count` | int | Approximate tokens |
| `created_at` | timestamp | Creation time |

## Chunking Strategy

- **Target**: 500-800 tokens
- **Preference order**:
  1. Paragraph breaks
  2. Sentence breaks
  3. Hard token cut (last resort)
- Rationale: Token limits are real; paragraph-only fails on large docs, sentence-only explodes metadata

## Embeddings Table (sqlite-vec)

| Field | Type | Description |
|-------|------|-------------|
| `embedding_id` | UUID | Primary key |
| `chunk_id` | UUID | Foreign key to chunks |
| `model_name` | string | Embedding model used |
| `modality` | enum | `text` or `image` |
| `vector` | blob | Normalized embedding vector |

**Indexes:**
- `idx_embeddings_chunk` on `chunk_id`
- `idx_embeddings_model` on `model_name`
- Vector index for similarity search

Supports:

- Text embeddings
- Image embeddings
- Multiple embeddings per chunk
- Model upgrades without re-ingestion

---

# Vector Engine (Locked)

- SQLite + sqlite-vec
- Metadata + vectors co-located
- SQL-level ACL filtering
- Category filtering
- Required indexes
- Chunk size: **400–800 tokens** (token-based with soft semantic boundaries)

**Similarity metric**: Cosine similarity
- Store normalized vectors → cosine = dot product
- Universal support across backends

No external vector DBs.
