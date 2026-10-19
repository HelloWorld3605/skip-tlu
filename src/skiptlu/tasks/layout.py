from __future__ import annotations

from pydantic import BaseModel, Field


class PageLayout(BaseModel):
    top_cm: float = 2.0
    bottom_cm: float = 2.0
    left_cm: float = 3.0
    right_cm: float = 1.5
    header_cm: float = 1.0
    footer_cm: float = 1.0
    orientation: str = "portrait"


class TextStyleSpec(BaseModel):
    font_family: str = "Times New Roman"
    font_size_pt: float = 13
    bold: bool = False
    italic: bool = False
    line_spacing: float = 1.3
    space_before_pt: float = 6
    space_after_pt: float = 6


class LayoutSpecification(BaseModel):
    page: PageLayout = Field(default_factory=PageLayout)
    heading_styles: dict[int, TextStyleSpec] = Field(default_factory=dict)
    body_style: TextStyleSpec = Field(default_factory=TextStyleSpec)
    caption_style: TextStyleSpec = Field(
        default_factory=lambda: TextStyleSpec(italic=True)
    )
    multilevel_numbering: bool = True
    include_page_numbers: bool = True
    include_toc: bool = False
    include_illustration_lists: bool = False
    landscape_before_level: int | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


def default_word_layout(*, include_toc: bool = False, include_landscape: bool = False) -> LayoutSpecification:
    return LayoutSpecification(
        heading_styles={
            1: TextStyleSpec(bold=True),
            2: TextStyleSpec(bold=True),
            3: TextStyleSpec(bold=True, italic=True),
        },
        include_toc=include_toc,
        include_illustration_lists=True,
        landscape_before_level=2 if include_landscape else None,
    )
