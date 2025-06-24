from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class DocumentType(str, Enum):
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    PDF = "pdf"

class ImageStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Image(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page_number: int
    file_path: str
    base64_image: Optional[str] = None
    original_text: Optional[str] = None
    llm_description: Optional[str] = None
    ocr_description: Optional[str] = None
    status: ImageStatus = ImageStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Text(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    page_number: int
    status: ImageStatus = ImageStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    document_type: DocumentType
    file_path: str
    total_pages: int
    images: List[Image] = []
    processed_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "processing"  # processing, completed, error

class ProcessingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    status: str = "pending"  # pending, processing, completed, error
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 

