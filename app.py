from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room
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
    room_code = random_str(_CODE_LEN)  # todo- Check for clashes with current ids
    new_room = Room(user_ip, room_code)

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
        in_room = val.present(client_ip)  # Client already inside
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

    # todo - bundle to onJoin() func
    if client_ip in ip_to_room:
        val = ip_to_room[client_ip]
        key = val.code
        add_x_to_room(x=client_ip, room_key=key, room_val=val, client_id=client_id)

    # # Send current board state
    # for data in stroke.data:
    #     if data == -1:
    #         continue
    #     socket_io.emit('draw', data, to=client_id)


@socket_io.on('disconnect')
def handle_disconnect():
    client_ip = request.remote_addr
    client_id = request.sid
    print(f'{client_id} Disconnects from {client_ip}.')

    # todo - bundle to onJoin() func
    if client_ip in ip_to_room:
        val = ip_to_room[client_ip]
        key = val.code
        rm_x_from_room(x=client_ip, room_key=key, room_val=val, client_id=client_id)


def add_x_to_room(x, room_key, room_val, client_id):
    join_room(room_key)
    ip_to_room[x] = room_val
    room_val.add(x)
    print(f'{x} joins room {room_key}!')
    print(rooms)
    socket_io.emit('room_code', {'code': room_key}, to=client_id)


def rm_x_from_room(x, room_key, room_val, client_id):
    leave_room(room_key)
    del ip_to_room[x]
    room_val.rm(x)
    print(f'{x} leaves room {room_key}!')

    if room_val.is_empty():
        del rooms[room_key]
        print(f'{room_key} is empty, deleting.')
    print(rooms)


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
