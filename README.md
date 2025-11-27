# ML Webview

**A web dashboard for ML projects where you can watch your models train, monitor statistics, and view past performance, even away from home.**

## Tech Stack
- **Docker & Docker Compose**
- **Backend:** Flask + Flask-SocketIO for real-time updates
- **Frontend:** Svelte with Chart.js for live graphing
- **Database:** PostgreSQL for storing previous training runs and their metrics
- **Reverse Proxy:** Caddy to serve frontend and backend

## Prerequisites
- Docker & Docker Compose
- Node.js & npm (to build the frontend)
- `.env` file (with the necessary variables)

## Environment Variables
### Copy the `.env.example` as `.env` and fill in or edit the secrets:
- SECRET_KEY: JWT secret key
- USERNAME: username for webview
- PASSWORD: password for webview
- POSTGRES_USER: username for database
- POSTGRES_PASSWORD: password for database
- POSTGRES_DB: database name
Docker Compose uses the `.env` file.

## Run with Docker
### 1. Build Frontend Files
Navigate to the `./frontend/` folder and build static files into `./frontend/dist` for Caddy to serve.
```
cd frontend
npm install
npm run build
```

### 2. Run Docker Compose
Navigate to project folder and build and run Docker Compose in detached mode.
```
docker compose up --build -d
```
### 3. Port Forward
Caddy serves the webview at `http://<your_local_ip>:8080`.
In order to access webview from outside your LAN, forward the host port to the internet.

## Connecting Your Model and Training Loop
**`mnistSimple.py` is provided as an example.**

### Modifying Your Training Loop

Use the provided SocketCallback helper — do not emit Socket.IO events directly from random files. The callback centralizes socket emits, training history management, and the stop event.

1. `app.py` must import your training loop method (e.g. `from mnistSimple import train_model`) and use it in `start_training_thread()` passing a `SocketCallback` instance.
2. Your training loop function must accept the callback, call `callback.update(...)` during training, and call `callback.finished()` when done. It must also stop when `stop_event.is_set()`.
3. Modify `requirements.txt` for the modules you used.

### Modifying Graphed Data
Your `callback.update(...)` call defines the data that will be displayed on the graphs. The frontend is adaptive and can automatically graph multiple metrics. Here's an example of a simple callback update: 
```
callback.update({'epoch': epoch, 'loss': epoch_loss, 'random': np.random.rand()})
```
Epoch is always used as the key value while all other values are used as metrics and given their own separate graph. This particular update will display two separate graphs for both `loss` and `random`. Another benefit of this adaptability is that, should you decide to change the metrics you display, your previously saved training runs will not be affected and you can still view them.