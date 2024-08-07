import json
import os
from time import sleep


class BufferedJSON:

    def __init__(self, fname):
        self.fname = fname
        self.last_time = self.get_time()
        self.last_data = self.get_data()


    def load(self):
        current_time = self.get_time()
        time_delta = current_time - self.last_time
        if time_delta <= 2: #TODO: is that a good time?
            return self.last_data

        sleep(0.5) #TODO: why?
        current_data = self.get_data()
        self.last_time = current_time
        self.last_data = current_data
        return current_data


    def get_time(self):
        if not self.exists():
            return -1
        return os.path.getmtime(self.fname)

    def get_data(self, *args, **kwargs):
        if not self.exists():
            return {}
        return json_load(self.fname, *args, **kwargs)

    def exists(self):
        if not self.fname:
            return False
        return os.path.exists(self.fname)



def json_load(filename, *args, **kwargs):
    with open(filename, "r") as f:
        return json.load(f, *args, **kwargs)



