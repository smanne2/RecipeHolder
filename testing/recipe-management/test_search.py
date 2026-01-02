"""
Tests for search and indexing service.
"""
import pytest
from app.search import RecipeSearchService, SearchError
from app.storage import RecipeStorage
from app.models import Recipe, Tag


class TestRecipeSearchService:
    """Tests for RecipeSearchService class."""
    
    def test_service_initialization(self, test_settings):
        """Test service initializes correctly."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        assert service.storage is not None
    
    def test_add_recipe_to_index(self, test_db, test_settings, sample_recipe_data):
        """Test adding recipe to search index."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        recipe = service.add_recipe_to_index(sample_recipe_data, test_db)
        
        assert recipe.id is not None
        assert recipe.title == sample_recipe_data['title']
        assert recipe.slug == sample_recipe_data['slug']
        assert recipe.source_url == sample_recipe_data['source_url']
        assert len(recipe.tags) > 0
    
    def test_add_duplicate_url(self, test_db, test_settings, sample_recipe_data):
        """Test adding recipe with duplicate URL raises error."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add first time
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Try to add again
        with pytest.raises(SearchError, match="already exists"):
            service.add_recipe_to_index(sample_recipe_data, test_db)
    
    def test_remove_recipe_from_index(self, test_db, test_settings, sample_recipe_data):
        """Test removing recipe from index."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add recipe
        recipe = service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Remove it
        result = service.remove_recipe_from_index(recipe.slug, test_db)
        assert result is True
        
        # Verify it's gone
        found = service.get_recipe_by_slug(recipe.slug, test_db)
        assert found is None
    
    def test_search_recipes_by_title(self, test_db, test_settings, sample_recipe_data):
        """Test searching recipes by title."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add recipe
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Search by title
        results = service.search_recipes(query="Chicken", db=test_db)
        assert len(results) == 1
        assert results[0].title == sample_recipe_data['title']
        
        # Search with no match
        results = service.search_recipes(query="Pizza", db=test_db)
        assert len(results) == 0
    
    def test_search_recipes_by_tag(self, test_db, test_settings, sample_recipe_data):
        """Test searching recipes by tag."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add recipe
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Search by tag
        results = service.search_recipes(tags=["chicken"], db=test_db)
        assert len(results) == 1
        
        # Search by non-existent tag
        results = service.search_recipes(tags=["pizza"], db=test_db)
        assert len(results) == 0
    
    def test_get_recipe_by_slug(self, test_db, test_settings, sample_recipe_data):
        """Test getting recipe by slug."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add recipe
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Get by slug
        recipe = service.get_recipe_by_slug(sample_recipe_data['slug'], test_db)
        assert recipe is not None
        assert recipe.title == sample_recipe_data['title']
    
    def test_get_recipe_by_url(self, test_db, test_settings, sample_recipe_data):
        """Test getting recipe by source URL."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add recipe
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Get by URL
        recipe = service.get_recipe_by_url(sample_recipe_data['source_url'], test_db)
        assert recipe is not None
        assert recipe.source_url == sample_recipe_data['source_url']
    
    def test_get_all_recipes(self, test_db, test_settings, sample_recipe_data):
        """Test getting all recipes."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add multiple recipes
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        another_recipe = sample_recipe_data.copy()
        another_recipe['title'] = 'Another Recipe'
        another_recipe['slug'] = 'another-recipe'
        another_recipe['source_url'] = 'https://example.com/another'
        service.add_recipe_to_index(another_recipe, test_db)
        
        # Get all
        recipes = service.get_all_recipes(db=test_db)
        assert len(recipes) == 2
    
    def test_get_all_tags(self, test_db, test_settings, sample_recipe_data):
        """Test getting all tags."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Add recipe with tags
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Get all tags
        tags = service.get_all_tags(test_db)
        assert len(tags) > 0
        tag_names = [t.name for t in tags]
        assert "chicken" in tag_names
        assert "curry" in tag_names
    
    def test_rebuild_index(self, test_db, test_settings, sample_recipe_data):
        """Test rebuilding index from files."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Save recipe to file
        storage.save_recipe(sample_recipe_data)
        
        # Rebuild index
        stats = service.rebuild_index(test_db)
        
        assert stats['total_files'] == 1
        assert stats['indexed'] == 1
        assert stats['errors'] == 0
        
        # Verify recipe in index
        recipe = service.get_recipe_by_slug(sample_recipe_data['slug'], test_db)
        assert recipe is not None
    
    def test_get_recipe_count(self, test_db, test_settings, sample_recipe_data):
        """Test getting recipe count."""
        storage = RecipeStorage(test_settings.recipes_path)
        service = RecipeSearchService(storage)
        
        # Initially zero
        count = service.get_recipe_count(test_db)
        assert count == 0
        
        # Add recipe
        service.add_recipe_to_index(sample_recipe_data, test_db)
        
        # Count should be 1
        count = service.get_recipe_count(test_db)
        assert count == 1
