from pathlib import Path
from pydantic import BaseModel, Field


class DocumentParagraph(BaseModel):
    text: str
    style: str | None = None
    level: int | None = None
    page: int | None = None


class DocumentTable(BaseModel):
    rows: list[list[str]] = Field(default_factory=list)
    caption: str | None = None


class DocumentSection(BaseModel):
    orientation: str = "portrait"
    page_width_twips: int | None = None
    page_height_twips: int | None = None
    margins_twips: dict[str, int] = Field(default_factory=dict)


class DocumentRequirementHints(BaseModel):
    headings: list[str] = Field(default_factory=list)
    captions: list[str] = Field(default_factory=list)
    has_toc: bool = False
    has_footnotes: bool = False
    has_landscape_section: bool = False


class DocumentImage(BaseModel):
    name: str
    path: Path | None = None
    width: int | None = None
    height: int | None = None


class ParsedDocument(BaseModel):
    path: Path
    file_type: str
    paragraphs: list[DocumentParagraph] = Field(default_factory=list)
    tables: list[DocumentTable] = Field(default_factory=list)
    images: list[DocumentImage] = Field(default_factory=list)
    sections: list[DocumentSection] = Field(default_factory=list)
    hints: DocumentRequirementHints = Field(default_factory=DocumentRequirementHints)
    metadata: dict[str, object] = Field(default_factory=dict)
