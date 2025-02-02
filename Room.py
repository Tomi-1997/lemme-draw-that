from ConstantArray import ConstantArray

# A Room for a canvas app
# User list
# A 6 digit room code
# A constant array to hold latest strokes made by users


class Room:
    def __init__(self, room_code):
        self.users = []
        self.code = room_code
        self.board_state = ConstantArray()

    def is_empty(self):
        return len(self.users) == 0

    def __repr__(self):
        return f'Users : {self.users}'

    def add(self, user):
        if self.id_present(user.id):
            return
        self.users.append(user)

    def rm(self, element):
        index = self.find_id(element)
        if index != -1:
            del self.users[index]

    def find_id(self, uid):
        for i, user in enumerate(self.users):
            if uid == user.id:
                return i
        return -1

    def find_nick(self, uid):
        for i, user in enumerate(self.users):
            if uid == user.id:
                return user.nick
        return -1

    def id_present(self, uid):
        return self.find_id(uid) != -1

    def id_not_present(self, element):
        return not self.id_present(element)

    def len(self):
        return len(self.users)

    def user_nicks(self):
        ans = []
        for user in self.users:
            ans.append(user.nick)
        return ans
    #
    # def at(self, i):
    #     return self.data[i]

    def draw(self, elem):
        self.board_state.add(elem)

    def clear_board(self):
        self.board_state.clear()

    def get_board(self):
        return self.board_state.data
