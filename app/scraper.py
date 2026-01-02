"""
Recipe scraper module using recipe-scrapers library.
Extracts recipe data from various websites and formats for storage.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests
from recipe_scrapers import scrape_html, WebsiteNotImplementedError
from app.config import settings
from app.utils import slugify, validate_url, extract_domain

logger = logging.getLogger(__name__)


class RecipeScraperError(Exception):
    """Base exception for recipe scraping errors."""
    pass


class UnsupportedWebsiteError(RecipeScraperError):
    """Raised when website is not supported by recipe-scrapers."""
    pass


class ScrapingFailedError(RecipeScraperError):
    """Raised when scraping fails for any reason."""
    pass


class RecipeScraper:
    """
    Recipe scraper using recipe-scrapers library.
    Extracts recipe data from URLs and formats for storage.
    """
    
    def __init__(self):
        self.timeout = settings.scrape_timeout
        self.user_agent = settings.user_agent
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_recipe(self, url: str) -> Dict[str, Any]:
        """
        Scrape recipe from URL.
        
        Args:
            url: Recipe URL to scrape
            
        Returns:
            Dictionary containing recipe data
            
        Raises:
            RecipeScraperError: If scraping fails
        """
        logger.info(f"Scraping recipe from: {url}")
        
        # Validate URL
        if not validate_url(url):
            raise ScrapingFailedError(f"Invalid URL: {url}")
        
        try:
            # Fetch HTML content
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            html_content = response.text
            
            logger.debug(f"Successfully fetched HTML from {url}")
            
        except requests.exceptions.Timeout:
            raise ScrapingFailedError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise ScrapingFailedError(f"Failed to fetch URL: {str(e)}")
        
        try:
            # Parse recipe using recipe-scrapers
            scraper = scrape_html(html_content, org_url=url)
            
            # Extract recipe data
            recipe_data = self._extract_recipe_data(scraper, url)
            
            logger.info(f"Successfully scraped recipe: {recipe_data['title']}")
            return recipe_data
            
        except WebsiteNotImplementedError:
            # Try wild mode for unsupported sites
            logger.warning(f"Website not directly supported, trying wild mode: {url}")
            try:
                scraper = scrape_html(html_content, org_url=url, wild_mode=True)
                recipe_data = self._extract_recipe_data(scraper, url)
                logger.info(f"Successfully scraped recipe in wild mode: {recipe_data['title']}")
                return recipe_data
            except Exception as e:
                raise UnsupportedWebsiteError(
                    f"Website not supported by recipe-scrapers: {extract_domain(url)}"
                )
        except Exception as e:
            logger.error(f"Failed to parse recipe from {url}: {str(e)}", exc_info=True)
            raise ScrapingFailedError(f"Failed to parse recipe: {str(e)}")
    
    def _extract_recipe_data(self, scraper, url: str) -> Dict[str, Any]:
        """
        Extract recipe data from scraper object.
        
        Args:
            scraper: Recipe scraper object
            url: Original URL
            
        Returns:
            Dictionary with extracted recipe data
        """
        # Extract title (required)
        title = self._safe_extract(scraper.title)
        if not title:
            raise ScrapingFailedError("Could not extract recipe title")
        
        # Extract ingredients (required)
        ingredients = self._safe_extract(scraper.ingredients, default=[])
        if not ingredients:
            logger.warning(f"No ingredients found for recipe: {title}")
        
        # Extract instructions (required)
        instructions = self._safe_extract(scraper.instructions)
        if not instructions:
            logger.warning(f"No instructions found for recipe: {title}")
            instructions = ""
        
        # Extract optional fields
        recipe_data = {
            'title': title,
            'slug': slugify(title),
            'source_url': url,
            'description': self._safe_extract(scraper.description) or "",
            'ingredients': ingredients,
            'instructions': instructions,
            'prep_time': self._extract_time(scraper, 'prep_time'),
            'cook_time': self._extract_time(scraper, 'cook_time'),
            'total_time': self._extract_time(scraper, 'total_time'),
            'servings': self._safe_extract(scraper.yields) or "",
            'author': self._safe_extract(scraper.author) or "",
            'tags': self._extract_tags(scraper),
            'scraped_at': datetime.utcnow().isoformat(),
        }
        
        return recipe_data
    
    def _safe_extract(self, func, default=None):
        """
        Safely extract data from scraper method.
        
        Args:
            func: Scraper method to call
            default: Default value if extraction fails
            
        Returns:
            Extracted value or default
        """
        try:
            if callable(func):
                result = func()
            else:
                result = func
            return result if result else default
        except Exception as e:
            logger.debug(f"Failed to extract data: {str(e)}")
            return default
    
    def _extract_time(self, scraper, time_type: str) -> Optional[int]:
        """
        Extract time in minutes.
        
        Args:
            scraper: Recipe scraper object
            time_type: Type of time ('prep_time', 'cook_time', 'total_time')
            
        Returns:
            Time in minutes or None
        """
        try:
            if time_type == 'prep_time':
                minutes = scraper.prep_time()
            elif time_type == 'cook_time':
                minutes = scraper.cook_time()
            elif time_type == 'total_time':
                minutes = scraper.total_time()
            else:
                return None
            
            return int(minutes) if minutes and minutes > 0 else None
        except Exception as e:
            logger.debug(f"Failed to extract {time_type}: {str(e)}")
            return None
    
    def _extract_tags(self, scraper) -> List[str]:
        """
        Extract and normalize tags from recipe.
        
        Args:
            scraper: Recipe scraper object
            
        Returns:
            List of normalized tags
        """
        tags = []
        
        # Try to get keywords
        keywords = self._safe_extract(scraper.keywords, default=[])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',')]
        
        # Try to get category
        category = self._safe_extract(scraper.category)
        if category:
            if isinstance(category, str):
                tags.append(category.lower())
            elif isinstance(category, list):
                tags.extend([c.lower() for c in category])
        
        # Add keywords as tags
        if keywords:
            tags.extend([k.lower() for k in keywords if k])
        
        # Normalize and deduplicate tags
        normalized_tags = []
        for tag in tags:
            # Clean tag
            tag = tag.strip().lower()
            # Remove special characters
            tag = ''.join(c for c in tag if c.isalnum() or c in ('-', '_', ' '))
            # Replace spaces with hyphens
            tag = tag.replace(' ', '-')
            # Skip empty or very long tags
            if tag and len(tag) <= 50 and tag not in normalized_tags:
                normalized_tags.append(tag)
        
        return normalized_tags[:20]  # Limit to 20 tags
