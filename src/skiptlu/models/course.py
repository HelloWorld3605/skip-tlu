from pydantic import BaseModel, Field
from .activity import Activity


class CourseSection(BaseModel):
    id: int | None = None
    name: str
    activities: list[Activity] = Field(default_factory=list)


class Course(BaseModel):
    id: int
    name: str
    sections: list[CourseSection] = Field(default_factory=list)

    @property
    def activities(self) -> list[Activity]:
        return [activity for section in self.sections for activity in section.activities]
