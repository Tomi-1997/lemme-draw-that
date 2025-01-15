import os

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socket_io = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')


@socket_io.on('draw')
def handle_draw(data):
    socket_io.emit('draw', data)


if __name__ == '__main__':
    socket_io.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=8080)
