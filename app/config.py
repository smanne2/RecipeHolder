"""
Configuration management for RecipeHolder application.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database configuration
    database_path: str = "/data/recipe_index.db"
    
    # Storage configuration
    recipes_path: str = "/data/recipes"
    max_recipe_size: int = 1_048_576  # 1MB max file size
    
    # Scraping configuration
    scrape_timeout: int = 30  # seconds
    user_agent: str = "RecipeHolder/1.0 (Recipe Management Application)"
    
    # Server configuration
    port: int = 8000
    log_level: str = "INFO"
    
    # Application metadata
    app_name: str = "RecipeHolder"
    app_version: str = "1.0.0"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        Path(self.recipes_path).mkdir(parents=True, exist_ok=True)
        
        # Ensure database directory exists
        db_dir = Path(self.database_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
