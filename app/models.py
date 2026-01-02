"""
Database models for recipe indexing.
Stores metadata about recipes for fast searching and browsing.
Actual recipe content stored in markdown files.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Table, Column, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Association table for many-to-many relationship between recipes and tags
recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Recipe(Base):
    """Recipe metadata model for indexing and search."""
    
    __tablename__ = "recipes"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    filepath: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    source_url: Mapped[str] = mapped_column(String(2000), unique=True, nullable=False, index=True)
    
    # Optional metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    servings: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Time fields (stored in minutes)
    prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cook_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Relationships
    tags: Mapped[List["Tag"]] = relationship(
        secondary=recipe_tags,
        back_populates="recipes",
        cascade="all, delete"
    )
    
    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, title='{self.title}', slug='{self.slug}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "source_url": self.source_url,
            "description": self.description,
            "servings": self.servings,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "total_time": self.total_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": [tag.name for tag in self.tags],
        }


class Tag(Base):
    """Tag model for categorizing recipes."""
    
    __tablename__ = "tags"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Tag name
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    recipes: Mapped[List["Recipe"]] = relationship(
        secondary=recipe_tags,
        back_populates="tags"
    )
    
    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "recipe_count": len(self.recipes),
        }
