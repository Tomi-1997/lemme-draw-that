import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room
from Room import Room
from User import User
from my_lib import *

app = Flask(__name__)
socket_io = SocketIO(app)

# {Code: Room}
rooms = {}
# {  ID: Room}
id_to_room = {}
# {Constants}
_MAX_ROOM = 8  # Max rooms overall
_MAX_USERS = 8  # Max users for one room
_ROOM_CODE_LEN = 6

app.config['MAX_CONTENT_LENGTH'] = 128

# { (id, 1) : 0903943) (user id, draw request, last time requested)
id_requests = {}
_MILLI = 1000000  # Nano to milli
_SEC = 1000 * _MILLI
_REQUEST_DEFAULT = 0
_REQUEST_DRAW = 1
_REQUEST_HOST = 2
_REQUEST_JOIN = 3
_REQUEST_CLEAR = 4
_REQUEST_GUESS = 5
_REQUEST_LOCK = 6

request_dt_ignore = {_REQUEST_DRAW: 8 * _MILLI}
request_dt_ignore_def = _SEC


@app.route('/')
def index():
    return render_template('index.html')


def send_private_data(event, data, to):
    try:
        socket_io.emit(event, data, to=to)
    except Exception as e:
        print(f'Error sending data to {to}, error: {e}')
        try_leave(to)


def send_room_data(event, data, include_self, room, src=None):
    try:
        socket_io.emit(event, data, include_self=include_self, room=room)
    except Exception as e:
        print(f'Error sending data to {src}, error: {e}')
        if src is not None:
            try_leave(src)


def too_soon(uid, request_id=_REQUEST_DEFAULT):
    tup = (uid, request_id)
    if tup in id_requests:

        # Calculate time between previous request
        prev_req = id_requests[tup]
        time_diff = time.time_ns() - prev_req

        # Compare difference to threshold
        threshold = request_dt_ignore.get(request_id, request_dt_ignore_def)
        if time_diff < threshold:
            return True

    id_requests[tup] = time.time_ns()
    return False


@socket_io.on('host')
def handle_host():
    client_id = request.sid
    if too_soon(client_id, _REQUEST_HOST):
        return

    # User clicked on host
    # ☻ Check if already inside a room
    # ☻ Check if there are rooms available
    # ☻ Generate room code, validate
    # ☻ Create room
    # ☻ Add to room, send data

    if client_id in id_to_room:
        return

    # Check for room limit
    if len(rooms) >= _MAX_ROOM:
        message = "Room capacity reached"
        send_private_data('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    # Create room
    room_code = random_str(_ROOM_CODE_LEN, rooms)
    if room_code == -1:
        message = "Error creating room"
        send_private_data('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    new_room = Room(room_code)
    rooms[room_code] = new_room
    print(f'[{now()}] {client_id} hosts!')
    add_id_to_room(uid=client_id, room_key=room_code, room_val=new_room)


@socket_io.on('join')
def handle_join(data):
    client_id = request.sid
    if too_soon(client_id, _REQUEST_JOIN):
        return

    # User clicked on JOIN
    # ☻ Validate user input
    # ☻ Search for room with same code
    # ☻ Check room capacity
    # ☻ Add to room, send data

    import re
    code = data['code']
    not_numbers = re.findall(r'[^0-9]', code)
    numbers = re.findall(r'[0-9]', code)

    if len(not_numbers) > 0:
        message = "Non-numbers in code."
        send_private_data('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    if len(numbers) != _ROOM_CODE_LEN:
        message = "Six digits required."
        send_private_data('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    for key, val in rooms.items():

        if key != code:  # Different room key
            continue
        if val.id_present(client_id):  # Room has same ID inside, somehow
            continue

        if val.locked():  # Room locked
            message = "Room is locked."
            send_private_data('room_code', {'code': '-1', 'message': message}, to=client_id)
            return

        if val.len() >= _MAX_USERS:  # Room reached user capacity
            message = "Room is full."
            send_private_data('room_code', {'code': '-1', 'message': message}, to=client_id)
            return

        # Add user to room
        add_id_to_room(uid=client_id, room_key=key, room_val=val)
        return

    message = "No such room."
    send_private_data('room_code', {'code': '-1', 'message': message}, to=client_id)


@socket_io.on('connect')
def handle_connect():
    # User connected to web
    # ☻ Wait for join \ host

    client_ip = request.remote_addr
    uid = request.sid

    print(f'[{now()}] {uid} Connects from {client_ip}.')


@socket_io.on('disconnect')
def handle_disconnect():

    # User left website
    # ☺ Check if inside a room
    # ☺ Remove

    client_id = request.sid
    print(f'[{now()}] {client_id} DCs.')
    try_leave(client_id)


@socket_io.on('leave')
def handle_leave():
    client_id = request.sid
    if too_soon(client_id):
        return
    # User pressed LEAVE
    # ☺ Check if inside a room
    # ☺ Remove

    client_id = request.sid
    print(f'[{now()}] {client_id} Leaves.')
    try_leave(client_id)


def add_id_to_room(uid, room_key, room_val):
    # User joined \ hosted
    # ☺ Add to socketIO room
    # ☺ Generate nickname
    # ☺ Create User, add to room
    # ☺ Send him room code, canvas data
    # ☺ Send others user list
    try:
        join_room(room_key)
    except Exception as e:
        print(f'Error on join_room() {room_key} with client id {uid}, error: {e}')
        message = "Error joining room."
        send_private_data('room_code', {'code': '-1', 'message': message}, to=uid)
        return

    id_to_room[uid] = room_val
    nickname = get_nickname(room_val)
    user = User(uid, nickname)
    room_val.add(user)
    print(f'[{now()}] {uid} joins room {room_key} as {nickname}!')
    print(rooms)

    data = {'code': room_key,
            'users': room_val.user_nicks(),
            'my_nick': nickname,
            }

    # Return to sender
    send_private_data('room_code', data, to=uid)
    # Notify others
    send_room_data('room_update', {'users': room_val.user_nicks()}, room=room_key, include_self=False, src=uid)
    # Sender newly connected user the current board
    for draw_data in room_val.get_board():
        if draw_data == -1:
            continue
        send_private_data('draw', draw_data, to=uid)


def rm_id_from_room(uid, room_key, room_val):
    # User left \ dc's
    # ☺ Remove from socketIO room
    # ☺ Remove from room and dict
    # ☺ Remove room if empty, notify others otherwise

    try:
        leave_room(room_key)
    except Exception as e:
        print(f'Error on leave_room() {room_key} with client id {uid}, error: {e}')

    del id_to_room[uid]
    room_val.rm(uid)
    print(f'[{now()}] {uid} leaves room {room_key}!')

    if room_val.is_empty():
        del rooms[room_key]
        print(f'[{now()}] {room_key} is empty, deleting.')
        return

    # Not empty, notify others
    send_room_data('room_update', {'users': room_val.user_nicks()}, room=room_key, include_self=False)
    print(rooms)


def try_leave(client_id):
    # ☺ Check if inside a room
    # ☺ Remove
    if client_id in id_to_room:
        val = id_to_room[client_id]
        key = val.code
        rm_id_from_room(uid=client_id, room_key=key, room_val=val)


def illegal_draw(data):
    keys = ['normX', 'normLX', 'normY', 'normLY']
    for key in keys:
        if key not in data:
            return True
        val = data[key]
        if val > 1 or val < 0:
            return True
    return False


@socket_io.on('draw')
def handle_draw(data):
    client_id = request.sid
    if too_soon(client_id, _REQUEST_DRAW):
        return

    if client_id not in id_to_room:
        return

    if illegal_draw(data):
        return

    room = id_to_room[client_id].code
    send_room_data('draw', data, include_self=False, room=room, src=client_id)
    rooms[room].draw(data)  # Remember draw history


@socket_io.on('clear')
def handle_clear(data):
    client_id = request.sid
    if too_soon(client_id, _REQUEST_CLEAR):
        return

    if client_id not in id_to_room:
        return

    # Validate data

    # Data okay, clear board
    room = id_to_room[client_id].code
    print(f'[{now()}] {client_id} Clears board in room {room}.')

    # Notify, clear board mem
    send_room_data('clear', data, include_self=False, room=room, src=client_id)
    rooms[room].clear_board()  # Clear draw history


def illegal_guess(data):
    if 'len' not in data:
        return True
    if data['len'] > 10 or data['len'] < 2:
        return True
    return True


@socket_io.on('guess')
def handle_guess(data):
    client_id = request.sid
    if too_soon(client_id, _REQUEST_GUESS):
        return

    if client_id not in id_to_room:
        return

    # Validate data
    if invalid_guess(data):
        return

    # Data ok, send others guess
    room = id_to_room[client_id].code
    print(f'd={data}')
    print(f'[{now()}] {client_id} Sends a guess in room {room}.')
    send_room_data('guess', data, include_self=False, room=room, src=client_id)


@socket_io.on('lock')
def handle_lock():
    client_id = request.sid
    if too_soon(client_id, _REQUEST_LOCK):
        return

    if client_id not in id_to_room:
        return

    # Validate data
    # ... (no data)

    # Data okay, send room lock state
    room = id_to_room[client_id].code
    print(f'[{now()}] {client_id} Sends a lock \\ unlock request in room {room}.')
    rooms[room].lock_unlock()
    send_room_data('lock', {'lock': rooms[room].locked()}, include_self=True, room=room, src=client_id)


def now():
    return time.ctime()


if __name__ == '__main__':
    print("Starting")
    socket_io.run(app, host='0.0.0.0', port=8000)
