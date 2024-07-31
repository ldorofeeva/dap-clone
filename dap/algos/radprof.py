import numpy as np


def calc_radial_integration(results, data, keep_pixels, pixel_mask_pf, center_radial_integration, r_radial_integration):
    data = np.copy(data)

    if keep_pixels is None and pixel_mask_pf is not None:
        keep_pixels = (pixel_mask_pf != 0)
    if center_radial_integration is None:
        center_radial_integration = [results["beam_center_x"], results["beam_center_y"]]
        r_radial_integration = None
    if r_radial_integration is None:
        r_radial_integration, nr_radial_integration = prepare_radial_profile(data, center_radial_integration, keep_pixels)
        r_min_max = [int(np.min(r_radial_integration)), int(np.max(r_radial_integration)) + 1]


    apply_threshold = results.get("apply_threshold", False)

    if apply_threshold and all(k in results for k in ("threshold_min", "threshold_max")):
        threshold_min = float(results["threshold_min"])
        threshold_max = float(results["threshold_max"])
        data[data < threshold_min] = np.nan
        if threshold_max > threshold_min:
            data[data > threshold_max] = np.nan

    rp = radial_profile(data, r_radial_integration, nr_radial_integration, keep_pixels)

    silent_region_min = results.get("radial_integration_silent_min", None)
    silent_region_max = results.get("radial_integration_silent_max", None)

    if (
        silent_region_min is not None and
        silent_region_max is not None and
        silent_region_max > silent_region_min and
        silent_region_min > r_min_max[0] and
        silent_region_max < r_min_max[1]
    ):

        integral_silent_region = np.sum(rp[silent_region_min:silent_region_max])
        rp = rp / integral_silent_region
        results["radint_normalised"] = [silent_region_min, silent_region_max]

    results["radint_I"] = list(rp[r_min_max[0]:])
    results["radint_q"] = r_min_max

    return keep_pixels, center_radial_integration, r_radial_integration



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



