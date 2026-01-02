"""
Tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestWebRoutes:
    """Tests for web routes (HTML)."""
    
    def test_home_page(self, client):
        """Test home page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert "RecipeHolder" in response.text
    
    def test_add_recipe_form(self, client):
        """Test add recipe form loads."""
        response = client.get("/add")
        assert response.status_code == 200
        assert "Add New Recipe" in response.text
        assert "Recipe URL" in response.text
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'app_name' in data


class TestAPIRoutes:
    """Tests for API routes (JSON)."""
    
    def test_api_list_recipes(self, client):
        """Test API recipe list endpoint."""
        response = client.get("/api/recipes")
        assert response.status_code == 200
        data = response.json()
        assert 'recipes' in data
        assert 'total' in data
        assert isinstance(data['recipes'], list)
    
    def test_api_list_recipes_with_search(self, client):
        """Test API recipe list with search query."""
        response = client.get("/api/recipes?q=chicken")
        assert response.status_code == 200
        data = response.json()
        assert data['query'] == 'chicken'
    
    def test_api_list_recipes_with_tag(self, client):
        """Test API recipe list with tag filter."""
        response = client.get("/api/recipes?tag=curry")
        assert response.status_code == 200
        data = response.json()
        assert data['tags'] == ['curry']
    
    def test_api_get_nonexistent_recipe(self, client):
        """Test getting non-existent recipe returns 404."""
        response = client.get("/api/recipe/nonexistent-recipe")
        assert response.status_code == 404
    
    def test_api_list_tags(self, client):
        """Test API tags list endpoint."""
        response = client.get("/api/tags")
        assert response.status_code == 200
        data = response.json()
        assert 'tags' in data
        assert isinstance(data['tags'], list)
    
    @patch('app.main.scraper.scrape_recipe')
    @patch('app.main.storage.save_recipe')
    @patch('app.main.search_service.get_recipe_by_url')
    @patch('app.main.search_service.add_recipe_to_index')
    def test_api_add_recipe(
        self,
        mock_add_to_index,
        mock_get_by_url,
        mock_save_recipe,
        mock_scrape_recipe,
        client
    ):
        """Test adding recipe via API."""
        # Mock responses
        mock_get_by_url.return_value = None  # Recipe doesn't exist
        mock_scrape_recipe.return_value = {
            'title': 'Test Recipe',
            'slug': 'test-recipe',
            'source_url': 'https://example.com/recipe',
            'ingredients': ['ingredient 1'],
            'instructions': 'Do this',
            'tags': ['test']
        }
        mock_save_recipe.return_value = '/path/to/recipe.md'
        
        mock_recipe = Mock()
        mock_recipe.slug = 'test-recipe'
        mock_recipe.title = 'Test Recipe'
        mock_add_to_index.return_value = mock_recipe
        
        # Test API call
        response = client.post(
            "/api/recipe",
            json={"url": "https://example.com/recipe"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'slug' in data['data']
        assert data['data']['slug'] == 'test-recipe'
    
    def test_api_add_recipe_invalid_url(self, client):
        """Test adding recipe with invalid URL."""
        response = client.post(
            "/api/recipe",
            json={"url": "not-a-url"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_api_rebuild_index(self, client):
        """Test rebuild index API endpoint."""
        response = client.post("/api/rebuild-index")
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_error_web(self, client):
        """Test 404 error on web route."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404
        assert "not found" in response.text.lower()
    
    def test_404_error_api(self, client):
        """Test 404 error on API route."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
