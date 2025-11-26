from flask import Flask, send_from_directory, jsonify, request, make_response # type: ignore
from flask_socketio import SocketIO, emit # type: ignore
import threading
import os
import time
import datetime
import jwt # type: ignore
from mnistSimple import train_model
from interface import SocketCallback
import db

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

training_thread = None
training_history = []

stop_event = threading.Event()

training_start_time = None
training_end_time = None

SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
USERNAME = os.getenv('USERNAME', 'admin')
PASSWORD = os.getenv('PASSWORD', 'password')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/webview')
db.init_db(app)

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
    
    status = {'training': training_thread is not None and training_thread.is_alive()}
    if status['training'] and training_start_time:
        status['start_time'] = training_start_time

    emit('status', status)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    
@app.route('/api/start', methods=['POST'])
def start_training():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    global training_thread, stop_event, training_start_time, training_end_time
    if training_thread is None or not training_thread.is_alive():
        training_history.clear()
        stop_event.clear()
        training_start_time = int(datetime.datetime.utcnow().timestamp() * 1000)
        training_end_time = None
        training_thread = threading.Thread(target=start_training_thread)
        training_thread.start()
        socketio.emit('status', {'training': True, 'start_time': training_start_time})
        return "Training started!"
    else:
        return "Training already in progress!"
    

@app.route('/api/stop', methods=['POST'])
def stop_training():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    global stop_event, training_thread, training_end_time
    if training_thread and training_thread.is_alive():
        training_end_time = int(datetime.datetime.utcnow().timestamp() * 1000)
        stop_event.set()
        training_thread.join(timeout=1)
        socketio.emit('status', {'training': False})
        return "Training stopped!"
    else:
        return "No training in progress!"

@app.route('/api/status', methods=['GET'])
def status():
    if not check_auth():
        return jsonify({'loggedIn': False, 'message': 'Unauthorized'}), 401
    return jsonify({'loggedIn': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username == USERNAME and password == PASSWORD:
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

@app.route('/api/runs', methods=['POST'])
def save_run():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    global training_start_time, training_end_time, training_history
    try:
        data = request.json
        title = data.get('title', 'Untitled Run')
        description = data.get('description', '')
        start_time = training_start_time
        if training_end_time:
            end_time = training_end_time
        else:
            end_time = int(datetime.datetime.utcnow().timestamp() * 1000)

        run_id = db.save_run(title, description, start_time, end_time, training_history)
        return jsonify({'success': True, 'run_id': run_id})
    except Exception as e:
        import traceback, sys
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/runs', methods=['GET'])
def list_runs():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    runs = db.list_runs()
    return jsonify({'success': True, 'runs': runs})

@app.route('/api/runs', methods=['DELETE'])
def delete_all_runs():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    runs = db.delete_all_runs()
    return jsonify({'success': True, 'runs': runs})

@app.route('/api/runs/<run_id>', methods=['GET'])
def get_run(run_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    run = db.get_run(run_id)
    if run:
        return jsonify({'success': True, 'run': run})
    else:
        return jsonify({'success': False, 'message': 'Run not found'}), 404

@app.route('/api/runs/<run_id>', methods=['DELETE'])
def delete_run(run_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    run = db.delete_run(run_id)
    if run:
        return jsonify({'success': True, 'run': run})
    else:
        return jsonify({'success': False, 'message': 'Run not found'}), 404

@app.route('/api/runs/<run_id>', methods=['PUT'])
def edit_run(run_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.json
    title = data.get('title', None)
    description = data.get('description', None)

    run = db.edit_run(run_id, title, description)
    if run:
        return jsonify({'success': True, 'run': run})
    else:
        return jsonify({'success': False, 'message': 'Run not found'}), 404

# --- Run ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
