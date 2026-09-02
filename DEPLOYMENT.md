# Web deployment

The browser version no longer needs `web_api.py`. Its game session runs locally in each browser tab, which matches the shared-table design and keeps different visitors out of each other's games.

## GitHub Pages

The workflow in `.github/workflows/deploy-pages.yml` builds and publishes the frontend whenever `main` is pushed.

1. Open the repository on GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, choose **GitHub Actions** as the source.
4. Push `main`, or run **Deploy GitHub Pages** from the Actions tab.

The project-repository path is detected automatically, including card artwork URLs.

## Local development

Run `./start_web.ps1` from PowerShell. Only the frontend development server is required now. The Python implementation remains the canonical reference and terminal version.
