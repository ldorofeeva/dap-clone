import json


def json_load(filename, *args, **kwargs):
    with open(filename, "r") as f:
        return json.load(f, *args, **kwargs)


def read_bit(bits, n):
    """
    read the n-th bit from bits as boolean
    """
    return bool((bits >> n) & 1)



