"""
Search and indexing service for recipes.
Manages SQLite index and provides search functionality.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, joinedload
from app.models import Recipe, Tag
from app.storage import RecipeStorage, StorageError
from app.database import get_db_session

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Base exception for search errors."""
    pass


class RecipeSearchService:
    """
    Service for searching and indexing recipes.
    Manages SQLite index for fast searching.
    """
    
    def __init__(self, storage: Optional[RecipeStorage] = None):
        """
        Initialize search service.
        
        Args:
            storage: RecipeStorage instance (creates new if None)
        """
        self.storage = storage or RecipeStorage()
    
    def add_recipe_to_index(
        self, 
        recipe_data: Dict[str, Any], 
        db: Session
    ) -> Recipe:
        """
        Add recipe to search index.
        
        Args:
            recipe_data: Recipe data dictionary
            db: Database session
            
        Returns:
            Created Recipe model
            
        Raises:
            SearchError: If indexing fails
        """
        try:
            # Check if recipe already exists by URL
            existing = db.execute(
                select(Recipe).where(Recipe.source_url == recipe_data['source_url'])
            ).scalar_one_or_none()
            
            if existing:
                logger.warning(f"Recipe already indexed: {recipe_data['source_url']}")
                raise SearchError(f"Recipe already exists: {existing.slug}")
            
            # Check by slug
            existing_slug = db.execute(
                select(Recipe).where(Recipe.slug == recipe_data['slug'])
            ).scalar_one_or_none()
            
            if existing_slug:
                # Append timestamp to make slug unique
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                recipe_data['slug'] = f"{recipe_data['slug']}-{timestamp}"
                logger.info(f"Slug collision, using: {recipe_data['slug']}")
            
            # Get filepath
            filepath = str(self.storage.get_recipe_filepath(recipe_data['slug']))
            
            # Create recipe record
            recipe = Recipe(
                title=recipe_data['title'],
                slug=recipe_data['slug'],
                filepath=filepath,
                source_url=recipe_data['source_url'],
                description=recipe_data.get('description', ''),
                servings=recipe_data.get('servings', ''),
                prep_time=recipe_data.get('prep_time'),
                cook_time=recipe_data.get('cook_time'),
                total_time=recipe_data.get('total_time'),
            )
            
            # Add tags
            tags = recipe_data.get('tags', [])
            if tags:
                recipe.tags = self._get_or_create_tags(tags, db)
            
            db.add(recipe)
            db.commit()
            db.refresh(recipe)
            
            logger.info(f"Recipe added to index: {recipe.slug}")
            return recipe
            
        except SearchError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add recipe to index: {str(e)}", exc_info=True)
            raise SearchError(f"Failed to add recipe to index: {str(e)}")
    
    def remove_recipe_from_index(self, slug: str, db: Session) -> bool:
        """
        Remove recipe from search index.
        
        Args:
            slug: Recipe slug
            db: Database session
            
        Returns:
            True if removed successfully
        """
        try:
            recipe = db.execute(
                select(Recipe).where(Recipe.slug == slug)
            ).scalar_one_or_none()
            
            if not recipe:
                logger.warning(f"Recipe not found in index: {slug}")
                return False
            
            db.delete(recipe)
            db.commit()
            
            logger.info(f"Recipe removed from index: {slug}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to remove recipe from index: {str(e)}", exc_info=True)
            raise SearchError(f"Failed to remove recipe from index: {str(e)}")
    
    def search_recipes(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Recipe]:
        """
        Search recipes by query and/or tags.
        
        Args:
            query: Search query (searches title and description)
            tags: List of tag names to filter by
            limit: Maximum number of results
            offset: Number of results to skip
            db: Database session (creates new if None)
            
        Returns:
            List of Recipe models
        """
        close_session = False
        if db is None:
            db = get_db_session()
            close_session = True
        
        try:
            # Build base query
            stmt = select(Recipe).options(joinedload(Recipe.tags))
            
            # Add search conditions
            conditions = []
            
            if query:
                search_term = f"%{query}%"
                conditions.append(
                    or_(
                        Recipe.title.ilike(search_term),
                        Recipe.description.ilike(search_term)
                    )
                )
            
            if tags:
                # Filter by tags
                stmt = stmt.join(Recipe.tags).where(Tag.name.in_(tags))
            
            if conditions:
                stmt = stmt.where(*conditions)
            
            # Add ordering and pagination
            stmt = stmt.order_by(Recipe.created_at.desc())
            stmt = stmt.limit(limit).offset(offset)
            
            # Execute query
            recipes = db.execute(stmt).scalars().unique().all()
            
            logger.debug(f"Search returned {len(recipes)} recipes")
            return list(recipes)
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            raise SearchError(f"Search failed: {str(e)}")
        finally:
            if close_session:
                db.close()
    
    def get_recipe_by_slug(self, slug: str, db: Optional[Session] = None) -> Optional[Recipe]:
        """
        Get recipe by slug from index.
        
        Args:
            slug: Recipe slug
            db: Database session (creates new if None)
            
        Returns:
            Recipe model or None
        """
        close_session = False
        if db is None:
            db = get_db_session()
            close_session = True
        
        try:
            recipe = db.execute(
                select(Recipe)
                .options(joinedload(Recipe.tags))
                .where(Recipe.slug == slug)
            ).unique().scalar_one_or_none()
            
            return recipe
        finally:
            if close_session:
                db.close()
    
    def get_recipe_by_url(self, url: str, db: Optional[Session] = None) -> Optional[Recipe]:
        """
        Get recipe by source URL from index.
        
        Args:
            url: Source URL
            db: Database session (creates new if None)
            
        Returns:
            Recipe model or None
        """
        close_session = False
        if db is None:
            db = get_db_session()
            close_session = True
        
        try:
            recipe = db.execute(
                select(Recipe).where(Recipe.source_url == url)
            ).scalar_one_or_none()
            
            return recipe
        finally:
            if close_session:
                db.close()
    
    def get_all_recipes(
        self, 
        limit: int = 100, 
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Recipe]:
        """
        Get all recipes from index.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            db: Database session (creates new if None)
            
        Returns:
            List of Recipe models
        """
        close_session = False
        if db is None:
            db = get_db_session()
            close_session = True
        
        try:
            recipes = db.execute(
                select(Recipe)
                .options(joinedload(Recipe.tags))
                .order_by(Recipe.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).scalars().unique().all()
            
            return list(recipes)
        finally:
            if close_session:
                db.close()
    
    def get_all_tags(self, db: Optional[Session] = None) -> List[Tag]:
        """
        Get all tags from index.
        
        Args:
            db: Database session (creates new if None)
            
        Returns:
            List of Tag models
        """
        close_session = False
        if db is None:
            db = get_db_session()
            close_session = True
        
        try:
            tags = db.execute(
                select(Tag).order_by(Tag.name)
            ).scalars().all()
            
            return list(tags)
        finally:
            if close_session:
                db.close()
    
    def rebuild_index(self, db: Optional[Session] = None) -> Dict[str, int]:
        """
        Rebuild search index from markdown files.
        
        Args:
            db: Database session (creates new if None)
            
        Returns:
            Dictionary with rebuild statistics
        """
        close_session = False
        if db is None:
            db = get_db_session()
            close_session = True
        
        try:
            logger.info("Starting index rebuild...")
            
            # Get all recipe slugs from storage
            slugs = self.storage.list_recipes()
            
            # Track statistics
            stats = {
                'total_files': len(slugs),
                'indexed': 0,
                'updated': 0,
                'errors': 0,
                'orphaned': 0,
            }
            
            # Get existing recipes in index
            existing_recipes = {r.slug: r for r in self.get_all_recipes(limit=10000, db=db)}
            
            # Process each file
            for slug in slugs:
                try:
                    # Load recipe data from file
                    recipe_data = self.storage.load_recipe(slug)
                    
                    # Check if already in index
                    if slug in existing_recipes:
                        # Update existing record
                        recipe = existing_recipes[slug]
                        recipe.title = recipe_data.get('title', recipe.title)
                        recipe.description = recipe_data.get('description', '')
                        recipe.servings = recipe_data.get('servings', '')
                        recipe.prep_time = recipe_data.get('prep_time')
                        recipe.cook_time = recipe_data.get('cook_time')
                        recipe.total_time = recipe_data.get('total_time')
                        recipe.updated_at = datetime.utcnow()
                        
                        # Update tags
                        tags = recipe_data.get('tags', [])
                        if tags:
                            recipe.tags = self._get_or_create_tags(tags, db)
                        
                        stats['updated'] += 1
                        del existing_recipes[slug]  # Remove from orphaned check
                    else:
                        # Create new record
                        recipe = Recipe(
                            title=recipe_data.get('title', 'Untitled'),
                            slug=slug,
                            filepath=recipe_data['filepath'],
                            source_url=recipe_data.get('source_url', ''),
                            description=recipe_data.get('description', ''),
                            servings=recipe_data.get('servings', ''),
                            prep_time=recipe_data.get('prep_time'),
                            cook_time=recipe_data.get('cook_time'),
                            total_time=recipe_data.get('total_time'),
                        )
                        
                        # Add tags
                        tags = recipe_data.get('tags', [])
                        if tags:
                            recipe.tags = self._get_or_create_tags(tags, db)
                        
                        db.add(recipe)
                        stats['indexed'] += 1
                    
                except StorageError as e:
                    logger.error(f"Failed to load recipe '{slug}': {e}")
                    stats['errors'] += 1
                except Exception as e:
                    logger.error(f"Error processing recipe '{slug}': {e}", exc_info=True)
                    stats['errors'] += 1
            
            # Remove orphaned records (in database but no file)
            for slug, recipe in existing_recipes.items():
                logger.warning(f"Removing orphaned recipe from index: {slug}")
                db.delete(recipe)
                stats['orphaned'] += 1
            
            # Commit all changes
            db.commit()
            
            logger.info(f"Index rebuild complete: {stats}")
            return stats
            
        except Exception as e:
            db.rollback()
            logger.error(f"Index rebuild failed: {str(e)}", exc_info=True)
            raise SearchError(f"Index rebuild failed: {str(e)}")
        finally:
            if close_session:
                db.close()
    
    def get_recipe_count(self, db: Optional[Session] = None) -> int:
        """
        Get total number of recipes in index.
        
        Args:
            db: Database session (creates new if None)
            
        Returns:
            Recipe count
        """
        close_session = False
        if db is None:
            db = get_db_session()
            close_session = True
        
        try:
            count = db.execute(select(func.count(Recipe.id))).scalar()
            return count or 0
        finally:
            if close_session:
                db.close()
    
    def _get_or_create_tags(self, tag_names: List[str], db: Session) -> List[Tag]:
        """
        Get or create tags by name.
        
        Args:
            tag_names: List of tag names
            db: Database session
            
        Returns:
            List of Tag models
        """
        tags = []
        for name in tag_names:
            name = name.lower().strip()
            if not name:
                continue
            
            # Try to get existing tag
            tag = db.execute(
                select(Tag).where(Tag.name == name)
            ).scalar_one_or_none()
            
            if not tag:
                # Create new tag
                tag = Tag(name=name)
                db.add(tag)
            
            tags.append(tag)
        
        return tags
