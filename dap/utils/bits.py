
def read_bit(bits, n):
    """
    read the n-th bit from bits as boolean
    """
    return bool((bits >> n) & 1)



