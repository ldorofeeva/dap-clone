import numpy as np


def radial_profile(data, r, nr, keep_pixels=None):
    if keep_pixels is not None:
        tbin = np.bincount(r, data[keep_pixels].ravel())
    else:
        tbin = np.bincount(r, data.ravel())
    radialprofile = tbin / nr
    return radialprofile

def prepare_radial_profile(data, center, keep_pixels=None):
    y, x = np.indices((data.shape))
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    if keep_pixels is not None:
        r = r[keep_pixels].astype(int).ravel()
    else:
        r = r.astype(np.int).ravel()
    nr = np.bincount(r)
    return r, nr



