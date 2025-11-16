from flask import Flask, send_from_directory, jsonify, request, make_response # type: ignore
from flask_socketio import SocketIO, emit # type: ignore
import threading
import os
import time
import datetime
import jwt # type: ignore
from mnistSimple import train_model
from interface import SocketCallback

BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'dist'))

app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path='')
socketio = SocketIO(app, cors_allowed_origins="*")

training_thread = None
training_history = []

stop_event = threading.Event()

SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')

def start_training_thread():
    callback = SocketCallback(socketio, training_history, stop_event)
    train_model(callback=callback)

def check_auth():
    token = request.cookies.get('jwt')
    if not token:
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload.get('user') == 'admin'
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

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

@app.route('/api/start', methods=['POST'])
def start_training():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    global training_thread, stop_event
    if training_thread is None or not training_thread.is_alive():
        training_history.clear()
        stop_event.clear()
        training_thread = threading.Thread(target=start_training_thread)
        training_thread.start()
        socketio.emit('status', {'training': True})
        return "Training started!"
    else:
        return "Training already in progress!"
    

@app.route('/api/stop', methods=['POST'])
def stop_training():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    global stop_event
    if training_thread and training_thread.is_alive():
        stop_event.set()
        training_thread.join(timeout=1)
        socketio.emit('status', {'training': False})
        return "Training stopped!"
    else:
        return "No training in progress!"

@app.route('/api/status', methods=['GET'])
def training_status():
    if not check_auth():
        return jsonify({'loggedIn': False, 'message': 'Unauthorized'}), 401
    return jsonify({'loggedIn': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username == 'admin' and password == 'password':
        payload = {
            'user': 'admin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # Return as HttpOnly cookie
        resp = make_response(jsonify({'success': True}))
        resp.set_cookie(
            'jwt',
            token,
            httponly=True,
            samesite='Lax',
            secure=False
        )
        return resp

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    

# --- Run ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, debug=True)
