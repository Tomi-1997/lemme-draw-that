import random
import string


def random_str(k):
    # K random digits
    digits = ''.join(random.choices(string.digits, k=k))

    # Shuffle
    random_string_list = list(digits)
    random.shuffle(random_string_list)

    # To string
    final_string = ''.join(random_string_list)
    return final_string
