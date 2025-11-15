from flask import Flask, send_from_directory # type: ignore
from flask_socketio import SocketIO, emit # type: ignore
import threading
import os
import time
import torch # type: ignore
import torch.nn as nn # type: ignore
import torch.optim as optim # type: ignore
from mnistSimple import train_model
from interface import SocketCallback

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'dist'))

app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

training_thread = None
training_history = []

stop_event = threading.Event()

def start_training_thread():
    callback = SocketCallback(socketio, training_history, stop_event)
    train_model(callback=callback)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    
    if training_history:
        emit('history', training_history)

    # send current status
    if training_thread and training_thread.is_alive():
        emit('status', {'training': True})
    else:
        emit('status', {'training': False})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/start')
def start_training():
    global training_thread, stop_event
    if training_thread is None or not training_thread.is_alive():
        training_history.clear()
        stop_event.clear()
        training_thread = threading.Thread(target=start_training_thread)
        training_thread.start()
        return "Training started!"
    else:
        return "Training already in progress!"

@app.route('/stop')
def stop_training():
    global stop_event
    if training_thread and training_thread.is_alive():
        stop_event.set()
        return "Training stopped!"
    else:
        return "No training in progress!"

@app.route('/status')
def training_status():
    if training_thread and training_thread.is_alive():
        return {'training': True}
    else:
        return {'training': False}

# --- Run ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, debug=True)
