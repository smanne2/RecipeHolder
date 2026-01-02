# RecipeHolder - Getting Started Guide

## Installation & Setup

### Prerequisites

- Docker & Docker Compose (for containerized deployment)
- OR Python 3.11+ (for local development)
- At least 1GB free disk space

### Option 1: Docker Deployment (Recommended)

1. **Download the project**
   ```bash
   git clone <repository-url>
   cd RecipeHolder
   ```

2. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env if you want to customize settings
   ```

3. **Start the container**
   ```bash
   docker-compose up -d
   ```

4. **Verify it's running**
   ```bash
   docker-compose logs -f recipe-holder
   # You should see: "Application started successfully"
   ```

5. **Access the application**
   - Open browser to: http://localhost:8000
   - Health check: http://localhost:8000/health

### Option 2: Local Development

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create data directory**
   ```bash
   mkdir -p data/recipes
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Access the application**
   - Open browser to: http://localhost:8000

## First Steps

### 1. Add Your First Recipe

1. Click **"Add Recipe"** in the top navigation
2. Enter a recipe URL, for example:
   - https://pipingpotcurry.com/chicken-curry-pressure-cooker/
   - https://www.allrecipes.com/recipe/any-recipe/
3. Click **"Scrape Recipe"**
4. Wait a few seconds while the recipe is extracted
5. You'll be redirected to your new recipe!

### 2. Browse Your Recipes

- Go to the home page (http://localhost:8000)
- See all your recipes in a clean, card-based layout
- Click any recipe to view the full details

### 3. Search and Filter

- Use the **search bar** to find recipes by name
- Click **tags** to filter by category (e.g., "chicken", "dessert")
- All searches are instant!

### 4. Access Recipe Files

Your recipes are stored as text files you can access directly:

**Location**: `./data/recipes/` (or `/data/recipes/` in Docker)

```bash
# View your recipes
ls data/recipes/

# Read a recipe
cat data/recipes/chicken-curry-pressure-cooker.md

# Edit a recipe (any text editor)
nano data/recipes/chicken-curry-pressure-cooker.md

# Backup your recipes
cp -r data/recipes/ /backup/location/
```

## Using the API

### Add Recipe Programmatically

```bash
curl -X POST http://localhost:8000/api/recipe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://pipingpotcurry.com/chicken-curry-pressure-cooker/"
  }'
```

### Search Recipes

```bash
# Search by query
curl "http://localhost:8000/api/recipes?q=curry"

# Filter by tag
curl "http://localhost:8000/api/recipes?tag=chicken"

# Combine query and tag
curl "http://localhost:8000/api/recipes?q=curry&tag=indian"
```

### List All Tags

```bash
curl http://localhost:8000/api/tags
```

### Rebuild Index

If recipes aren't showing up:

```bash
curl -X POST http://localhost:8000/api/rebuild-index
```

## Common Tasks

### Backup Your Recipes

```bash
# Backup recipe files
cp -r data/recipes/ /path/to/backup/recipes-$(date +%Y%m%d)/

# Backup database index
cp data/recipe_index.db /path/to/backup/
```

### Restore Recipes

```bash
# Copy recipes back
cp -r /path/to/backup/recipes-20260102/* data/recipes/

# Rebuild index
curl -X POST http://localhost:8000/api/rebuild-index
```

### Update the Application

```bash
# Pull latest changes
git pull

# Rebuild Docker image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### View Logs

```bash
# Docker
docker-compose logs -f recipe-holder

# Local
# Logs appear in console
```

## Tips & Tricks

### Best Practices

1. **Regular Backups**: Recipe files are just markdown—easy to back up!
2. **Use Tags**: They make finding recipes easier
3. **Print View**: Use browser's print function for recipe cards
4. **Direct File Access**: Edit recipes directly if scraping misses something

### Supported Websites

The app supports 600+ recipe websites including:
- AllRecipes
- Food Network
- Serious Eats
- BBC Good Food
- Epicurious
- Minimalist Baker
- Budget Bytes
- Tasty
- And many more!

### Troubleshooting

**Problem**: Recipe scraping fails
- **Solution**: Website might not be supported, or is blocking scrapers
- **Workaround**: Copy recipe manually into markdown file

**Problem**: Recipes not showing in web interface
- **Solution**: Run rebuild index: `POST /api/rebuild-index`

**Problem**: Docker permission errors
- **Solution**: Check volume permissions, run as correct user

**Problem**: Slow scraping
- **Solution**: Some sites are slow to respond; wait up to 30 seconds

## Next Steps

- Add more recipes from your favorite sites
- Organize recipes with tags
- Share recipe files with family/friends
- Set up automated backups
- Customize the interface (edit templates/)

## Support

- Check [Technical Documentation](../documentation/recipe-management/technical-documentation.md)
- Review [Implementation Tracker](../documentation/recipe-management/implementation-tracker.md)

---

Enjoy your ad-free recipe collection! 🍳📚
