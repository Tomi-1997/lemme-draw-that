# List with fixed length, overwriting the oldest element
# For remembering the current canvas state

class ConstantArray:
    def __init__(self, size=1024):
        self.size = size
        self.data = [-1 for _ in range(size)]
        self.index = 0

    def clear(self):
        for i in range(self.size):
            self.data[i] = -1

    def add(self, element):
        self.data[self.index] = element
        self.index = (self.index + 1) % self.size

    def append(self, element):
        self.add(element)

    def at(self, i):
        return self.data[i]
