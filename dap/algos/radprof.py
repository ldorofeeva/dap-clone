import numpy as np


def calc_radial_integration(results, data, pixel_mask_pf, center, rad):
    if center is None:
        center = [
            results["beam_center_x"],
            results["beam_center_y"]
        ]
        rad = None

    if rad is None:
        rad, norm = prepare_radial_profile(data, center, keep_pixels=pixel_mask_pf)
        r_min = int(np.min(rad))
        r_max = int(np.max(rad)) + 1

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

    rp = radial_profile(data, rad, norm, keep_pixels=pixel_mask_pf)

    silent_min = results.get("radial_integration_silent_min", None)
    silent_max = results.get("radial_integration_silent_max", None)

    if (
        silent_min is not None and
        silent_max is not None and
        #TODO: skipping entirely is a guess, but not obvious -- better to ensure the order min < max by switching them if needed
        silent_max > silent_min and
        silent_min > r_min and
        silent_max < r_max
    ):
        silent_region = rp[silent_min:silent_max]
        integral_silent_region = np.sum(silent_region)
        rp = rp / integral_silent_region
        results["radint_normalised"] = [silent_min, silent_max]

    results["radint_I"] = rp[r_min:].tolist()
    results["radint_q"] = [r_min, r_max]

    return center, rad


def prepare_radial_profile(data, center, keep_pixels=None):
    y, x = np.indices(data.shape)
    x0, y0 = center
    rad = np.sqrt((x - x0)**2 + (y - y0)**2)
    if keep_pixels is not None:
        rad = rad[keep_pixels]
    rad = rad.astype(int).ravel()
    norm = np.bincount(rad)
    return rad, norm


def radial_profile(data, rad, norm, keep_pixels=None):
    if keep_pixels is not None:
        data = data[keep_pixels]
    data = data.ravel()
    tbin = np.bincount(rad, data)
    rp = tbin / norm
    return rp



