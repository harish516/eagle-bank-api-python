"""Address-related schema models."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class AddressBase(BaseModel):
    """Base address model."""
    line1: str = Field(..., min_length=1, max_length=100)
    line2: Optional[str] = Field(None, max_length=100)
    line3: Optional[str] = Field(None, max_length=100)
    town: str = Field(..., min_length=1, max_length=50)
    county: str = Field(..., min_length=1, max_length=50)
    postcode: str = Field(..., min_length=1, max_length=10)
    
    @field_validator('postcode', mode='before')
    @classmethod
    def validate_postcode(cls, v):
        """Validate UK postcode format."""
        if not v:
            raise ValueError('Postcode is required')
        
        # Simple UK postcode validation
        pattern = r'^[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}$'
        v_upper = str(v).upper().strip()
        
        if not re.match(pattern, v_upper):
            raise ValueError('Invalid UK postcode format. Example: SW1A 1AA')
        
        return v_upper

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "line1": "123 Main Street",
            "line2": "Apt 4B",
            "town": "London",
            "county": "Greater London",
            "postcode": "SW1A 1AA"
        }
    })
