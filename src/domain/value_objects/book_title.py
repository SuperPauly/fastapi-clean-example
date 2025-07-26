"""Book title value object."""

from pydantic import BaseModel, Field, field_validator


class BookTitle(BaseModel):
    """Value object representing a book's title."""
    
    value: str = Field(..., description="The book's title")
    
    model_config = {
        "frozen": True,  # Immutable value object
        "str_strip_whitespace": True,  # Automatically strip whitespace
    }
    
    @field_validator('value')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate book title."""
        if not v:
            raise ValueError("Book title cannot be empty")
        
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Book title cannot be only whitespace")
        
        if len(v) > 200:
            raise ValueError("Book title cannot exceed 200 characters")
        
        return v
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
