"""
File storage module for recipes.
Handles reading/writing recipes as markdown files with YAML frontmatter.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import frontmatter
from markdown import markdown
from app.config import settings
from app.utils import slugify, sanitize_filename

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class RecipeStorage:
    """
    Manages recipe storage as markdown files with YAML frontmatter.
    Each recipe stored as {slug}.md in the recipes directory.
    """
    
    def __init__(self, recipes_path: Optional[str] = None):
        """
        Initialize recipe storage.
        
        Args:
            recipes_path: Path to recipes directory (defaults to settings)
        """
        self.recipes_path = Path(recipes_path or settings.recipes_path)
        self.recipes_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Recipe storage initialized at: {self.recipes_path}")
    
    def save_recipe(self, recipe_data: Dict[str, Any]) -> str:
        """
        Save recipe to markdown file.
        
        Args:
            recipe_data: Dictionary containing recipe information
            
        Returns:
            Path to saved file
            
        Raises:
            StorageError: If save fails
        """
        try:
            slug = recipe_data.get('slug')
            if not slug:
                raise StorageError("Recipe data must contain 'slug' field")
            
            # Generate filename
            filename = f"{sanitize_filename(slug)}.md"
            filepath = self.recipes_path / filename
            
            # Check if file already exists
            if filepath.exists():
                logger.warning(f"Recipe file already exists: {filepath}")
            
            # Create markdown content
            markdown_content = self._create_markdown(recipe_data)
            
            # Write to file atomically (write to temp, then rename)
            temp_filepath = filepath.with_suffix('.tmp')
            try:
                temp_filepath.write_text(markdown_content, encoding='utf-8')
                temp_filepath.replace(filepath)
                logger.info(f"Recipe saved: {filepath}")
            finally:
                # Clean up temp file if it still exists
                if temp_filepath.exists():
                    temp_filepath.unlink()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save recipe: {str(e)}", exc_info=True)
            raise StorageError(f"Failed to save recipe: {str(e)}")
    
    def load_recipe(self, slug: str) -> Dict[str, Any]:
        """
        Load recipe from markdown file.
        
        Args:
            slug: Recipe slug (filename without .md extension)
            
        Returns:
            Dictionary containing recipe data
            
        Raises:
            StorageError: If load fails or file not found
        """
        try:
            filename = f"{sanitize_filename(slug)}.md"
            filepath = self.recipes_path / filename
            
            if not filepath.exists():
                raise StorageError(f"Recipe not found: {slug}")
            
            # Check file size
            file_size = filepath.stat().st_size
            if file_size > settings.max_recipe_size:
                raise StorageError(
                    f"Recipe file too large: {file_size} bytes "
                    f"(max: {settings.max_recipe_size})"
                )
            
            # Load and parse markdown with frontmatter
            post = frontmatter.load(filepath)
            
            # Extract metadata and content
            recipe_data = {
                'slug': slug,
                'filepath': str(filepath),
                **post.metadata,
                'content': post.content,
            }
            
            logger.debug(f"Recipe loaded: {slug}")
            return recipe_data
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Failed to load recipe '{slug}': {str(e)}", exc_info=True)
            raise StorageError(f"Failed to load recipe: {str(e)}")
    
    def delete_recipe(self, slug: str) -> bool:
        """
        Delete recipe file.
        
        Args:
            slug: Recipe slug
            
        Returns:
            True if deleted successfully
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            filename = f"{sanitize_filename(slug)}.md"
            filepath = self.recipes_path / filename
            
            if not filepath.exists():
                logger.warning(f"Recipe file not found for deletion: {slug}")
                return False
            
            filepath.unlink()
            logger.info(f"Recipe deleted: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete recipe '{slug}': {str(e)}", exc_info=True)
            raise StorageError(f"Failed to delete recipe: {str(e)}")
    
    def recipe_exists(self, slug: str) -> bool:
        """
        Check if recipe file exists.
        
        Args:
            slug: Recipe slug
            
        Returns:
            True if recipe exists
        """
        filename = f"{sanitize_filename(slug)}.md"
        filepath = self.recipes_path / filename
        return filepath.exists()
    
    def list_recipes(self) -> List[str]:
        """
        List all recipe slugs in storage.
        
        Returns:
            List of recipe slugs
        """
        try:
            recipe_files = sorted(self.recipes_path.glob('*.md'))
            slugs = [f.stem for f in recipe_files]
            logger.debug(f"Found {len(slugs)} recipes in storage")
            return slugs
        except Exception as e:
            logger.error(f"Failed to list recipes: {str(e)}", exc_info=True)
            return []
    
    def get_recipe_filepath(self, slug: str) -> Path:
        """
        Get full filepath for a recipe slug.
        
        Args:
            slug: Recipe slug
            
        Returns:
            Path object for recipe file
        """
        filename = f"{sanitize_filename(slug)}.md"
        return self.recipes_path / filename
    
    def _create_markdown(self, recipe_data: Dict[str, Any]) -> str:
        """
        Create markdown content with YAML frontmatter.
        
        Args:
            recipe_data: Recipe data dictionary
            
        Returns:
            Formatted markdown string
        """
        # Extract frontmatter fields
        metadata = {
            'title': recipe_data.get('title', 'Untitled Recipe'),
            'source_url': recipe_data.get('source_url', ''),
            'created_at': recipe_data.get('scraped_at') or datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
        }
        
        # Add optional metadata
        if recipe_data.get('prep_time'):
            metadata['prep_time'] = recipe_data['prep_time']
        if recipe_data.get('cook_time'):
            metadata['cook_time'] = recipe_data['cook_time']
        if recipe_data.get('total_time'):
            metadata['total_time'] = recipe_data['total_time']
        if recipe_data.get('servings'):
            metadata['servings'] = recipe_data['servings']
        if recipe_data.get('tags'):
            metadata['tags'] = recipe_data['tags']
        if recipe_data.get('author'):
            metadata['author'] = recipe_data['author']
        
        # Create content sections
        content_parts = []
        
        # Title
        title = recipe_data.get('title', 'Untitled Recipe')
        content_parts.append(f"# {title}\n")
        
        # Description
        description = recipe_data.get('description', '').strip()
        if description:
            content_parts.append(f"{description}\n")
        
        # Ingredients section
        ingredients = recipe_data.get('ingredients', [])
        if ingredients:
            content_parts.append("## Ingredients\n")
            for ingredient in ingredients:
                content_parts.append(f"- {ingredient}")
            content_parts.append("")  # Blank line
        
        # Instructions section
        instructions = recipe_data.get('instructions', '').strip()
        if instructions:
            content_parts.append("## Instructions\n")
            # Check if instructions are already numbered/formatted
            if '\n' in instructions:
                # Multi-line instructions
                lines = instructions.split('\n')
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line:
                        # Add number if not already present
                        if not line[0].isdigit():
                            content_parts.append(f"{i}. {line}")
                        else:
                            content_parts.append(line)
            else:
                # Single line instruction
                content_parts.append(f"1. {instructions}")
            content_parts.append("")  # Blank line
        
        # Notes section (if any additional info)
        notes = recipe_data.get('notes', '').strip()
        if notes:
            content_parts.append("## Notes\n")
            content_parts.append(notes)
        
        # Create frontmatter post
        content = "\n".join(content_parts)
        post = frontmatter.Post(content, **metadata)
        
        # Convert to string
        return frontmatter.dumps(post)
    
    def render_recipe_html(self, slug: str) -> str:
        """
        Load recipe and render markdown content to HTML.
        
        Args:
            slug: Recipe slug
            
        Returns:
            HTML string of recipe content
            
        Raises:
            StorageError: If recipe not found or render fails
        """
        try:
            recipe_data = self.load_recipe(slug)
            content = recipe_data.get('content', '')
            
            # Convert markdown to HTML
            html = markdown(
                content,
                extensions=['extra', 'nl2br', 'sane_lists']
            )
            
            return html
            
        except Exception as e:
            logger.error(f"Failed to render recipe '{slug}': {str(e)}", exc_info=True)
            raise StorageError(f"Failed to render recipe: {str(e)}")
