"""Tortoise ORM model for Author."""

from tortoise.models import Model
from tortoise import fields
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.database.models.book_model import BookModel


class AuthorModel(Model):
    """Tortoise ORM model for Author entity."""
    
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Many-to-many relationship with books
    books: fields.ManyToManyRelation["BookModel"] = fields.ManyToManyField(
        "models.BookModel",
        related_name="authors",
        through="author_book"
    )
    
    class Meta:
        table = "authors"
        ordering = ["name"]
    
    def __str__(self) -> str:
        return f"Author(id={self.id}, name={self.name})"

