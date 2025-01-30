class Room:
    def __init__(self, room_code):
        self.users = []
        self.code = room_code

    def is_empty(self):
        return len(self.users) == 0

    def __repr__(self):
        return f'Users : {self.users}'

    def add(self, user):
        if self.ip_present(user.ip):
            return
        self.users.append(user)

    def rm(self, element):
        index = self.find_ip(element)
        if index != -1:
            del self.users[index]

    def find_ip(self, ip):
        for i, user in enumerate(self.users):
            if ip == user.ip:
                return i
        return -1

    def find_nick(self, ip):
        for i, user in enumerate(self.users):
            if ip == user.ip:
                return user.nick
        return -1

    def ip_present(self, ip):
        return self.find_ip(ip) != -1

    def ip_not_present(self, element):
        return not self.ip_present(element)

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
