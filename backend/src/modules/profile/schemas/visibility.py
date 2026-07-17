from pydantic import field_validator

from src.modules.profile.utils.enums import FieldsVisibility
from src.utils.schemas.base_schema import BaseSchema


class ProfileVisibilityUpdateSchema(BaseSchema):
    visible_fields: dict[str, bool]

    @field_validator("visible_fields")
    @classmethod
    def validate_known_fields(cls, value: dict[str, bool]) -> dict[str, bool]:
        unknown = set(value.keys()) - FieldsVisibility.VISIBILITY_TOGGLEABLE_FIELDS.value
        if unknown:
            raise ValueError(
                f"Unknown or non-toggleable field(s): {', '.join(sorted(unknown))}. "
                f"Allowed: {', '.join(sorted(FieldsVisibility.VISIBILITY_TOGGLEABLE_FIELDS.value))}"
            )
        return value
