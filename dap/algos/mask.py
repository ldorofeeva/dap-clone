import numpy as np


def calc_mask_pixels(pfdata, pixel_mask_pf):
    if pixel_mask_pf is None:
        return

    pfdata[pixel_mask_pf != 1] = np.nan #TODO: boolean mask



