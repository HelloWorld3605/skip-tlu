from __future__ import annotations

from pydantic import BaseModel, Field


class CoverSpecification(BaseModel):
    institution: str | None = None
    organization: str | None = None
    document_type: str | None = None
    title: str | None = None
    footer: str | None = None


class ContentSection(BaseModel):
    level: int
    title: str
    source: str | None = None
    children: list["ContentSection"] = Field(default_factory=list)


class ContentFigure(BaseModel):
    label: str
    caption: str
    source: str | None = None


class ContentTable(BaseModel):
    label: str
    caption: str
    rows: list[list[str]] = Field(default_factory=list)
    source: str | None = None


class ContentSpecification(BaseModel):
    title: str
    source_documents: list[str] = Field(default_factory=list)
    sections: list[ContentSection] = Field(default_factory=list)
    figures: list[ContentFigure] = Field(default_factory=list)
    tables: list[ContentTable] = Field(default_factory=list)
    cover: CoverSpecification | None = None
    include_toc: bool = False
    include_footnotes: bool = False
    include_landscape_section: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)
