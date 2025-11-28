from pydantic import BaseModel, Field, field_validator
from typing import Optional


class RagParameters(BaseModel):
    similarity_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score to include documents (0.0-1.0)"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of top-matching documents to retrieve (1-50)"
    )
    chunk_size: int = Field(
        default=512,
        ge=100,
        le=2000,
        description="Size of text chunks to retrieve in tokens (100-2000)"
    )
    overlap: int = Field(
        default=15,
        ge=0,
        le=50,
        description="Percentage of chunk overlap for context continuity (0-50)"
    )

    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v):
        allowed_values = [256, 512, 1024]
        if v not in allowed_values:
            closest = min(allowed_values, key=lambda x: abs(x - v))
            return closest
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "similarity_threshold": 0.6,
                "top_k": 5,
                "chunk_size": 512,
                "overlap": 15
            }
        }


class RagPreset:
    DEFAULT = RagParameters(
        similarity_threshold=0.6,
        top_k=5,
        chunk_size=512,
        overlap=15
    )

    HIGH_PRECISION = RagParameters(
        similarity_threshold=0.8,
        top_k=3,
        chunk_size=256,
        overlap=10
    )

    COMPREHENSIVE = RagParameters(
        similarity_threshold=0.5,
        top_k=10,
        chunk_size=1024,
        overlap=20
    )

    FAST = RagParameters(
        similarity_threshold=0.7,
        top_k=3,
        chunk_size=256,
        overlap=10
    )

    @classmethod
    def get_preset(cls, name: str) -> RagParameters:
        presets = {
            "default": cls.DEFAULT,
            "high_precision": cls.HIGH_PRECISION,
            "comprehensive": cls.COMPREHENSIVE,
            "fast": cls.FAST
        }
        return presets.get(name.lower(), cls.DEFAULT)
