import numpy as np


def calc_roi(results, data, pixel_mask_pf, threshold_value_choice):
    if pixel_mask_pf is None:
        return

    for k in ("roi_x1", "roi_x2", "roi_y1", "roi_y2"):
        if k not in results:
            return

    roi_x1 = results["roi_x1"]
    roi_x2 = results["roi_x2"]
    roi_y1 = results["roi_y1"]
    roi_y2 = results["roi_y2"]

    if len(roi_x1) == 0:
        return

    if not (len(roi_x1) == len(roi_x2) == len(roi_y1) == len(roi_y2)):
        return

    roi_intensities = []
    roi_intensities_normalised = []
    roi_intensities_x = []
    roi_intensities_proj_x = []

    for ix1, ix2, iy1, iy2 in zip(roi_x1, roi_x2, roi_y1, roi_y2):
        data_roi = data[iy1:iy2, ix1:ix2]

        roi_sum = np.nansum(data_roi)

        if threshold_value_choice == "NaN":
            roi_area = (ix2 - ix1) * (iy2 - iy1)
            roi_sum_norm = roi_sum / roi_area
        else:
            roi_sum_norm = np.nanmean(data_roi)

        roi_indices_x = [ix1, ix2]
        roi_proj_x = np.nansum(data_roi, axis=0).tolist()

        roi_intensities.append(roi_sum)
        roi_intensities_normalised.append(roi_sum_norm)
        roi_intensities_x.append(roi_indices_x)
        roi_intensities_proj_x.append(roi_proj_x)

    results["roi_intensities"] = roi_intensities
    results["roi_intensities_normalised"] = roi_intensities_normalised
    results["roi_intensities_x"] = roi_intensities_x
    results["roi_intensities_proj_x"] = roi_intensities_proj_x



