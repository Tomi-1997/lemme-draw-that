from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room
from Room import Room
from User import User
from my_lib import random_str, get_nickname

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


@app.route('/')
def index():
    return render_template('index.html')


@socket_io.on('host')
def handle_host():
    # User clicked on host
    # ☻ Check if already inside a room
    # ☻ Check if there are rooms available
    # ☻ Generate room code, validate
    # ☻ Create room
    # ☻ Add to room, send data

    client_id = request.sid
    if client_id in id_to_room:
        return

    # Check for room limit
    if len(rooms) >= _MAX_ROOM:
        message = "Room capacity reached"
        socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    # Create room
    room_code = random_str(_ROOM_CODE_LEN, rooms)
    if room_code == -1:
        message = "Error creating room"
        socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    new_room = Room(room_code)
    rooms[room_code] = new_room
    print(f'{client_id} hosts!')
    add_id_to_room(uid=client_id, room_key=room_code, room_val=new_room)


@socket_io.on('join')
def handle_join(data):
    # User clicked on JOIN
    # ☻ Validate user input
    # ☻ Search for room with same code
    # ☻ Check room capacity
    # ☻ Add to room, send data

    import re
    code = data['code']
    not_numbers = re.findall(r'[^0-9]', code)
    numbers = re.findall(r'[0-9]', code)

    client_id = request.sid
    if len(not_numbers) > 0:
        message = "Non-numbers in code."
        socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    if len(numbers) != _ROOM_CODE_LEN:
        message = "Six digits required."
        socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    for key, val in rooms.items():

        if key != code:  # Different room key
            continue
        if val.id_present(client_id):  # Room has same ID inside, somehow
            continue

        if val.locked():  # Room locked
            message = "Room is locked."
            socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
            return

        if val.len() >= _MAX_USERS:  # Room reached user capacity
            message = "Room is full."
            socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
            return

        # Add user to room
        add_id_to_room(uid=client_id, room_key=key, room_val=val)
        return

    message = "No such room."
    socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)


@socket_io.on('connect')
def handle_connect():
    # User connected to web
    # ☻ Wait for join \ host

    client_ip = request.remote_addr
    uid = request.sid
    print(f'{uid} Connects from {client_ip}.')


@socket_io.on('disconnect')
def handle_disconnect():
    # User left website
    # ☺ Check if inside a room
    # ☺ Remove

    client_id = request.sid
    print(f'{client_id} DCs.')
    try_leave(client_id)


@socket_io.on('leave')
def handle_leave():
    # User pressed LEAVE
    # ☺ Check if inside a room
    # ☺ Remove

    client_id = request.sid
    print(f'{client_id} Leaves.')
    try_leave(client_id)


def add_id_to_room(uid, room_key, room_val):
    # User joined \ hosted
    # ☺ Add to socketIO room
    # ☺ Generate nickname
    # ☺ Create User, add to room
    # ☺ Send him room code, canvas data
    # ☺ Send others user list
    join_room(room_key)
    id_to_room[uid] = room_val
    nickname = get_nickname(room_val)
    user = User(uid, nickname)
    room_val.add(user)
    print(f'{uid} joins room {room_key} as {nickname}!')
    print(rooms)

    data = {'code': room_key,
            'users': room_val.user_nicks(),
            'my_nick': nickname,
            }

    # Return to sender
    socket_io.emit('room_code', data, to=uid)
    # Notify others
    socket_io.emit('room_update', {'users': room_val.user_nicks()}, room=room_key, include_self=False)
    # Sender newly connected user the current board
    for draw_data in room_val.get_board():
        if draw_data == -1:
            continue
        socket_io.emit('draw', draw_data, to=uid)


def rm_id_from_room(uid, room_key, room_val):
    # User left \ dc's
    # ☺ Remove from socketIO room
    # ☺ Remove from room and dict
    # ☺ Remove room if empty, notify others otherwise
    leave_room(room_key)
    del id_to_room[uid]
    room_val.rm(uid)
    print(f'{uid} leaves room {room_key}!')

    if room_val.is_empty():
        del rooms[room_key]
        print(f'{room_key} is empty, deleting.')
        return

    # Not empty, notify others
    socket_io.emit('room_update', {'users': room_val.user_nicks()}, room=room_key, include_self=False)
    print(rooms)


def try_leave(client_id):
    # ☺ Check if inside a room
    # ☺ Remove
    if client_id in id_to_room:
        val = id_to_room[client_id]
        key = val.code
        rm_id_from_room(uid=client_id, room_key=key, room_val=val)


@socket_io.on('draw')
def handle_draw(data):
    client_id = request.sid
    if client_id not in id_to_room:
        return
    room = id_to_room[client_id].code
    socket_io.emit('draw', data, include_self=False, room=room)
    rooms[room].draw(data)  # Remember draw history


@socket_io.on('clear')
def handle_draw(data):
    client_id = request.sid
    if client_id not in id_to_room:
        return
    room = id_to_room[client_id].code
    print(f'{client_id} Clears board in room {room}.')
    socket_io.emit('clear', data, include_self=False, room=room)
    rooms[room].clear_board()  # Clear draw history


@socket_io.on('guess')
def handle_guess(data):
    client_id = request.sid
    if client_id not in id_to_room:
        return
    room = id_to_room[client_id].code
    print(f'{client_id} Sends a guess in room {room}.')
    socket_io.emit('guess', data, include_self=False, room=room)


@socket_io.on('lock')
def handle_guess():
    client_id = request.sid
    if client_id not in id_to_room:
        return
    room = id_to_room[client_id].code
    print(f'{client_id} Sends a lock \\ unlock request in room {room}.')
    rooms[room].lock_unlock()
    socket_io.emit('lock', {'lock': rooms[room].locked()}, include_self=True, room=room)


if __name__ == '__main__':
    print("Starting")
    socket_io.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=8080, debug=True)
