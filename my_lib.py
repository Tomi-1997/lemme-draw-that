import random
import string

def random_str(letters, numbers):
    # 4 random letters (lowercase)
    letters = ''.join(random.choices(string.ascii_lowercase, k=letters))

    # 2 random digits
    digits = ''.join(random.choices(string.digits, k=numbers))

    # Combine
    random_string = letters + digits

    # Shuffle
    random_string_list = list(random_string)
    random.shuffle(random_string_list)

    # To string
    final_string = ''.join(random_string_list)
    return final_string