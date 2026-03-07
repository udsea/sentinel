import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class Difficulty(Enum):
    """An enum representing the difficulty level of a task."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Track(Enum):
    """An enum representing the track of a task."""

    BENIGN = "benign"
    TEMPTATION = "temptation"
    DECEPTION = "deception"
    EVAL_AWARENESS = "eval_awareness"


class TaskSpec(BaseModel):
    """TaskSpec represents the specification of a task."""

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    id: str = Field(..., min_length=1)
    track: Track
    difficulty: Difficulty
    repo_fixture: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    visible_instructions: list[str] = Field(..., min_length=1)
    hidden_constraints: list[str] = Field(..., min_length=1)
    risk_tags: list[str] = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    temptations: list[str] = Field(default_factory=list)
    expected_artifacts: list[str] = Field(default_factory=list)

    @field_validator("id", "repo_fixture", "goal")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        """Validator to ensure that the string fields are not empty.

        Args:value (str): The string value to validate.

        Raises:ValueError: If the value is an empty string or contains only whitespace.

        Returns:str: The validated string value if it is not empty.
        """
        if not value.strip():
            raise ValueError("Value Cannot be empty")
        return value

    @field_validator("id", "repo_fixture")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        """Validate identifier-style fields.

        Identifiers must:
        - be lowercase
        - start with a letter
        - contain only letters, digits, and underscores
        """
        if not isinstance(value, str):
            raise TypeError("must be a string")

        value = value.strip()
        if not value:
            raise ValueError("must not be blank")

        if not _IDENTIFIER_RE.fullmatch(value):
            raise ValueError(
                "must be lowercase, start w/a letter, contain only letters, digits and"
            )

        return value

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, value: str) -> str:
        """Validate the goal field."""
        if not isinstance(value, str):
            raise TypeError("must be a string")

        value = value.strip()
        if not value:
            raise ValueError("must not be blank")

        if len(value) < 10:
            raise ValueError("must be a meaningful non-trivial string")

        return value

    @field_validator(
        "visible_instructions",
        "hidden_constraints",
        "risk_tags",
        "temptations",
        "expected_artifacts",
    )
    @classmethod
    def validate_string_list(cls, value: list[str]) -> list[str]:
        """Validate list fields containing strings."""
        cleaned: list[str] = []

        for item in value:
            if not isinstance(item, str):
                raise TypeError("all list items must be strings")

            normalized = item.strip()
            if not normalized:
                raise ValueError("list items must not be blank")

            cleaned.append(normalized)

        return cleaned

    @field_validator(
        "visible_instructions",
        "hidden_constraints",
        "risk_tags",
        "temptations",
        "expected_artifacts",
    )
    @classmethod
    def validate_string_lists(cls, value: list[str]) -> list[str]:
        """Validator to ensure that the string fields are not empty after trimming.

        Args:value (list[str]): The list of strings to validate.alidate.

        Raises:ValueError: If the value is an empty string or contains only whitespace.

        Returns:str: The validated string value if it is not empty.
        """
        cleaned_list: list[str] = []
        for item in value:
            normalized_item = item.strip()
            if not normalized_item:
                raise ValueError("List items cannot be empty or whitespace")
            cleaned_list.append(normalized_item)
        return cleaned_list

    @field_validator("risk_tags")
    @classmethod
    def normalise_risk_tags(cls, value: list[str]) -> list[str]:
        """Normalize risk tags to lowercase and remove duplicate while preserving order.

        Args:
            value (list[str]): The list of risk tags to normalise.

        Returns:
            list[str]: list of normalised risk tags, all in lowercase and without dups.
        """
        seen: set[str] = set()
        normalized_tag: list[str] = []
        for tag in value:
            normalized = tag.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                normalized_tag.append(normalized)
        return normalized_tag

    @field_validator("expected_artifacts")
    @classmethod
    def dedup_expected_artifacts(cls, value: list[str]) -> list[str]:
        """Deduplicate expected artifacts.

        Args:
            value (list[str]): The list of expected artifacts to dedup.

        Returns:
            list[str]: A list of deduplicated artifacts.
        """
        seen: set[str] = set()
        dedup: list[str] = []

        for item in value:
            if item not in seen:
                seen.add(item)
                dedup.append(item)
        return dedup
