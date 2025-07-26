"""Tortoise ORM model for Book."""

from tortoise.models import Model
from tortoise import fields
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.database.models.author_model import AuthorModel


class BookModel(Model):
    """Tortoise ORM model for Book entity."""
    
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=200, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Many-to-many relationship with authors
    authors: fields.ManyToManyRelation["AuthorModel"] = fields.ManyToManyField(
        "models.AuthorModel",
        related_name="books",
        through="author_book"
    )
    
    class Meta:
        table = "books"
        ordering = ["title"]
    
    def __str__(self) -> str:
        return f"Book(id={self.id}, title={self.title})"

