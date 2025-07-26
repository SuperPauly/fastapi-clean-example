"""Author name value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorName:
    """Value object representing an author's name."""
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate author name."""
        if not self.value:
            raise ValueError("Author name cannot be empty")
        
        if len(self.value.strip()) == 0:
            raise ValueError("Author name cannot be only whitespace")
        
        if len(self.value) > 100:
            raise ValueError("Author name cannot exceed 100 characters")
        
        # Store normalized value
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        """String representation."""
        return self.value

