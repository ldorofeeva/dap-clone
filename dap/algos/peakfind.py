from copy import copy

import numpy as np

from peakfinder8_extension import peakfinder_8


def calc_peakfinder_analysis(results, pfdata, pixel_mask_pf):
    x_beam = results["beam_center_x"] - 0.5 # to coordinates where position of first pixel/point is 0.5, 0.5
    y_beam = results["beam_center_y"] - 0.5 # to coordinates where position of first pixel/point is 0.5, 0.5
    hitfinder_min_snr = results["hitfinder_min_snr"]
    hitfinder_min_pix_count = int(results["hitfinder_min_pix_count"])
    hitfinder_adc_thresh = results["hitfinder_adc_thresh"]

    asic_ny, asic_nx = pfdata.shape
    nasics_y, nasics_x = 1, 1
    hitfinder_max_pix_count = 100
    max_num_peaks = 10000

    # usually don't need to change this value, rather robust
    hitfinder_local_bg_radius= 20.

    # in case of further modification with the mask, make a new one, independent from real mask
    maskPr = np.copy(pixel_mask_pf)

    y, x = np.indices(pfdata.shape)
    pix_r = np.sqrt((x-x_beam)**2 + (y-y_beam)**2)

    peak_list_x, peak_list_y, peak_list_value = peakfinder_8(
        max_num_peaks,
        pfdata.astype(np.float32),
        maskPr.astype(np.int8),
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
    if number_of_spots != 0:
        results["spot_x"] = [-1.0] * number_of_spots
        results["spot_y"] = [-1.0] * number_of_spots
        results["spot_intensity"] = copy(peak_list_value)
        for i in range(number_of_spots):
            results["spot_x"][i] = peak_list_x[i] + 0.5
            results["spot_y"][i] = peak_list_y[i] + 0.5
    else:
        results["spot_x"] = []
        results["spot_y"] = []
        results["spot_intensity"] = []

    npeaks_threshold_hit = results.get("npeaks_threshold_hit", 15)

    if number_of_spots >= npeaks_threshold_hit:
        results["is_hit_frame"] = True



