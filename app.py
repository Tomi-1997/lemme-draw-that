from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room
from ConstantArray import ConstantArray
from Room import Room
from User import User
from my_lib import random_str, get_nickname

app = Flask(__name__)
socket_io = SocketIO(app)

# todo -- generalise to a number of rooms (Fixed size list to hold recent strokes)
stroke = ConstantArray()

# {Code -> Room}
rooms = {}

# {Ip -> Room}
ip_to_room = {}

_CODE_LEN = 6


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

    # Create room
    room_code = random_str(_CODE_LEN, rooms)
    if room_code == -1:
        message = "Error creating room"
        socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
        return
    new_room = Room(room_code)

    # Add host to room {todo add room.admin?}
    rooms[room_code] = new_room
    print(f'{user_ip} hosts!')
    add_x_to_room(x=user_ip, room_key=room_code, room_val=new_room, client_id=client_id)


@socket_io.on('join')
def handle_join(data):

    import re
    code = data['code']
    not_numbers = re.findall(r'[^0-9]', code)
    numbers = re.findall(r'[0-9]', code)

    client_id = request.sid
    client_ip = request.remote_addr

    if len(not_numbers) > 0:
        message = "Non-numbers in code."
        socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    if len(numbers) != _CODE_LEN:
        message = "Six digits required."
        socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)
        return

    for key, val in rooms.items():

        found_match = (key == code)  # There is a room with requested code
        in_room = val.ip_present(client_ip)  # Client already inside
        if found_match and not in_room:

            # Add
            add_x_to_room(x=client_ip, room_key=key, room_val=val, client_id=client_id)
            return

    message = "No such room."
    socket_io.emit('room_code', {'code': '-1', 'message': message}, to=client_id)


@socket_io.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    client_id = request.sid
    print(f'{client_id} Connects from {client_ip}.')

    if client_ip in ip_to_room:
        val = ip_to_room[client_ip]
        key = val.code
        join_room(key)
        print(f'{client_ip} joins room {key} from another browser!')
        print(rooms)

        data = {'code': key,
                'users': val.user_nicks(),
                'my_nick': val.find_nick(client_ip),
                }

        # Return to sender
        socket_io.emit('room_code', data, to=client_id)


@socket_io.on('disconnect')
def handle_disconnect():  #todo user.browserConnected -= 1
    client_ip = request.remote_addr
    client_id = request.sid
    print(f'{client_id} Disconnects from {client_ip}.')
    try_leave(client_ip, client_id)


@socket_io.on('leave')
def handle_leave():  #todo user.browserConnected -= 1
    client_ip = request.remote_addr
    client_id = request.sid
    print(f'{client_id} Leaves from {client_ip}.')
    try_leave(client_ip, client_id)


def add_x_to_room(x, room_key, room_val, client_id):
    join_room(room_key)
    ip_to_room[x] = room_val
    nickname = get_nickname(room_val)
    user = User(x, nickname)
    room_val.add(user)
    print(f'{x} joins room {room_key} as {nickname}!')
    print(rooms)

    data = {'code': room_key,
            'users': room_val.user_nicks(),
            'my_nick': nickname,
            }

    # Return to sender
    socket_io.emit('room_code', data, to=client_id)
    # Notify others
    socket_io.emit('room_update', {'users': room_val.user_nicks()}, room=room_key, include_self=False)


def rm_x_from_room(x, room_key, room_val, client_id):
    leave_room(room_key)
    del ip_to_room[x]
    room_val.rm(x)
    print(f'{x} leaves room {room_key}!')

    if room_val.is_empty():
        del rooms[room_key]
        print(f'{room_key} is empty, deleting.')
    print(rooms)


def try_leave(client_ip, client_id):
    # todo log user.timesConnect for each browser connect
    # todo, if user leaves from another browser, room could be deleted
    if client_ip in ip_to_room:
        val = ip_to_room[client_ip]
        key = val.code
        rm_x_from_room(x=client_ip, room_key=key, room_val=val, client_id=client_id)


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


if __name__ == '__main__':
    print("Starting")
    socket_io.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=8080, debug=True)
