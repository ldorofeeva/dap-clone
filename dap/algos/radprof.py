import numpy as np


def calc_radial_integration(results, data, keep_pixels, pixel_mask_pf, center_radial_integration, r_radial_integration):
    if keep_pixels is None and pixel_mask_pf is not None:
        keep_pixels = (pixel_mask_pf == 1) #TODO: boolean mask

    if center_radial_integration is None:
        center_radial_integration = [
            results["beam_center_x"],
            results["beam_center_y"]
        ]
        r_radial_integration = None

    if r_radial_integration is None:
        r_radial_integration, nr_radial_integration = prepare_radial_profile(data, center_radial_integration, keep_pixels)
        r_min = int(np.min(r_radial_integration))
        r_max = int(np.max(r_radial_integration)) + 1

    apply_threshold = results.get("apply_threshold", False)

    #TODO: this is duplicated in calc_apply_threshold
    if apply_threshold and all(k in results for k in ("threshold_min", "threshold_max")):
        threshold_min = float(results["threshold_min"])
        threshold_max = float(results["threshold_max"])
        data = np.copy(data) # do the following in-place changes on a copy
        data[data < threshold_min] = np.nan
        #TODO: skipping max is a guess, but not obvious/symmetric -- better to ensure the order min < max by switching them if needed
        if threshold_max > threshold_min:
            data[data > threshold_max] = np.nan

    rp = radial_profile(data, r_radial_integration, nr_radial_integration, keep_pixels)

    silent_region_min = results.get("radial_integration_silent_min", None)
    silent_region_max = results.get("radial_integration_silent_max", None)

    if (
        silent_region_min is not None and
        silent_region_max is not None and
        #TODO: skipping entirely is a guess, but not obvious -- better to ensure the order min < max by switching them if needed
        silent_region_max > silent_region_min and
        silent_region_min > r_min and
        silent_region_max < r_max
    ):
        silent_region = rp[silent_region_min:silent_region_max]
        integral_silent_region = np.sum(silent_region)
        rp = rp / integral_silent_region
        results["radint_normalised"] = [silent_region_min, silent_region_max]

    results["radint_I"] = rp[r_min:].tolist()
    results["radint_q"] = [r_min, r_max]

    return keep_pixels, center_radial_integration, r_radial_integration



def radial_profile(data, r, nr, keep_pixels=None):
    if keep_pixels is not None:
        data = data[keep_pixels]
    data = data.ravel()
    tbin = np.bincount(r, data)
    rp = tbin / nr
    return rp

def prepare_radial_profile(data, center, keep_pixels=None):
    y, x = np.indices(data.shape)
    x0, y0 = center
    rad = np.sqrt((x - x0)**2 + (y - y0)**2)
    if keep_pixels is not None:
        rad = rad[keep_pixels]
    rad = rad.astype(int).ravel()
    nr = np.bincount(rad)
    return rad, nr



