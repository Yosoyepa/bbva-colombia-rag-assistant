from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Document:
    """Raw scraped page before any processing."""
    source_url: str
    raw_html: str
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    id: UUID = field(default_factory=uuid4)


@dataclass
class Chunk:
    """Cleaned text fragment ready for embedding and retrieval."""
    content: str
    source_url: str
    embedding: list[float] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)


@dataclass
class ChatSession:
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatSessionSummary:
    id: UUID
    created_at: datetime
    updated_at: datetime | None
    message_count: int
    title: str


@dataclass
class ChatMessage:
    session_id: UUID
    role: str          # "user" | "assistant" | "system"
    content: str
    sources: list[str] = field(default_factory=list)  # URLs citadas (respuestas) → CU-04
    created_at: datetime = field(default_factory=datetime.utcnow)
    id: UUID = field(default_factory=uuid4)
