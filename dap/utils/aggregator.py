
class Aggregator:

    def __init__(self):
        self.reset()

    def reset(self):
        self.data = None
        self.counter = 0
        self.nmax = None

    def add(self, item):
        if self.data is None:
            self.data = item.copy()
            self.counter = 1
        else:
            self.data += item
            self.counter += 1
        return self

    __iadd__ = add

    def is_ready(self):
        if self.nmax is None:
            return False
        return (self.counter >= self.nmax)

    def __repr__(self):
        return f"{self.data!r} # ({self.counter} / {self.nmax})"



