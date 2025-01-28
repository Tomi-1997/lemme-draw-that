class Room:
    def __init__(self, user_ip, room_code):
        self.users = [user_ip]
        self.code = room_code

    def is_empty(self):
        return len(self.users) == 0

    def __repr__(self):
        return f'Room : {self.code} | Users : {self.users}'

    def add(self, element):
        if element in self.users:
            return
        self.users.append(element)

    def rm(self, element):
        self.users.remove(element)

    def present(self, element):
        return element in self.users
    #
    # def at(self, i):
    #     return self.data[i]
