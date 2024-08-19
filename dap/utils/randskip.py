from random import randint


def randskip(skip_rate):
    return (randint(1, skip_rate) != 1)


# from randint docs:
#  randint(a, b)
#  Return random integer in range [a, b], including both end points.

# thus:
#  randskip(1)   -> False 100% of times (never skip)
#  randskip(10)  -> False  10% of times (skip 90%)
#  randskip(100) -> False   1% of times (skip 99%)

#TODO: does this actually make sense?



