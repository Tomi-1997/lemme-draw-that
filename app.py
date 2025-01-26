import base64

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from ConstantArray import ConstantArray

app = Flask(__name__)
socket_io = SocketIO(app)
stroke = ConstantArray()


@app.route('/')
def index():
    return render_template('index.html')


@socket_io.on('draw')
def handle_draw(data):
    socket_io.emit('draw', data, include_self=False)
    stroke.append(data)


@socket_io.on('draw_done')
def handle_draw(data):
    socket_io.emit('draw_done', data, include_self=False)


@socket_io.on('clear')
def handle_draw(data):
    print(f'{request.sid} Clears board.')
    socket_io.emit('clear', data, include_self=False)
    stroke.clear()


@socket_io.on('guess')
def handle_guess(data):
    print(f'{request.sid} Sends guess.')
    socket_io.emit('guess', data, include_self=False)


# @app.route('/upload', methods=['POST'])
# def upload():
#     data = request.get_json()
#     image_data = data['image']
#
#     # Remove the prefix (data:image/png;base64,)
#     header, encoded = image_data.split(',', 1)
#     binary_data = base64.b64decode(encoded)
#
#     # Save the image to a file
#     with open('canvas_image.png', 'wb') as f:
#         f.write(binary_data)
#
#     return jsonify({'message': 'Image saved successfully!'})
#
#
# def load():
#     with open('canvas_image.png', 'rb') as f:
#         encoded_string = base64.b64encode(f.read()).decode('utf-8')
#
#     data = {
#         'message': 'Welcome to the canvas!',
#         'image': f'data:image/png;base64,{encoded_string}'  # Base64 string
#     }


@socket_io.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    client_id = request.sid
    print(f'{request.sid} Connects from {client_ip}.')

    # Send current board state
    for data in stroke.data:
        if data == -1:
            continue
        socket_io.emit('draw', data, to=client_id)


if __name__ == '__main__':
    socket_io.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=8080, debug=True)
