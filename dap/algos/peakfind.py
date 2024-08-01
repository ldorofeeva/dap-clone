from copy import copy

import numpy as np

from peakfinder8_extension import peakfinder_8


def calc_peakfinder_analysis(results, data, pixel_mask_pf):
    if pixel_mask_pf is None:
        return

    for k in ("beam_center_x", "beam_center_y", "hitfinder_min_snr", "hitfinder_min_pix_count", "hitfinder_adc_thresh"):
        if k not in results:
            return

    # to coordinates where position of first pixel/point is 0.5, 0.5
    x_beam = results["beam_center_x"] - 0.5
    y_beam = results["beam_center_y"] - 0.5

    hitfinder_min_snr = results["hitfinder_min_snr"]
    hitfinder_min_pix_count = int(results["hitfinder_min_pix_count"])
    hitfinder_adc_thresh = results["hitfinder_adc_thresh"]

    asic_ny, asic_nx = data.shape
    nasics_y, nasics_x = 1, 1
    hitfinder_max_pix_count = 100
    max_num_peaks = 10000

    # usually don't need to change this value, rather robust
    hitfinder_local_bg_radius = 20.

    y, x = np.indices(data.shape)
    pix_r = np.sqrt((x - x_beam)**2 + (y - y_beam)**2)

    peak_list_x, peak_list_y, peak_list_value = peakfinder_8(
        max_num_peaks,
        data.astype(np.float32),
        pixel_mask_pf.astype(np.int8),
        pix_r.astype(np.float32),
        asic_nx, asic_ny,
        nasics_x, nasics_y,
        hitfinder_adc_thresh,
        hitfinder_min_snr,
        hitfinder_min_pix_count,
        hitfinder_max_pix_count,
        hitfinder_local_bg_radius
    )

    number_of_spots = len(peak_list_x)
    results["number_of_spots"] = number_of_spots

    # to coordinates where position of first pixel/point is 1, 1
    results["spot_x"] = [x + 0.5 for x in peak_list_x]
    results["spot_y"] = [y + 0.5 for y in peak_list_y]
    results["spot_intensity"] = copy(peak_list_value) #TODO: why is this copy needed?

    npeaks_threshold_hit = results.get("npeaks_threshold_hit", 15)

    if number_of_spots >= npeaks_threshold_hit:
        results["is_hit_frame"] = True



