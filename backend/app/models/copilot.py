# app/models/copilot.py
"""
Database models for BIZIO AI Copilot.
Includes documents, embeddings, conversations, and data fix suggestions.
"""
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Date, ForeignKey, Boolean, Enum, JSON, Index, LargeBinary
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.db import Base


class DocumentType(str, PyEnum):
    """Types of documents that can be uploaded to the AI Copilot."""
    receipt = "receipt"
    invoice = "invoice"
    contract = "contract"
    sop = "sop"
    policy = "policy"
    catalog = "catalog"
    other = "other"


class Document(Base):
    """
    Uploaded documents (receipts, invoices, contracts, SOPs, policies).
    These are indexed by the RAG system for semantic search.
    """
    __tablename__ = "copilot_documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Document metadata
    title = Column(String, nullable=False)
    doc_type = Column(Enum(DocumentType), nullable=False, default=DocumentType.other)
    file_path = Column(String, nullable=True)  # Path to stored file
    file_name = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    
    # Extracted content
    raw_text = Column(Text, nullable=True)  # Full extracted text
    
    # Document-level metadata (extracted or provided)
    doc_date = Column(Date, nullable=True)  # Date mentioned in document
    vendor = Column(String, nullable=True)
    amount = Column(Numeric(precision=18, scale=2), nullable=True)
    currency = Column(String, default="KZT")
    category = Column(String, nullable=True)
    
    # Related entities
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    product_ids = Column(JSON, nullable=True)  # List of related product IDs
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(String, nullable=True)
    ocr_confidence = Column(Numeric(precision=5, scale=2), nullable=True)  # 0-100
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="copilot_documents")
    user = relationship("User", back_populates="copilot_documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_copilot_documents_tenant_type', 'tenant_id', 'doc_type'),
        Index('ix_copilot_documents_tenant_date', 'tenant_id', 'doc_date'),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, type={self.doc_type})>"


class DocumentChunk(Base):
    """
    Vector embeddings for RAG semantic search.
    Each document is split into chunks with embeddings.
    """
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("copilot_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    
    # Embedding - stored as JSON array for SQLite compatibility
    # For PostgreSQL with pgvector, this would be Vector(768)
    embedding = Column(JSON, nullable=True)
    
    # Metadata for filtering during retrieval
    doc_type = Column(String, nullable=True)
    doc_date = Column(Date, nullable=True)
    supplier_id = Column(Integer, nullable=True)
    product_skus = Column(JSON, nullable=True)  # List of SKUs mentioned
    category = Column(String, nullable=True)
    
    # Token counts
    token_count = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('ix_document_chunks_tenant', 'tenant_id'),
        Index('ix_document_chunks_doc_type', 'doc_type'),
    )

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"


class CopilotConversation(Base):
    """
    Chat sessions with the AI Copilot.
    Each conversation has a history of messages.
    """
    __tablename__ = "copilot_conversations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Conversation metadata
    title = Column(String, nullable=True)  # Auto-generated from first message
    
    # Context - what page/entity was the user looking at when starting?
    context_type = Column(String, nullable=True)  # "dashboard", "product", "expense", etc.
    context_id = Column(Integer, nullable=True)  # ID of the entity if applicable
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="copilot_conversations")
    user = relationship("User", back_populates="copilot_conversations")
    messages = relationship("CopilotMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="CopilotMessage.created_at")
    
    __table_args__ = (
        Index('ix_copilot_conversations_user', 'user_id'),
    )

    def __repr__(self):
        return f"<CopilotConversation(id={self.id}, title={self.title})>"


class MessageRole(str, PyEnum):
    """Role of a message in the conversation."""
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class CopilotMessage(Base):
    """
    Individual messages in a Copilot conversation.
    Includes both user queries and AI responses.
    """
    __tablename__ = "copilot_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("copilot_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # For assistant messages - structured response data
    response_data = Column(JSON, nullable=True)  # {key_numbers, sources, actions, confidence}
    
    # For tool calls
    tool_calls = Column(JSON, nullable=True)  # List of tool calls made
    tool_results = Column(JSON, nullable=True)  # Results from tool calls
    
    # Token usage
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    
    # Processing time
    processing_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("CopilotConversation", back_populates="messages")
    
    __table_args__ = (
        Index('ix_copilot_messages_conversation', 'conversation_id'),
    )

    def __repr__(self):
        return f"<CopilotMessage(id={self.id}, role={self.role}, conv_id={self.conversation_id})>"


class DataFixStatus(str, PyEnum):
    """Status of a data fix suggestion."""
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"
    failed = "failed"


class DataFixSuggestion(Base):
    """
    Proposed data quality fixes (merge duplicates, fill missing, etc.).
    User must approve before changes are applied.
    """
    __tablename__ = "data_fix_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Who requested
    conversation_id = Column(Integer, ForeignKey("copilot_conversations.id", ondelete="SET NULL"), nullable=True)
    
    # Fix details
    fix_type = Column(String, nullable=False)  # merge_duplicates, fill_missing, correct_category
    entity_type = Column(String, nullable=False)  # products, suppliers, clients
    
    # The actual changes proposed
    changes = Column(JSON, nullable=False)
    # Example: [{"action": "merge", "source_ids": [1, 2], "target_id": 1, "field_values": {...}}]
    
    # Status
    status = Column(Enum(DataFixStatus), default=DataFixStatus.pending)
    
    # Impact assessment
    affected_records = Column(Integer, nullable=True)
    estimated_impact = Column(String, nullable=True)
    
    # Approval/rejection
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    
    # Application result
    applied_at = Column(DateTime, nullable=True)
    apply_error = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-expire old suggestions

    # Relationships
    tenant = relationship("Tenant", back_populates="data_fix_suggestions")
    
    __table_args__ = (
        Index('ix_data_fix_suggestions_tenant_status', 'tenant_id', 'status'),
    )

    def __repr__(self):
        return f"<DataFixSuggestion(id={self.id}, type={self.fix_type}, status={self.status})>"
