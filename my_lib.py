import random
import string
import re


def random_str_(k):
    # K random digits
    digits = ''.join(random.choices(string.digits, k=k))

    # Shuffle
    random_string_list = list(digits)
    random.shuffle(random_string_list)

    # To string
    final_string = ''.join(random_string_list)
    return final_string


def random_str(k, rooms):
    max_attempts = 100
    for i in range(max_attempts):
        ans = random_str_(k)
        if ans not in rooms.keys():
            return ans
    return -1


def get_nickname(room):
    import json
    with open('nickname.json', 'r') as f:
        data = json.load(f)
    adj = data['adjectives']
    ani = data['animals']

    max_attempts = 10
    nickname = 'Unknown Animal'
    for _ in range(max_attempts):
        adj = random.choice(adj)
        ani = random.choice(ani)
        adj = adj.capitalize()
        ani = ani.capitalize()
        nickname = adj + ' ' + ani
        if room.id_not_present(nickname):
            return nickname
    return nickname


def valid_color(cl):
    # Starts with #
    # Has the same 3 lettered sequence, once or twice
    pattern = r"^#([0-9A-Fa-f]{3}){1,2}$"
    match = re.match(pattern, cl)
    return bool(match)


def invalid_join(d):
    # Expected example:
    # d = {'code' : '314159'}
    if not isinstance(d, dict):
        return True

    if 'code' not in d:
        return True

    code = d['code']
    if not isinstance(code, str):
        return True

    if not re.match(r"^\d{6}", code):
        return True

    return False


def invalid_draw(d):
    # Expected example:
    #  { normX: 0.5, ...,
    #    userColor: "#dcdcdc"
    #    userSize: 1
    #    erasing: False }
    if not isinstance(d, dict):
        return True

    norms = ['normX', 'normLX', 'normY', 'normLY']
    keys = norms + ['userColor', 'userSize', 'erasing']
    key_type = [float, float, float, float, str, int, bool]

    if len(d) != len(keys):
        return True

    for key, kt in zip(keys, key_type):

        if key not in d:
            return True

        val = d[key]
        if not isinstance(val, kt):
            return True

        if key in norms:
            if 0 > val > 1:
                return True

        if key == 'userColor':
            if not valid_color(val):
                return True

        if key == 'userSize':
            if val < 0:  # (?) check for size too big?
                return True

    return False


def invalid_guess(d):
    # Expected example:
    # d = {'len' : 4}
    if not isinstance(d, dict):
        return True
    if len(d) != 1:
        return True
    if 'len' not in d:
        return True
    dl = d['len']
    if not isinstance(dl, int):
        return True
    if 1 > dl > 10:
        return True
    return False
