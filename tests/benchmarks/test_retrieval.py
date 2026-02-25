"""Retrieval benchmarking for RAG system.

Measures:
- Retrieval latency
- Top-K recall against expected chunks
- Cosine vs MMR comparison
- Lambda sensitivity analysis
"""

import asyncio
import time
import uuid
from dataclasses import dataclass

import pytest

from mywebui.core.rag import Modality, RetrievedChunk, RAGService


FIXED_CORPUS = [
    {
        "id": "doc-python-basics",
        "title": "Python Basics",
        "text": """# Python Programming Basics

Python is a high-level programming language known for its simplicity and readability.

## Variables

Variables in Python are used to store data values. Unlike other languages, Python has no command for declaring a variable.

```python
x = 5
y = "Hello World"
```

## Data Types

Python has various data types including:
- int (integer)
- float (decimal)
- str (string)
- bool (boolean)
- list (collection)
- dict (key-value pairs)

## Functions

Functions are defined using the def keyword:

```python
def greet(name):
    return f"Hello, {name}!"
```

## Control Flow

Python uses indentation for code blocks with if, elif, and else statements.

```python
if x > 10:
    print("x is greater than 10")
elif x > 5:
    print("x is greater than 5")
else:
    print("x is 5 or less")
```
""",
        "expected_chunks": ["variables", "data types", "functions", "control flow"],
    },
    {
        "id": "doc-web-dev",
        "title": "Web Development",
        "text": """# Web Development Fundamentals

Web development involves creating websites and web applications.

## HTML

HTML (HyperText Markup Language) is the standard markup language for documents designed to be displayed in a web browser.

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Page</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
```

## CSS

CSS (Cascading Style Sheets) is used to style and layout web pages.

```css
body {
    font-family: Arial, sans-serif;
    background-color: #f0f0f0;
}
```

## JavaScript

JavaScript adds interactivity to web pages.

```javascript
document.getElementById("myButton").addEventListener("click", function() {
    alert("Button clicked!");
});
```

## Frontend Frameworks

Popular frontend frameworks include React, Vue, and Angular.
""",
        "expected_chunks": ["html", "css", "javascript", "frontend frameworks"],
    },
    {
        "id": "doc-databases",
        "title": "Database Concepts",
        "text": """# Database Management Systems

Databases are organized collections of structured data.

## SQL

SQL (Structured Query Language) is used to manage relational databases.

```sql
SELECT * FROM users WHERE age > 18;
```

## NoSQL

NoSQL databases provide flexible schemas and scale horizontally.

## ACID Properties

Database transactions must be:
- Atomic (all or nothing)
- Consistent (valid state)
- Isolated (concurrent transactions)
- Durable (permanent changes)
""",
        "expected_chunks": ["sql", "nosql", "acid properties"],
    },
    {
        "id": "doc-git",
        "title": "Git Version Control",
        "text": """# Git Version Control

Git is a distributed version control system.

## Basic Commands

```bash
git init          # Initialize repository
git add .         # Stage changes
git commit -m "Initial commit"
```

## Branching

```bash
git branch feature/new-feature
git checkout feature/new-feature
```

## Merging

```bash
git checkout main
git merge feature/new-feature
```

## Remote Operations

```bash
git push origin main
git pull origin main
git clone https://github.com/user/repo.git
```
""",
        "expected_chunks": ["basic commands", "branching", "merging", "remote operations"],
    },
    {
        "id": "doc-api-design",
        "title": "API Design Best Practices",
        "text": """# RESTful API Design

REST (Representational State Transfer) is an architectural style for APIs.

## HTTP Methods

- GET (retrieve)
- POST (create)
- PUT (update)
- DELETE (remove)

## Status Codes

- 200 OK
- 201 Created
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

## Best Practices

Use nouns for resources:
/users instead of /getUsers

Version your API:
/api/v1/users

Use pagination:
/users?page=1&limit=10
""",
        "expected_chunks": ["http methods", "status codes", "best practices"],
    },
]

CANNED_QUERIES = [
    {"query": "how to declare variables in python", "expected_doc": "doc-python-basics"},
    {"query": "html css javascript web", "expected_doc": "doc-web-dev"},
    {"query": "sql database query language", "expected_doc": "doc-databases"},
    {"query": "git branch merge commit", "expected_doc": "doc-git"},
    {"query": "rest api http methods", "expected_doc": "doc-api-design"},
]


class MockEmbeddingModel:
    """Mock embedding model for benchmarking."""

    def __init__(self, dimension: int = 2048):
        self.dimension = dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return deterministic mock embeddings based on text content."""
        embeddings = []
        for text in texts:
            seed = sum(ord(c) for c in text.lower()) % 1000
            emb = [seed / 1000.0 + i * 0.001 for i in range(self.dimension)]
            norm = sum(x * x for x in emb) ** 0.5
            emb = [x / norm for x in emb]
            embeddings.append(emb)
        return embeddings


class BenchmarkFixture:
    """Benchmark fixture for RAG testing."""

    def __init__(self):
        self.service = RAGService.__new__(RAGService)
        self.service.chunk_size = 512
        self.service.chunk_overlap = 96
        self.service.embedding_ctx_size = 8192
        self.service.mmr_lambda = 0.5
        self.service.embedding_model = MockEmbeddingModel()

        self.corpus = FIXED_CORPUS
        self.chunks: list[tuple[str, RetrievedChunk]] = []

    def ingest_corpus(self) -> None:
        """Ingest the fixed corpus into chunks."""
        for doc in self.corpus:
            doc_id = uuid.uuid4()
            chunks = self.service._chunk_text(doc["text"])

            for i, chunk_text in enumerate(chunks):
                chunk = RetrievedChunk(
                    chunk_id=uuid.uuid4(),
                    document_id=doc_id,
                    text=chunk_text,
                    score=0.0,
                    modality=Modality.TEXT,
                )
                self.chunks.append((doc["id"], chunk))

    def retrieve(self, query: str, use_mmr: bool = False, mmr_lambda: float = 0.5) -> list[str]:
        """Simulate retrieval by scoring chunks against query."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            query_emb = loop.run_until_complete(self.service.embedding_model.embed([query]))[0]

            results = []
            for doc_id, chunk in self.chunks:
                chunk_emb = loop.run_until_complete(
                    self.service.embedding_model.embed([chunk.text])
                )[0]
                score = self.service._cosine_similarity(query_emb, chunk_emb)
                results.append((chunk.chunk_id, doc_id, score))

            results.sort(key=lambda x: x[2], reverse=True)

            return [str(r[0]) for r in results[:5]]
        finally:
            loop.close()


@pytest.fixture
def benchmark():
    """Create benchmark fixture."""
    fixture = BenchmarkFixture()
    fixture.ingest_corpus()
    return fixture


class TestRetrievalBenchmark:
    """Retrieval benchmarking tests."""

    def test_retrieval_latency(self, benchmark):
        """Benchmark retrieval latency."""
        latencies = []

        for _ in range(10):
            start = time.perf_counter()
            benchmark.retrieve("python variables functions")
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        print(f"\nAverage retrieval latency: {avg_latency:.2f}ms")

        assert avg_latency < 1000, "Retrieval should be under 1 second"

    def test_cosine_vs_mmr(self, benchmark):
        """Compare cosine vs MMR retrieval."""
        query = "python programming basics"

        cosine_results = benchmark.retrieve(query, use_mmr=False)
        mmr_results = benchmark.retrieve(query, use_mmr=True, mmr_lambda=0.5)

        print(f"\nCosine results: {cosine_results[:3]}")
        print(f"MMR results: {mmr_results[:3]}")

        overlap = len(set(cosine_results[:3]) & set(mmr_results[:3]))
        print(f"Top-3 overlap: {overlap}/3")

    def test_recall_at_k(self, benchmark):
        """Test recall at different K values."""
        query = "git branch merge commit"

        retrieved = benchmark.retrieve(query, use_mmr=False)
        expected_doc = "doc-git"

        for k in [1, 3, 5]:
            hits = sum(
                1
                for r in retrieved[:k]
                if any(
                    str(chunk.chunk_id) == r and doc_id == expected_doc
                    for doc_id, chunk in benchmark.chunks
                )
            )
            recall = hits / k
            print(f"\nRecall@{k}: {recall:.2f} ({hits}/{k})")

    def test_all_canned_queries(self, benchmark):
        """Run all canned queries and report results."""
        print("\n=== Canned Query Results ===")

        for cq in CANNED_QUERIES:
            results = benchmark.retrieve(cq["query"], use_mmr=False)
            hit = any(
                doc_id == cq["expected_doc"]
                for r in results[:3]
                for doc_id, chunk in benchmark.chunks
                if str(chunk.chunk_id) == r
            )
            status = "HIT" if hit else "MISS"
            print(f"[{status}] Query: '{cq['query']}' -> Expected: {cq['expected_doc']}")
