"""
Tests for recipe storage module.
"""
import pytest
from pathlib import Path
from app.storage import RecipeStorage, StorageError


class TestRecipeStorage:
    """Tests for RecipeStorage class."""
    
    def test_storage_initialization(self, test_settings):
        """Test storage initializes correctly."""
        storage = RecipeStorage(test_settings.recipes_path)
        assert storage.recipes_path.exists()
        assert storage.recipes_path.is_dir()
    
    def test_save_recipe(self, test_settings, sample_recipe_data):
        """Test saving recipe to file."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        filepath = storage.save_recipe(sample_recipe_data)
        
        assert Path(filepath).exists()
        assert Path(filepath).name == "test-chicken-curry.md"
        
        # Check file content
        content = Path(filepath).read_text()
        assert "Test Chicken Curry" in content
        assert "## Ingredients" in content
        assert "## Instructions" in content
        assert "2 lbs chicken" in content
    
    def test_save_recipe_without_slug(self, test_settings):
        """Test saving recipe without slug raises error."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        with pytest.raises(StorageError, match="slug"):
            storage.save_recipe({})
    
    def test_load_recipe(self, test_settings, sample_recipe_data):
        """Test loading recipe from file."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        # Save recipe first
        storage.save_recipe(sample_recipe_data)
        
        # Load it back
        loaded = storage.load_recipe(sample_recipe_data['slug'])
        
        assert loaded['title'] == sample_recipe_data['title']
        assert loaded['slug'] == sample_recipe_data['slug']
        assert loaded['source_url'] == sample_recipe_data['source_url']
        assert 'content' in loaded
        assert '## Ingredients' in loaded['content']
    
    def test_load_nonexistent_recipe(self, test_settings):
        """Test loading non-existent recipe raises error."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        with pytest.raises(StorageError, match="not found"):
            storage.load_recipe("nonexistent-recipe")
    
    def test_delete_recipe(self, test_settings, sample_recipe_data):
        """Test deleting recipe."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        # Save recipe first
        filepath = storage.save_recipe(sample_recipe_data)
        assert Path(filepath).exists()
        
        # Delete it
        result = storage.delete_recipe(sample_recipe_data['slug'])
        assert result is True
        assert not Path(filepath).exists()
    
    def test_delete_nonexistent_recipe(self, test_settings):
        """Test deleting non-existent recipe."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        result = storage.delete_recipe("nonexistent-recipe")
        assert result is False
    
    def test_recipe_exists(self, test_settings, sample_recipe_data):
        """Test checking if recipe exists."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        # Should not exist initially
        assert storage.recipe_exists(sample_recipe_data['slug']) is False
        
        # Save recipe
        storage.save_recipe(sample_recipe_data)
        
        # Should exist now
        assert storage.recipe_exists(sample_recipe_data['slug']) is True
    
    def test_list_recipes(self, test_settings, sample_recipe_data):
        """Test listing all recipes."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        # Initially empty
        recipes = storage.list_recipes()
        assert len(recipes) == 0
        
        # Save recipe
        storage.save_recipe(sample_recipe_data)
        
        # Save another recipe
        another_recipe = sample_recipe_data.copy()
        another_recipe['title'] = 'Another Recipe'
        another_recipe['slug'] = 'another-recipe'
        storage.save_recipe(another_recipe)
        
        # List should contain both
        recipes = storage.list_recipes()
        assert len(recipes) == 2
        assert sample_recipe_data['slug'] in recipes
        assert another_recipe['slug'] in recipes
    
    def test_render_recipe_html(self, test_settings, sample_recipe_data):
        """Test rendering recipe markdown to HTML."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        # Save recipe
        storage.save_recipe(sample_recipe_data)
        
        # Render to HTML
        html = storage.render_recipe_html(sample_recipe_data['slug'])
        
        assert '<h2>Ingredients</h2>' in html or '<h2 id="ingredients">Ingredients</h2>' in html
        assert '<h2>Instructions</h2>' in html or '<h2 id="instructions">Instructions</h2>' in html
        assert '2 lbs chicken' in html
    
    def test_markdown_frontmatter_format(self, test_settings, sample_recipe_data):
        """Test that saved file has correct YAML frontmatter."""
        storage = RecipeStorage(test_settings.recipes_path)
        
        filepath = storage.save_recipe(sample_recipe_data)
        content = Path(filepath).read_text()
        
        # Check YAML frontmatter
        assert content.startswith('---')
        assert 'title: ' in content
        assert 'source_url: ' in content
        assert 'prep_time: 15' in content
        assert 'cook_time: 30' in content
        assert 'tags:' in content
        assert '- chicken' in content
