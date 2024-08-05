import functools
#import hashlib
import numpy as np


def npmemo(func):
    """
    numpy array aware memoizer
    """
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        key = make_key(args)
        try:
            return cache[key]
        except KeyError:
            cache[key] = res = func(*args)
            return res

#    wrapper.cache = cache
    return wrapper


def make_key(args):
    return tuple(make_key_entry(i) for i in args)

def make_key_entry(x):
    if isinstance(x, np.ndarray):
        return np_array_hash(x)
    return x

def np_array_hash(arr):
#    return id(arr) # this has been used so far
    res = arr.tobytes()
#    res = hashlib.sha256(res).hexdigest() # if tobytes was too large, we could hash it
#    res = (arr.shape, res) # tobytes does not take shape into account
    return res





if __name__ == "__main__":
    @npmemo
    def expensive(arr, offset):
        print("recalc", arr, offset)
        return np.dot(arr, arr) + offset

    def test(arr, offset):
        print("first")
        res1 = expensive(arr, offset)
        print("second")
        res2 = expensive(arr, offset)
        print()
        assert np.array_equal(res1, res2)

    arrays = (
        [1, 2, 3],
        [1, 2, 3, 4],
        [1, 2, 3, 4]
    )

    offsets = (
        2,
        2,
        5
    )

    for a, o in zip(arrays, offsets):
        a = np.array(a)
        test(a, o)

#    print(expensive.cache)



