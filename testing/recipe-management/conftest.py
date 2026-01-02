"""
Test configuration and fixtures for RecipeHolder tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.config import Settings


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings with temporary paths."""
    return Settings(
        database_path=str(temp_dir / "test_recipe_index.db"),
        recipes_path=str(temp_dir / "recipes"),
        max_recipe_size=1_048_576,
        scrape_timeout=10,
        log_level="DEBUG"
    )


@pytest.fixture
def test_db(test_settings):
    """Create test database."""
    engine = create_engine(f"sqlite:///{test_settings.database_path}")
    Base.metadata.create_all(bind=engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for testing."""
    return {
        'title': 'Test Chicken Curry',
        'slug': 'test-chicken-curry',
        'source_url': 'https://example.com/chicken-curry',
        'description': 'A delicious test recipe',
        'ingredients': [
            '2 lbs chicken',
            '1 onion, chopped',
            '2 cloves garlic',
            '1 tbsp curry powder'
        ],
        'instructions': 'Cook the chicken with spices.',
        'prep_time': 15,
        'cook_time': 30,
        'total_time': 45,
        'servings': '4 servings',
        'tags': ['chicken', 'curry', 'indian'],
        'author': 'Test Chef',
        'scraped_at': '2026-01-02T10:00:00Z'
    }
