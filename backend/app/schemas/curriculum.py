"""Validation for the additive curriculum JSON contract, not a new persistence model."""

from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StringConstraints,
    model_validator,
)

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Difficulty = Literal["beginner", "intermediate", "advanced"]


class ContentModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Reference(ContentModel):
    title: Text
    url: Text

    @model_validator(mode="after")
    def valid_url(self):
        url = urlsplit(self.url)
        if url.scheme != "https" or not url.netloc or url.username or url.password:
            raise ValueError(
                "References require an absolute HTTPS URL without credentials"
            )
        return self


class Section(ContentModel):
    title: Text
    description: Text
    diagram: Text


class Question(ContentModel):
    question: Text
    options: list[Text] = Field(min_length=2)
    answerIndex: StrictInt = Field(ge=0)
    explanation: Text

    @model_validator(mode="after")
    def answer_integrity(self):
        if self.answerIndex >= len(self.options) or len(set(self.options)) != len(
            self.options
        ):
            raise ValueError(
                "Each question needs distinct options and one valid answer index"
            )
        return self


class Activity(ContentModel):
    id: Text
    moduleId: StrictInt
    title: Text
    type: Literal["circuit", "conceptual"]
    concept: Text
    description: Text
    objective: Text
    learnerAction: Text
    expectedResult: Text
    difficulty: Difficulty
    requiresBuilder: StrictBool
    status: Literal["planned"]
    assessmentQuestionIndices: list[StrictInt] = Field(min_length=1)


class Lesson(ContentModel):
    id: StrictInt = Field(ge=1)
    title: Text
    objectives: Text
    introduction: Text
    sections: list[Section] = Field(min_length=1)
    workedExample: Text
    keyTakeaways: Text
    questions: list[Question] = Field(min_length=1)
    tryInBuilder: StrictBool
    builderLink: Text | None = None
    curriculumVersion: StrictInt = Field(ge=1)
    difficulty: Difficulty
    estimatedMinutes: StrictInt = Field(gt=0)
    prerequisites: list[StrictInt]
    learningObjectives: list[Text] = Field(min_length=1)
    mathematicalLevel: Literal["none", "basic", "linear-algebra"]
    references: list[Reference] = Field(min_length=1)
    experiments: list[Activity] = Field(min_length=1)
    challenges: list[Activity] = Field(min_length=1)

    @model_validator(mode="after")
    def relationships(self):
        if self.objectives != " ".join(self.learningObjectives):
            raise ValueError("Legacy and structured objectives must agree")
        if self.tryInBuilder and not self.builderLink:
            raise ValueError("Builder-enabled lessons need a link")
        if len(set(self.prerequisites)) != len(self.prerequisites):
            raise ValueError("Duplicate prerequisites")
        for activity in self.experiments + self.challenges:
            if (
                activity.moduleId != self.id
                or activity.objective not in self.learningObjectives
            ):
                raise ValueError("Activity must reference its lesson and an objective")
            indices = activity.assessmentQuestionIndices
            if len(set(indices)) != len(indices) or any(
                i < 0 or i >= len(self.questions) for i in indices
            ):
                raise ValueError("Invalid activity assessment relationship")
        return self


def validate_curriculum(data):
    lessons = [Lesson.model_validate(item) for item in data]
    by_id = {lesson.id: lesson for lesson in lessons}
    if len(by_id) != len(lessons):
        raise ValueError("Duplicate module IDs")
    activity_ids = [a.id for m in lessons for a in m.experiments + m.challenges]
    if len(set(activity_ids)) != len(activity_ids):
        raise ValueError("Duplicate activity IDs")
    visited, active = set(), set()

    def visit(number):
        if number not in by_id:
            raise ValueError("Unknown prerequisite")
        if number in active:
            raise ValueError("Circular prerequisites")
        if number in visited:
            return
        active.add(number)
        for prerequisite in by_id[number].prerequisites:
            visit(prerequisite)
        active.remove(number)
        visited.add(number)

    for number in by_id:
        visit(number)
    # Preserve the source shape and unknown additive fields for existing consumers.
    return data
