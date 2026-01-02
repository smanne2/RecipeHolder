# Static Files Directory

This directory is for custom static files, including your logo for print watermarks.

## Adding a Custom Print Logo

1. Place your logo image in this directory (e.g., `logo.png`)
2. Set the environment variable `PRINT_LOGO_URL=/static/logo.png`
3. Restart the application

### Recommended Logo Specifications

- **Format**: PNG with transparent background
- **Size**: 100-200px wide, will be scaled to ~0.25 inches height in print
- **Color**: Dark color or grayscale works best for printing

### Example Configuration

In `docker-compose.yml`:
```yaml
environment:
  - PRINT_LOGO_URL=/static/logo.png
```

Or in `.env` file:
```
PRINT_LOGO_URL=/static/logo.png
```
