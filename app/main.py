"""
Main FastAPI application for RecipeHolder.
Provides web interface and REST API for recipe management.
"""
import logging
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from app.config import settings
from app.database import init_db, get_db
from app.models import Recipe
from app.scraper import RecipeScraper, RecipeScraperError, UnsupportedWebsiteError
from app.storage import RecipeStorage, StorageError
from app.search import RecipeSearchService, SearchError
from app.utils import format_time

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RecipeHolder application...")
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Initialize database
    init_db()
    
    # Rebuild index on startup
    try:
        logger.info("Rebuilding recipe index...")
        search_service = RecipeSearchService()
        stats = search_service.rebuild_index()
        logger.info(f"Index rebuilt: {stats['total_files']} files, "
                   f"{stats['indexed']} indexed, {stats['updated']} updated")
    except Exception as e:
        logger.error(f"Failed to rebuild index: {e}")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RecipeHolder application...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Add custom template filters
templates.env.filters['format_time'] = format_time

# Initialize services
scraper = RecipeScraper()
storage = RecipeStorage()
search_service = RecipeSearchService(storage)


# ============================================================================
# Pydantic Models for API
# ============================================================================

class AddRecipeRequest(BaseModel):
    """Request model for adding recipe."""
    url: HttpUrl


class RecipeResponse(BaseModel):
    """Response model for recipe."""
    id: int
    title: str
    slug: str
    source_url: str
    description: Optional[str]
    servings: Optional[str]
    prep_time: Optional[int]
    cook_time: Optional[int]
    total_time: Optional[int]
    tags: List[str]
    created_at: str
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Response model for search results."""
    recipes: List[RecipeResponse]
    total: int
    query: Optional[str]
    tags: Optional[List[str]]


class ApiResponse(BaseModel):
    """Generic API response."""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


# ============================================================================
# Web Routes (HTML)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Home page with recipe list."""
    try:
        if q or tag:
            # Search with query or tag
            tags = [tag] if tag else None
            recipes = search_service.search_recipes(query=q, tags=tags, limit=100, db=db)
        else:
            # Get all recipes
            recipes = search_service.get_all_recipes(limit=100, db=db)
        
        # Get all tags for filter
        all_tags = search_service.get_all_tags(db=db)
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "recipes": recipes,
                "query": q,
                "selected_tag": tag,
                "tags": all_tags,
                "recipe_count": len(recipes),
            }
        )
    except Exception as e:
        logger.error(f"Error loading home page: {e}", exc_info=True)
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@app.get("/recipe/{slug}", response_class=HTMLResponse)
async def view_recipe(
    request: Request,
    slug: str,
    db: Session = Depends(get_db)
):
    """View individual recipe."""
    try:
        # Get recipe from index
        recipe = search_service.get_recipe_by_slug(slug, db=db)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Load full recipe content
        recipe_data = storage.load_recipe(slug)
        
        # Render markdown to HTML
        content_html = storage.render_recipe_html(slug)
        
        return templates.TemplateResponse(
            "recipe.html",
            {
                "request": request,
                "recipe": recipe,
                "recipe_data": recipe_data,
                "content_html": content_html,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing recipe '{slug}': {e}", exc_info=True)
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@app.get("/add", response_class=HTMLResponse)
async def add_recipe_form(request: Request):
    """Show add recipe form."""
    return templates.TemplateResponse(
        "add_recipe.html",
        {"request": request}
    )


@app.post("/add", response_class=HTMLResponse)
async def add_recipe(
    request: Request,
    url: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add recipe from URL."""
    try:
        # Check if recipe already exists
        existing = search_service.get_recipe_by_url(url, db=db)
        if existing:
            return templates.TemplateResponse(
                "add_recipe.html",
                {
                    "request": request,
                    "error": f"Recipe already exists: {existing.title}",
                    "existing_slug": existing.slug,
                },
                status_code=400
            )
        
        # Scrape recipe
        logger.info(f"Scraping recipe from: {url}")
        recipe_data = scraper.scrape_recipe(url)
        
        # Save to storage
        filepath = storage.save_recipe(recipe_data)
        logger.info(f"Recipe saved: {filepath}")
        
        # Add to index
        recipe = search_service.add_recipe_to_index(recipe_data, db=db)
        logger.info(f"Recipe indexed: {recipe.slug}")
        
        # Redirect to recipe page
        return RedirectResponse(
            url=f"/recipe/{recipe.slug}",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except UnsupportedWebsiteError as e:
        logger.warning(f"Unsupported website: {e}")
        return templates.TemplateResponse(
            "add_recipe.html",
            {
                "request": request,
                "error": f"Website not supported: {str(e)}",
                "url": url,
            },
            status_code=400
        )
    except RecipeScraperError as e:
        logger.error(f"Scraping failed: {e}")
        return templates.TemplateResponse(
            "add_recipe.html",
            {
                "request": request,
                "error": f"Failed to scrape recipe: {str(e)}",
                "url": url,
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error adding recipe: {e}", exc_info=True)
        return templates.TemplateResponse(
            "add_recipe.html",
            {
                "request": request,
                "error": f"An error occurred: {str(e)}",
                "url": url,
            },
            status_code=500
        )


@app.get("/search", response_class=HTMLResponse)
async def search_recipes(
    request: Request,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search recipes page."""
    return await index(request, q=q, db=db)


# ============================================================================
# API Routes (JSON)
# ============================================================================

@app.get("/api/recipes", response_model=SearchResponse)
async def api_list_recipes(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List recipes via API."""
    try:
        tags = [tag] if tag else None
        recipes = search_service.search_recipes(
            query=q,
            tags=tags,
            limit=limit,
            offset=offset,
            db=db
        )
        
        return SearchResponse(
            recipes=[RecipeResponse.model_validate(r) for r in recipes],
            total=len(recipes),
            query=q,
            tags=tags
        )
    except Exception as e:
        logger.error(f"API list recipes failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recipe/{slug}", response_model=RecipeResponse)
async def api_get_recipe(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get recipe by slug via API."""
    try:
        recipe = search_service.get_recipe_by_slug(slug, db=db)
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return RecipeResponse.model_validate(recipe)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get recipe failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recipe", response_model=ApiResponse)
async def api_add_recipe(
    request: AddRecipeRequest,
    db: Session = Depends(get_db)
):
    """Add recipe from URL via API."""
    try:
        url = str(request.url)
        
        # Check if exists
        existing = search_service.get_recipe_by_url(url, db=db)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Recipe already exists: {existing.slug}"
            )
        
        # Scrape and save
        recipe_data = scraper.scrape_recipe(url)
        storage.save_recipe(recipe_data)
        recipe = search_service.add_recipe_to_index(recipe_data, db=db)
        
        return ApiResponse(
            success=True,
            message="Recipe added successfully",
            data={
                "slug": recipe.slug,
                "title": recipe.title,
            }
        )
    except HTTPException:
        raise
    except RecipeScraperError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"API add recipe failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rebuild-index", response_model=ApiResponse)
async def api_rebuild_index(db: Session = Depends(get_db)):
    """Rebuild recipe index via API."""
    try:
        stats = search_service.rebuild_index(db=db)
        return ApiResponse(
            success=True,
            message="Index rebuilt successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"API rebuild index failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tags")
async def api_list_tags(db: Session = Depends(get_db)):
    """List all tags via API."""
    try:
        tags = search_service.get_all_tags(db=db)
        return {
            "tags": [{"name": tag.name, "recipe_count": len(tag.recipes)} for tag in tags]
        }
    except Exception as e:
        logger.error(f"API list tags failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    try:
        # Check database
        recipe_count = search_service.get_recipe_count()
        
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "recipe_count": recipe_count,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Not found"}
        )
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": "Page not found"},
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Handle 500 errors."""
    logger.error(f"Server error: {exc}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": "Internal server error"},
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False
    )
