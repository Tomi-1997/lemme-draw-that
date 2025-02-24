class User:
    def __init__(self, user_id, nickname):
        self.id = user_id
        self.nick = nickname

    def __repr__(self):
        return f'({self.id}, {self.nick})'
