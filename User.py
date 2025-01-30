class User:
    def __init__(self, user_ip, nickname):
        self.ip = user_ip
        self.nick = nickname

    def __repr__(self):
        return f'({self.ip}, {self.nick})'
