class SocketCallback:
    def __init__(self, socketio, training_history, stop_event):
        self.socketio = socketio
        self.training_history = training_history
        self.stop_event = stop_event
    def update(self, data):
        self.training_history.append(data)
        self.socketio.emit('update', data)
    def finished(self):
        self.socketio.emit('status', {'training': False})
    def stop(self):
        self.socketio.emit('status', {'training': False})