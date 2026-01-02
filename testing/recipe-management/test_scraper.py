"""
Tests for recipe scraper module.
"""
import pytest
from unittest.mock import Mock, patch
from app.scraper import RecipeScraper, RecipeScraperError, UnsupportedWebsiteError


class TestRecipeScraper:
    """Tests for RecipeScraper class."""
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly."""
        scraper = RecipeScraper()
        assert scraper.timeout > 0
        assert scraper.user_agent is not None
        assert 'User-Agent' in scraper.headers
    
    def test_invalid_url(self):
        """Test scraping with invalid URL."""
        scraper = RecipeScraper()
        
        with pytest.raises(RecipeScraperError):
            scraper.scrape_recipe("not-a-url")
        
        with pytest.raises(RecipeScraperError):
            scraper.scrape_recipe("ftp://invalid.com")
    
    @patch('app.scraper.requests.get')
    @patch('app.scraper.scrape_html')
    def test_successful_scrape(self, mock_scrape_html, mock_requests):
        """Test successful recipe scraping."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "<html>Recipe content</html>"
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response
        
        # Mock recipe scraper
        mock_scraper = Mock()
        mock_scraper.title.return_value = "Test Recipe"
        mock_scraper.ingredients.return_value = ["ingredient 1", "ingredient 2"]
        mock_scraper.instructions.return_value = "Step 1. Do this."
        mock_scraper.description.return_value = "A test recipe"
        mock_scraper.prep_time.return_value = 10
        mock_scraper.cook_time.return_value = 20
        mock_scraper.total_time.return_value = 30
        mock_scraper.yields.return_value = "4 servings"
        mock_scraper.author.return_value = "Test Chef"
        mock_scraper.keywords.return_value = ["test", "recipe"]
        mock_scraper.category.return_value = "main-dish"
        
        mock_scrape_html.return_value = mock_scraper
        
        # Test scraping
        scraper = RecipeScraper()
        result = scraper.scrape_recipe("https://example.com/recipe")
        
        assert result['title'] == "Test Recipe"
        assert len(result['ingredients']) == 2
        assert result['prep_time'] == 10
        assert result['slug'] == "test-recipe"
        assert 'scraped_at' in result
    
    @patch('app.scraper.requests.get')
    def test_timeout_handling(self, mock_requests):
        """Test timeout handling."""
        import requests
        mock_requests.side_effect = requests.exceptions.Timeout()
        
        scraper = RecipeScraper()
        with pytest.raises(RecipeScraperError, match="timed out"):
            scraper.scrape_recipe("https://example.com/recipe")
    
    @patch('app.scraper.requests.get')
    def test_network_error_handling(self, mock_requests):
        """Test network error handling."""
        import requests
        mock_requests.side_effect = requests.exceptions.ConnectionError()
        
        scraper = RecipeScraper()
        with pytest.raises(RecipeScraperError):
            scraper.scrape_recipe("https://example.com/recipe")
    
    def test_extract_tags(self):
        """Test tag extraction and normalization."""
        scraper = RecipeScraper()
        
        # Mock scraper object
        mock_scraper = Mock()
        mock_scraper.keywords.return_value = ["Chicken", "CURRY", "indian food"]
        mock_scraper.category.return_value = "Main Dish"
        
        tags = scraper._extract_tags(mock_scraper)
        
        assert "chicken" in tags
        assert "curry" in tags
        assert "indian-food" in tags
        assert "main-dish" in tags
        # Check deduplication
        assert len(tags) == len(set(tags))
        # Check length limit
        assert len(tags) <= 20
