# RecipeHolder

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

A Docker-based recipe management application that scrapes recipes from websites and stores them as clean, readable markdown files. No more ads, no more clutter—just your recipes, accessible as text files.

## ✨ Features

- **🌐 Universal Recipe Scraping**: Supports 600+ recipe websites (AllRecipes, Food Network, Serious Eats, etc.)
- **📝 Text-Based Storage**: Recipes stored as markdown files with YAML frontmatter for direct filesystem access
- **🔍 Fast Search**: SQLite-powered indexing for quick searching and browsing
- **🏷️ Automatic Tagging**: Extracts and organizes recipes with tags
- **🐳 Docker Ready**: Easy deployment on NAS or any Docker-compatible system
- **🎨 Clean Interface**: Ad-free, distraction-free web interface
- **📖 Print Friendly**: Beautiful recipe views optimized for printing
- **🔌 REST API**: Full API for programmatic access

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RecipeHolder
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Open your browser to http://localhost:8000
   - Start adding recipes from your favorite websites!

### Manual Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## 📖 Usage

### Adding Recipes

1. Click "Add Recipe" in the navigation
2. Paste the recipe URL (e.g., `https://pipingpotcurry.com/chicken-curry-pressure-cooker/`)
3. Click "Scrape Recipe"
4. The recipe is automatically extracted and saved!

### Searching Recipes

- Use the search bar on the home page
- Filter by tags
- Browse all recipes in a clean, card-based layout

### Accessing Recipe Files

All recipes are stored as markdown files in the `data/recipes/` directory:

```
data/
├── recipes/
│   ├── chicken-curry-pressure-cooker.md
│   ├── chocolate-chip-cookies.md
│   └── ...
└── recipe_index.db
```

You can read, edit, or backup these files directly from your file system!

## 🏗️ Project Structure

```
RecipeHolder/
├── app/                          # Application code
│   ├── main.py                   # FastAPI application
│   ├── models.py                 # Database models
│   ├── scraper.py                # Recipe scraping logic
│   ├── storage.py                # File storage operations
│   ├── search.py                 # Search and indexing
│   ├── config.py                 # Configuration
│   ├── database.py               # Database management
│   └── utils.py                  # Utility functions
├── templates/                    # Jinja2 HTML templates
├── static/                       # Static assets (CSS, JS)
├── testing/recipe-management/    # Test suite
├── documentation/                # Technical documentation
│   └── recipe-management/
│       ├── implementation-tracker.md
│       └── technical-documentation.md
├── data/                         # Data directory (volume mount)
│   ├── recipes/                  # Markdown recipe files
│   └── recipe_index.db           # SQLite index
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker Compose configuration
└── requirements.txt              # Python dependencies
```

## 🔧 Configuration

Environment variables (create `.env` file):

```env
DATABASE_PATH=/data/recipe_index.db
RECIPES_PATH=/data/recipes
LOG_LEVEL=INFO
MAX_RECIPE_SIZE=1048576
SCRAPE_TIMEOUT=30
PORT=8000
```

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest testing/recipe-management/

# Run specific test file
pytest testing/recipe-management/test_scraper.py

# Run with coverage
pytest --cov=app testing/recipe-management/
```

## 📡 API Documentation

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recipes` | List all recipes |
| GET | `/api/recipe/{slug}` | Get recipe by slug |
| POST | `/api/recipe` | Add recipe from URL |
| GET | `/api/search?q={query}` | Search recipes |
| GET | `/api/tags` | List all tags |
| POST | `/api/rebuild-index` | Rebuild recipe index |
| GET | `/health` | Health check |

**Example: Add Recipe via API**
```bash
curl -X POST http://localhost:8000/api/recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/recipe"}'
```

**Interactive API Documentation**: http://localhost:8000/docs

## 🐳 Docker Deployment

### On NAS (Synology, QNAP, etc.)

1. Copy project files to your NAS
2. Edit `docker-compose.yml` to set data volume path
3. Run via Docker Compose or your NAS's Docker UI

### Custom Configuration

```yaml
version: '3.8'
services:
  recipe-holder:
    image: recipe-holder:latest
    ports:
      - "8000:8000"
    volumes:
      - /path/on/nas/data:/data
    environment:
      - LOG_LEVEL=INFO
```

## 📄 Recipe File Format

Recipes are stored with YAML frontmatter and markdown content:

```markdown
---
title: "Chicken Curry (Pressure Cooker)"
source_url: "https://example.com/recipe"
created_at: "2026-01-02T10:30:00Z"
prep_time: 15
cook_time: 20
tags:
  - chicken
  - curry
  - indian
---

# Chicken Curry (Pressure Cooker)

A delicious and quick chicken curry.

## Ingredients

- 2 lbs chicken
- 1 onion, chopped
- 2 cloves garlic

## Instructions

1. Heat oil in pressure cooker
2. Add onions and cook until golden
3. Add chicken and spices
4. Pressure cook for 10 minutes
```

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Scraping**: recipe-scrapers (600+ websites)
- **Database**: SQLite (indexing only)
- **Storage**: Markdown files with YAML frontmatter
- **Templates**: Jinja2 with Bootstrap 5
- **Deployment**: Docker & Docker Compose

## 📚 Documentation

- [Technical Documentation](documentation/recipe-management/technical-documentation.md)
- [Implementation Tracker](documentation/recipe-management/implementation-tracker.md)

## 🤝 Contributing

This is a personal project, but feel free to fork and customize for your needs!

## 📝 License

This project uses open-source libraries with permissive licenses (MIT, BSD, Apache-2.0).

## 🙏 Acknowledgments

- [recipe-scrapers](https://github.com/hhursev/recipe-scrapers) - Excellent library for recipe extraction
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Bootstrap](https://getbootstrap.com/) - UI framework

## 🐛 Troubleshooting

### Recipes not showing up
- Check if files exist in `data/recipes/`
- Run index rebuild: `POST /api/rebuild-index`

### Scraping fails
- Website might not be supported
- Check network connectivity
- Verify URL is correct

### Docker permission issues
- Ensure proper UID/GID mapping in Docker
- Check volume mount permissions

## 📞 Support

For issues, questions, or feature requests, please check the documentation first.

---

**Made with ❤️ for recipe lovers who hate ads and clutter**

