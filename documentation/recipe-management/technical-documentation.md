# Recipe Management Application - Technical Documentation

**Version**: 1.0.0  
**Last Updated**: January 2, 2026  
**Author**: RecipeHolder Team

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Data Model](#data-model)
4. [API Endpoints](#api-endpoints)
5. [File Storage Format](#file-storage-format)
6. [Scraping Engine](#scraping-engine)
7. [Search & Indexing](#search--indexing)
8. [Docker Deployment](#docker-deployment)
9. [Configuration](#configuration)
10. [Security Considerations](#security-considerations)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         FastAPI Web Application                │    │
│  │  ┌──────────────┐  ┌──────────────┐           │    │
│  │  │  Jinja2      │  │  REST API    │           │    │
│  │  │  Templates   │  │  Endpoints   │           │    │
│  │  └──────────────┘  └──────────────┘           │    │
│  └────────────────────────────────────────────────┘    │
│                       │                                 │
│  ┌────────────────────┼────────────────────────────┐   │
│  │     Business Logic Layer                        │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────┐ │   │
│  │  │  Scraper    │ │   Storage    │ │  Search  │ │   │
│  │  │  Service    │ │   Service    │ │  Engine  │ │   │
│  │  └─────────────┘ └──────────────┘ └──────────┘ │   │
│  └────────────────────────────────────────────────┘   │
│                       │                                 │
│  ┌────────────────────┼────────────────────────────┐   │
│  │         Data Layer                              │   │
│  │  ┌─────────────────┐  ┌────────────────────┐   │   │
│  │  │  SQLite Index   │  │  Markdown Files    │   │   │
│  │  │  (Metadata)     │  │  (Recipe Storage)  │   │   │
│  │  └─────────────────┘  └────────────────────┘   │   │
│  └────────────────────────────────────────────────┘   │
│                       │                                 │
│  ┌────────────────────┼────────────────────────────┐   │
│  │          Volume Mount: /data                    │   │
│  │  - /data/recipes/         (markdown files)      │   │
│  │  - /data/recipe_index.db  (SQLite database)     │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   NAS Storage │
                 └───────────────┘
```

### Component Responsibilities

#### **Web Layer (FastAPI)**
- HTTP request handling
- Template rendering (Jinja2)
- Form validation
- Session management
- Static file serving

#### **Scraper Service**
- URL validation
- Recipe extraction using recipe-scrapers
- Data normalization
- Error handling for unsupported sites
- Duplicate detection (URL-based)

#### **Storage Service**
- Markdown file creation/reading
- YAML frontmatter parsing
- File naming (slugification)
- Directory management
- Atomic file operations

#### **Search Engine**
- SQLite index management
- Full-text search
- Tag-based filtering
- Index rebuilding
- Query optimization

---

## Technology Stack

### Backend Framework
- **FastAPI 0.109+**: Modern async web framework
  - Automatic OpenAPI documentation
  - Type hints with Pydantic validation
  - High performance (Starlette + Uvicorn)

### Core Libraries
- **recipe-scrapers 14.51+**: Recipe extraction from 600+ websites
- **SQLAlchemy 2.0+**: ORM for SQLite index
- **python-frontmatter 1.1+**: YAML frontmatter parsing
- **Jinja2 3.1+**: Template engine
- **python-slugify 8.0+**: URL-safe filename generation
- **Uvicorn 0.27+**: ASGI server

### Additional Dependencies
- **requests 2.31+**: HTTP client for scraping
- **beautifulsoup4 4.12+**: HTML parsing (via recipe-scrapers)
- **markdown 3.5+**: Markdown to HTML conversion
- **pydantic 2.5+**: Data validation

### Development Tools
- **pytest 7.4+**: Testing framework
- **pytest-asyncio**: Async test support
- **black**: Code formatting
- **ruff**: Linting

---

## Data Model

### SQLite Index Schema

The SQLite database stores **metadata only** for fast searching. Actual recipe content lives in markdown files.

```sql
-- recipes table: index of all recipe files
CREATE TABLE recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    filepath TEXT UNIQUE NOT NULL,
    source_url TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prep_time INTEGER,        -- minutes
    cook_time INTEGER,        -- minutes
    total_time INTEGER,       -- minutes
    servings TEXT,
    description TEXT
);

-- tags table: recipe categorization
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- recipe_tags table: many-to-many relationship
CREATE TABLE recipe_tags (
    recipe_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (recipe_id, tag_id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- indexes for performance
CREATE INDEX idx_recipes_title ON recipes(title);
CREATE INDEX idx_recipes_source_url ON recipes(source_url);
CREATE INDEX idx_recipes_slug ON recipes(slug);
CREATE INDEX idx_tags_name ON tags(name);
```

### SQLAlchemy Models

```python
# Simplified model structure
class Recipe(Base):
    __tablename__ = "recipes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    filepath: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    source_url: Mapped[str] = mapped_column(String(2000), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    # ... additional fields
    
    tags: Mapped[List["Tag"]] = relationship(secondary="recipe_tags", back_populates="recipes")
```

---

## File Storage Format

### Markdown File Structure

Each recipe is stored as a `.md` file with YAML frontmatter:

```markdown
---
title: "Chicken Curry (Pressure Cooker)"
source_url: "https://pipingpotcurry.com/chicken-curry-pressure-cooker/"
created_at: "2026-01-02T10:30:00Z"
updated_at: "2026-01-02T10:30:00Z"
prep_time: 15
cook_time: 20
total_time: 35
servings: "4-6 servings"
tags:
  - chicken
  - curry
  - pressure-cooker
  - indian
---

# Chicken Curry (Pressure Cooker)

A quick and flavorful chicken curry made in a pressure cooker.

## Ingredients

- 2 lbs chicken, cut into pieces
- 2 large onions, chopped
- 3 tomatoes, pureed
- 1 tbsp ginger-garlic paste
- 2 tsp curry powder
- 1 tsp turmeric
- 1 cup water
- Salt to taste
- Fresh cilantro for garnish

## Instructions

1. Turn on pressure cooker to sauté mode. Add oil and onions, cook until golden.
2. Add ginger-garlic paste, cook for 1 minute until fragrant.
3. Add tomato puree, curry powder, turmeric, and salt. Cook for 3-4 minutes.
4. Add chicken pieces and mix well to coat with masala.
5. Add water, close lid and set to high pressure for 10 minutes.
6. Natural release for 5 minutes, then quick release.
7. Garnish with fresh cilantro and serve with rice or naan.

## Notes

- Can substitute chicken thighs for more tender meat
- Adjust spice level by adding chili powder
- Freezes well for up to 3 months
```

### File Naming Convention

Files are named using slugified titles:
- **Original**: "Chicken Curry (Pressure Cooker)"
- **Slug**: `chicken-curry-pressure-cooker`
- **Filename**: `chicken-curry-pressure-cooker.md`
- **Full Path**: `/data/recipes/chicken-curry-pressure-cooker.md`

### Directory Structure

```
/data/
├── recipes/
│   ├── chicken-curry-pressure-cooker.md
│   ├── chocolate-chip-cookies.md
│   ├── sourdough-bread.md
│   └── ...
└── recipe_index.db
```

---

## API Endpoints

### Web Interface (HTML)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/` | Home page with recipe list | HTML |
| GET | `/recipe/{slug}` | Individual recipe view | HTML |
| GET | `/add` | Add recipe form | HTML |
| POST | `/add` | Submit new recipe URL | Redirect |
| GET | `/search?q={query}` | Search results | HTML |

### REST API (JSON)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/api/recipes` | List all recipes (paginated) | JSON |
| GET | `/api/recipe/{slug}` | Get recipe details | JSON |
| POST | `/api/recipe` | Add recipe from URL | JSON |
| GET | `/api/search?q={query}` | Search recipes | JSON |
| POST | `/api/rebuild-index` | Rebuild recipe index | JSON |
| GET | `/api/tags` | List all tags | JSON |

### Request/Response Examples

#### POST /api/recipe - Add Recipe
```json
// Request
{
  "url": "https://pipingpotcurry.com/chicken-curry-pressure-cooker/"
}

// Response (201 Created)
{
  "success": true,
  "slug": "chicken-curry-pressure-cooker",
  "title": "Chicken Curry (Pressure Cooker)",
  "message": "Recipe added successfully"
}

// Error Response (400 Bad Request)
{
  "success": false,
  "error": "Recipe already exists",
  "slug": "chicken-curry-pressure-cooker"
}
```

#### GET /api/recipes - List Recipes
```json
// Response
{
  "recipes": [
    {
      "slug": "chicken-curry-pressure-cooker",
      "title": "Chicken Curry (Pressure Cooker)",
      "description": "A quick and flavorful chicken curry...",
      "total_time": 35,
      "tags": ["chicken", "curry", "pressure-cooker"]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## Scraping Engine

### Recipe-Scrapers Integration

The application uses the `recipe-scrapers` library which supports 600+ websites.

#### Scraping Flow

```python
# High-level flow
1. User submits URL
2. Validate URL format
3. Check if URL already exists in index (duplicate detection)
4. Fetch HTML content
5. Parse with recipe-scrapers
6. Extract: title, ingredients, instructions, times, servings
7. Generate slug from title
8. Create markdown file with YAML frontmatter
9. Save to /data/recipes/{slug}.md
10. Add entry to SQLite index
11. Return success response
```

#### Supported Data Fields

Extracted from websites when available:
- Title
- Ingredients (list)
- Instructions (text or list)
- Prep time, cook time, total time
- Servings/yields
- Description
- Author
- Recipe category
- Keywords/tags

#### Error Handling

- **Unsupported Website**: Graceful failure with error message
- **Invalid URL**: Validation error before scraping
- **Network Error**: Retry with exponential backoff
- **Parse Error**: Log and return user-friendly message
- **Duplicate URL**: Check before scraping, return existing recipe

---

## Search & Indexing

### Index Management

#### Building Index
- Index built on application startup
- Scans `/data/recipes/` directory
- Parses YAML frontmatter from each `.md` file
- Populates SQLite database

#### Rebuilding Index
- Manual trigger via `/api/rebuild-index`
- Automatic on startup
- Orphaned database entries cleaned
- New files added to index

### Search Functionality

#### Search Strategy
1. **Primary**: Query SQLite index (title, description, tags)
2. **Fallback**: Full-text search in markdown files
3. **Ranking**: Sort by relevance (title matches > description > content)

#### Search Query Types
- **Simple**: "chicken curry" - searches in title and description
- **Tag-based**: "tag:indian" - filters by specific tag
- **Time-based**: Sort by creation date, total time
- **Combined**: Multiple filters applied together

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

# Create data directory
RUN mkdir -p /data/recipes

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  recipe-holder:
    build: .
    container_name: recipe-holder
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    environment:
      - DATABASE_PATH=/data/recipe_index.db
      - RECIPES_PATH=/data/recipes
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Volume Mounts
- **./data:/data**: Persistent storage for recipes and index
  - Recipes accessible at host: `./data/recipes/`
  - Direct filesystem access for reading recipes

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `/data/recipe_index.db` | SQLite database location |
| `RECIPES_PATH` | `/data/recipes` | Recipe markdown files directory |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MAX_RECIPE_SIZE` | `1048576` | Max recipe file size (1MB) |
| `SCRAPE_TIMEOUT` | `30` | Scraping timeout in seconds |
| `PORT` | `8000` | Application port |

### Configuration File (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_path: str = "/data/recipe_index.db"
    recipes_path: str = "/data/recipes"
    log_level: str = "INFO"
    max_recipe_size: int = 1_048_576  # 1MB
    scrape_timeout: int = 30
    port: int = 8000
    
    class Config:
        env_file = ".env"
```

---

## Security Considerations

### Input Validation
- URL validation before scraping
- Sanitize user input for search queries
- Validate file paths to prevent directory traversal
- Limit file sizes to prevent DoS

### Rate Limiting
- Limit scraping requests per IP
- Add delays between scrapes to respect robots.txt
- Implement exponential backoff for retries

### File System Security
- Validate filename slugs
- Prevent path traversal in slug generation
- Use atomic file operations
- Set proper file permissions

### Network Security
- Use HTTPS for scraping when available
- Set appropriate User-Agent headers
- Respect robots.txt
- Handle SSL certificate errors gracefully

### Docker Security
- Run as non-root user
- Minimal base image (python:slim)
- No sensitive data in image
- Regular security updates

---

## Performance Considerations

### Optimization Strategies
1. **Lazy Loading**: Load recipe content only when needed
2. **Index Caching**: Keep index in memory for fast searches
3. **Pagination**: Limit results per page
4. **Async Operations**: Use async/await for I/O operations
5. **Connection Pooling**: Reuse database connections

### Scaling Considerations
- SQLite suitable for < 10,000 recipes
- For larger deployments, consider PostgreSQL
- Add Redis cache for frequently accessed recipes
- Implement CDN for static assets

---

## Maintenance & Operations

### Backup Strategy
- **Database**: Copy `/data/recipe_index.db`
- **Recipes**: Backup `/data/recipes/` directory
- Frequency: Daily automated backups on NAS
- Can rebuild index from markdown files if database corrupted

### Monitoring
- Application logs in stdout (Docker logs)
- Health check endpoint: `/health`
- Metrics: recipes count, scraping success rate, search performance

### Troubleshooting
- Check logs: `docker logs recipe-holder`
- Rebuild index if search not working
- Verify volume mounts for persistent data
- Test network connectivity for scraping

---

## Future Enhancements

### Planned Features
- Meal planning calendar
- Shopping list generation
- Recipe scaling (adjust servings)
- Recipe collections/cookbooks
- Export to PDF
- Nutrition information
- Recipe rating system
- Multi-language support

### Technical Improvements
- Full-text search with ranking
- Elasticsearch integration
- Recipe recommendation engine
- Mobile-responsive design improvements
- Progressive Web App (PWA)
- Offline support

---

## References

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [recipe-scrapers GitHub](https://github.com/hhursev/recipe-scrapers)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

### Standards
- [Schema.org Recipe](https://schema.org/Recipe) - Recipe markup standard
- [Markdown Specification](https://spec.commonmark.org/)
- [YAML Specification](https://yaml.org/spec/)

---

**End of Technical Documentation**
