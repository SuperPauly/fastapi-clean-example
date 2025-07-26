"""Database connection management."""

from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from src.infrastructure.config.settings import database_config


TORTOISE_ORM = {
    "connections": {
        "default": database_config.url
    },
    "apps": {
        "models": {
            "models": [
                "src.infrastructure.database.models.author_model",
                "src.infrastructure.database.models.book_model",
                "aerich.models"
            ],
            "default_connection": "default",
        },
    },
}


async def init_db() -> None:
    """Initialize database connection."""
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db() -> None:
    """Close database connection."""
    await Tortoise.close_connections()


def register_db_with_app(app) -> None:
    """Register database with FastAPI app."""
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )

