import random
import string


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
        nickname = random.choice(adj) + ' ' + random.choice(ani)
        if room.not_present(nickname):
            return nickname
    print(nickname)
