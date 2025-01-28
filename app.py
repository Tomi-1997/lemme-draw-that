from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room
from ConstantArray import ConstantArray
from Room import Room
from my_lib import random_str

app = Flask(__name__)
socket_io = SocketIO(app)

# todo -- generalise to a number of rooms (Fixed size list to hold recent strokes)
stroke = ConstantArray()

# {Code -> Room} (code is a 6 letter string: 2 are numbers, rest are letters) --todo change to 6 digits
rooms = {}

# {Ip -> Room}
ip_to_room = {}

_LETTERS = 4  ## todo change to 6 digits
_NUMBERS = 2


@app.route('/')
def index():
    return render_template('index.html')


@socket_io.on('host')
def handle_host():
    user_ip = request.remote_addr
    client_id = request.sid

    # Ignore, will be sent code
    if user_ip in ip_to_room:
        return

    # todo- convert code to 6 digits
    room_code = random_str(_LETTERS, _NUMBERS)  # todo- Check for clashes with current ids
    new_room = Room(user_ip, room_code)

    # todo- bundle a single onJoin() func
    rooms[room_code] = new_room
    ip_to_room[user_ip] = new_room
    socket_io.emit('room_code', {'code': room_code}, to=client_id)
    join_room(room_code)

    print(f'{user_ip} hosts! Rooms now:')
    print(rooms)


@socket_io.on('join')
def handle_join(data):

    # todo - convert to 6 digit code
    import re
    code = data['code']
    letters = re.findall(r'[a-z]', code)
    numbers = re.findall(r'[0-9]', code)
    client_id = request.sid
    client_ip = request.remote_addr

    # todo - send actual error code
    if len(letters) != _LETTERS or len(numbers) != _NUMBERS:
        socket_io.emit('room_code', {'code': '-1'}, to=client_id)
        return

    for key, val in rooms.items():
        if key == code:
            # todo - bundle to onJoin func
            socket_io.emit('room_code', {'code': code}, to=client_id)
            join_room(key)
            ip_to_room[client_ip] = val
            val.add(client_ip)
            print(f'{client_ip} joins room {key}! Rooms now')
            print(rooms)
            return

    # todo - send actual error code
    socket_io.emit('room_code', {'code': '-1'}, to=client_id)


@socket_io.on('draw')
def handle_draw(data):
    ip = request.remote_addr
    if ip not in ip_to_room:
        return
    socket_io.emit('draw', data, include_self=False, room=ip_to_room[ip].code)
    stroke.append(data)


@socket_io.on('clear')
def handle_draw(data):
    ip = request.remote_addr
    if ip not in ip_to_room:
        return
    print(f'{ip} Clears board.')  # todo - give more info (which room, etc)
    socket_io.emit('clear', data, include_self=False, room=ip_to_room[ip].code)
    stroke.clear()


@socket_io.on('guess')
def handle_guess(data):
    ip = request.remote_addr
    if ip not in ip_to_room:
        return
    print(f'{ip} Sends guess.')  # todo - give more info (which room, etc)
    socket_io.emit('guess', data, include_self=False, room=ip_to_room[ip].code)


@socket_io.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    client_id = request.sid
    print(f'{request.sid} Connects from {client_ip}.')
    print(rooms)

    # todo - bundle to onJoin() func
    if client_ip in ip_to_room:
        room = ip_to_room[client_ip]
        print(f'Redirecting {client_id} to existing room')
        socket_io.emit('room_code', {'code': room.code}, to=client_id)
        join_room(room.code)

    # # Send current board state
    # for data in stroke.data:
    #     if data == -1:
    #         continue
    #     socket_io.emit('draw', data, to=client_id)


if __name__ == '__main__':
    print("Starting")
    socket_io.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=8080, debug=True)
