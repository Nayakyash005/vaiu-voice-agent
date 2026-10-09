import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PhoneCreate(BaseModel):
    rawTranscript: str = Field(min_length=1)
    parsedNumber: str
    language: str = Field(min_length=1, max_length=32)

    @field_validator("parsedNumber")
    @classmethod
    def validate_indian_mobile_number(cls, value: str) -> str:
        if re.fullmatch(r"[6-9][0-9]{9}", value) is None:
            raise ValueError("parsedNumber must be a valid 10-digit Indian mobile number")
        return value


class PhoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rawTranscript: str
    parsedNumber: str
    language: str
    collectedAt: datetime
