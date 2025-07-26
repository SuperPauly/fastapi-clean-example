"""Book title value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BookTitle:
    """Value object representing a book's title."""
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate book title."""
        if not self.value:
            raise ValueError("Book title cannot be empty")
        
        if len(self.value.strip()) == 0:
            raise ValueError("Book title cannot be only whitespace")
        
        if len(self.value) > 200:
            raise ValueError("Book title cannot exceed 200 characters")
        
        # Store normalized value
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        """String representation."""
        return self.value

