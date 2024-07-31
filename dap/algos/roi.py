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
        roi_intensities.append(roi_sum)

        if threshold_value_choice == "NaN":
            roi_area = (iy2 - iy1) * (ix2 - ix1)
            roi_sum_norm = roi_sum / roi_area
        else:
            roi_sum_norm = np.nanmean(data_roi)

        roi_intensities_normalised.append(roi_sum_norm)

        roi_intensity_x = [ix1, ix2]
        roi_intensity_proj_x = np.nansum(data_roi, axis=0).tolist()

        roi_intensities_x.append(roi_intensity_x)
        roi_intensities_proj_x.append(roi_intensity_proj_x)

    results["roi_intensities"] = [float(r) for r in roi_intensities]
    results["roi_intensities_normalised"] = [float(r) for r in roi_intensities_normalised]

    results["roi_intensities_x"] = roi_intensities_x
    results["roi_intensities_proj_x"] = roi_intensities_proj_x



