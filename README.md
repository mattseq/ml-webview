# ML Webview

**A web dashboard for ML projects where you can watch your models train, monitor statistics, and view past performance.**

## Tech Stack
- **Backend:** Flask + Flask-SocketIO for real-time updates
- **Frontend:** Svelte with Chart.js for live graphing

## Run with Docker
### Build Frontend Files
Navigate to the `./frontend/` folder and build static files into `./frontend/dist` for Flask to serve.
```
cd frontend
npm run build
```

### Run with Docker
Build Docker image using Docker Compose and run in detached mode.
```
docker compose up --build -d
```

