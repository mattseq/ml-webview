from flask import Flask, send_from_directory # type: ignore
from flask_socketio import SocketIO # type: ignore
import threading
import time
import torch # type: ignore
import torch.nn as nn # type: ignore
import torch.optim as optim # type: ignore
from mnistSimple import train_model

app = Flask(__name__, static_folder='/frontend')
socketio = SocketIO(app, cors_allowed_origins="*")

training_thread = None
training_history = []

def start_training_thread():
    def callback(data):
        training_history.append(data)
        socketio.emit('update', data)
    
    train_model(update_callback=callback)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    
    if training_history:
        socketio.emit('history', training_history)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/start')
def start_training():
    global training_thread
    if training_thread is None or not training_thread.is_alive():
        training_thread = threading.Thread(target=start_training_thread)
        training_thread.start()
        return "Training started!"
    else:
        return "Training already in progress!"

# --- Run ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, debug=True)
