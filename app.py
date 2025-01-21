from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socket_io = SocketIO(app)
history = []  # List of strokes
stroke = []  # List of recently drawn lines


@app.route('/')
def index():
    return render_template('index.html')


@socket_io.on('draw')
def handle_draw(data):
    socket_io.emit('draw', data, include_self=False)
    # stroke.append(data)


@socket_io.on('draw_done')
def handle_draw(data):
    socket_io.emit('draw_done', data, include_self=False)
    # history.append(stroke)
    # stroke.clear()
    # print('------------------------')
    # print(len(history))


@socket_io.on('clear')
def handle_draw(data):
    socket_io.emit('clear', data, include_self=False)


if __name__ == '__main__':
    socket_io.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=8080, debug=True)
