"""Author name value object."""

from pydantic import BaseModel, Field, field_validator


class AuthorName(BaseModel):
    """Value object representing an author's name."""
    
    value: str = Field(..., description="The author's name")
    
    model_config = {
        "frozen": True,  # Immutable value object
        "str_strip_whitespace": True,  # Automatically strip whitespace
    }
    
    @field_validator('value')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate author name."""
        if not v:
            raise ValueError("Author name cannot be empty")
        
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Author name cannot be only whitespace")
        
        if len(v) > 100:
            raise ValueError("Author name cannot exceed 100 characters")
        
        return v
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
