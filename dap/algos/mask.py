import numpy as np


def calc_mask_pixels(data, pixel_mask_pf):
    if pixel_mask_pf is None:
        return

    data[~pixel_mask_pf] = np.nan



