# ML Webview

**A web dashboard for ML projects where you can watch your models train, monitor statistics, and view past performance.**

## Tech Stack
- **Backend:** Flask + Flask-SocketIO for real-time updates
- **Frontend:** Svelte with Chart.js for live graphing
- **Reverse Proxy:** Caddy to serve frontend and backend

## Run with Docker
### 1. Build Frontend Files
Navigate to the `./frontend/` folder and build static files into `./frontend/dist` for Caddy to serve.
```
cd frontend
npm run build
```

### 2. Run Docker Compose
Navigate to project folder and build and run Docker Compose in detached mode.
```
docker compose up --build -d
```