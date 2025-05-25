from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class SpacingOption(str, Enum):
    DEFAULT = "default"
    COMPACT = "compact"
    SPACIOUS = "spacious"


class PDFGenerationRequest(BaseModel):
    markup: str
    font_family: Optional[str] = "Inter"
    size_level: int = Field(3, ge=1, le=5)
    spacing: SpacingOption = SpacingOption.DEFAULT
    auto_width_tables: bool = True
    filename: Optional[str] = None

    @validator("markup")
    def markup_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Markup cannot be empty")
        return v

    @validator("font_family")
    def font_family_available(cls, v):
        """Ensure the requested font is available."""
        if v:
            from app.services.font_service import font_service
            if v not in font_service.get_available_fonts():
                raise ValueError("Unsupported font family")
        return v

