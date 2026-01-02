# RecipeHolder Test Instructions

## Running the Complete Test Suite

### Prerequisites
```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio httpx pytest-cov
```

### Run All Tests
```bash
# From project root
pytest testing/recipe-management/ -v

# With coverage report
pytest testing/recipe-management/ --cov=app --cov-report=html --cov-report=term

# View HTML coverage report
# Open htmlcov/index.html in browser
```

### Run Specific Test Files
```bash
# Test scraper module
pytest testing/recipe-management/test_scraper.py -v

# Test storage module
pytest testing/recipe-management/test_storage.py -v

# Test search service
pytest testing/recipe-management/test_search.py -v

# Test API endpoints
pytest testing/recipe-management/test_api.py -v
```

### Run Specific Test Classes or Functions
```bash
# Run a specific test class
pytest testing/recipe-management/test_scraper.py::TestRecipeScraper -v

# Run a specific test function
pytest testing/recipe-management/test_scraper.py::TestRecipeScraper::test_scraper_initialization -v
```

## Test Structure

```
testing/recipe-management/
├── conftest.py           # Shared fixtures and configuration
├── test_scraper.py       # Recipe scraper tests
├── test_storage.py       # File storage tests
├── test_search.py        # Search and indexing tests
└── test_api.py           # FastAPI endpoint tests
```

## Test Coverage

Expected coverage by module:
- `app/scraper.py`: 85%+
- `app/storage.py`: 90%+
- `app/search.py`: 85%+
- `app/main.py`: 80%+
- Overall: 85%+

## Common Test Scenarios

### Testing Recipe Scraping
```python
# Tests invalid URLs
# Tests timeout handling
# Tests successful scraping
# Tests tag extraction
```

### Testing Storage
```python
# Tests file creation with frontmatter
# Tests file reading and parsing
# Tests file deletion
# Tests markdown rendering
```

### Testing Search
```python
# Tests adding recipes to index
# Tests duplicate detection
# Tests search by title/tags
# Tests index rebuilding
```

### Testing API
```python
# Tests all endpoints
# Tests error handling
# Tests form submissions
# Tests JSON responses
```

## Continuous Integration

To run tests in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest testing/ --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Manual Testing Checklist

### ✅ Before Deployment

1. **Scraping**
   - [ ] Scrape from AllRecipes
   - [ ] Scrape from Food Network
   - [ ] Scrape from unsupported site (should fail gracefully)
   
2. **Storage**
   - [ ] Recipe files created in data/recipes/
   - [ ] Files have correct YAML frontmatter
   - [ ] Files are human-readable
   
3. **Search**
   - [ ] Search by recipe name works
   - [ ] Tag filtering works
   - [ ] Results are accurate
   
4. **UI**
   - [ ] Home page loads
   - [ ] Recipe detail page loads
   - [ ] Add recipe form works
   - [ ] Search bar works
   
5. **API**
   - [ ] GET /api/recipes returns data
   - [ ] POST /api/recipe adds recipe
   - [ ] Health check returns healthy status
   
6. **Docker**
   - [ ] Container builds successfully
   - [ ] Container starts without errors
   - [ ] Data persists after restart
   - [ ] Logs are accessible

## Debugging Failed Tests

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure you're in the project root
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Database Errors**
   ```bash
   # Tests use temporary databases
   # Check that temp directories are writable
   ```

3. **Fixture Errors**
   ```bash
   # Make sure conftest.py is present
   # Check fixture dependencies
   ```

### Verbose Output
```bash
# Show print statements
pytest testing/ -v -s

# Show full error traces
pytest testing/ -v --tb=long

# Stop on first failure
pytest testing/ -x
```

## Performance Testing

```bash
# Time each test
pytest testing/ --durations=10

# Run tests in parallel (if installed pytest-xdist)
pytest testing/ -n auto
```

## Test Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures to clean up test data
3. **Mocking**: Mock external dependencies (HTTP requests)
4. **Coverage**: Aim for 85%+ code coverage
5. **Fast**: Keep tests fast (< 1 second each)

---

**Note**: All tests use temporary directories and databases. No production data is affected during testing.
