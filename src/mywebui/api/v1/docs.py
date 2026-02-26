"""Docs API routes for document management and RAG."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mywebui.core.rag import get_rag_service
from mywebui.db import connection
from mywebui.db.models import Document

router = APIRouter()


class DocumentCreate(BaseModel):
    """Document creation request."""

    title: str
    content: str
    visibility: str = "private"
    categories: list[str] = []
    source: str | None = None


class DocumentUpdate(BaseModel):
    """Document update request."""

    title: str | None = None
    visibility: str | None = None
    categories: list[str] | None = None
    allowed_users: list[str] | None = None
    allowed_roles: list[str] | None = None


class DocumentResponse(BaseModel):
    """Document response."""

    id: str
    title: str
    visibility: str
    categories: list[str]
    source: str | None
    created_at: datetime
    updated_at: datetime | None


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: list[DocumentResponse]
    total: int


class SearchRequest(BaseModel):
    """Search request."""

    query: str
    limit: int = 5
    category: str | None = None


class SearchResult(BaseModel):
    """Search result."""

    chunk_id: str
    document_id: str
    text: str
    score: float
    modality: str


async def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return {
        "user_id": request.state.user_id,
        "username": request.state.username,
    }


@router.post("/ingest", response_model=DocumentResponse)
async def ingest_document(
    request: DocumentCreate,
    http_request: Request,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Ingest a new document."""
    rag_service = get_rag_service()

    doc = await rag_service.ingest_document(
        db,
        owner_id=current["user_id"],
        title=request.title,
        text=request.content,
        visibility=request.visibility,
        categories=request.categories,
        source=request.source,
    )

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        visibility=doc.visibility,
        categories=doc.categories,
        source=doc.source,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    http_request: Request,
    current: dict = Depends(get_current_user),
    visibility: str | None = None,
    category: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """List documents accessible to the user."""
    query = select(Document)

    conditions = []
    conditions.append((Document.visibility == "public") | (Document.owner_id == current["user_id"]))

    if visibility:
        conditions.append(Document.visibility == visibility)

    if category:
        conditions.append(Document.categories.contains([category]))

    query = query.where(*conditions)

    count_result = await db.execute(select(Document).where(*conditions))
    total = len(count_result.scalars().all())

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=d.id,
                title=d.title,
                visibility=d.visibility,
                categories=d.categories,
                source=d.source,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in documents
        ],
        total=total,
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    http_request: Request,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Get a document by ID."""
    result = await db.execute(select(Document).where(Document.id == str(doc_id)))
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if not _can_access_doc(doc, current["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        visibility=doc.visibility,
        categories=doc.categories,
        source=doc.source,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.patch("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    request: DocumentUpdate,
    http_request: Request,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Update a document."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if str(doc.owner_id) != current["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can update the document",
        )

    if request.title is not None:
        doc.title = request.title
    if request.visibility is not None:
        doc.visibility = request.visibility
    if request.categories is not None:
        doc.categories = request.categories
    if request.allowed_users is not None:
        doc.allowed_users = request.allowed_users
    if request.allowed_roles is not None:
        doc.allowed_roles = request.allowed_roles

    doc.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(doc)

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        visibility=doc.visibility,
        categories=doc.categories,
        source=doc.source,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    http_request: Request,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Delete a document."""
    result = await db.execute(select(Document).where(Document.id == str(doc_id)))
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if str(doc.owner_id) != current["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete the document",
        )

    await db.delete(doc)
    await db.commit()


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    http_request: Request,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(connection.get_docs_db),
):
    """Search documents using RAG."""
    rag_service = get_rag_service()

    results = await rag_service.search(
        db,
        query=request.query,
        user_id=current["user_id"],
        limit=request.limit,
        category=request.category,
    )

    return {
        "results": [
            {
                "chunk_id": str(r.chunk_id),
                "document_id": str(r.document_id),
                "text": r.text,
                "score": r.score,
                "modality": r.modality,
            }
            for r in results
        ]
    }


def _can_access_doc(doc: Document, user_id: str) -> bool:
    """Check if user can access document."""
    if doc.visibility == "public":
        return True
    if str(doc.owner_id) == user_id:
        return True
    return False
