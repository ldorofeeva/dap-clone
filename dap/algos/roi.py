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

    roi_results = [0] * len(roi_x1)
    roi_results_normalised = [0] * len(roi_x1)

    results["roi_intensities_x"] = []
    results["roi_intensities_proj_x"] = []

    for iRoi in range(len(roi_x1)):
        data_roi = data[roi_y1[iRoi]:roi_y2[iRoi], roi_x1[iRoi]:roi_x2[iRoi]]

        roi_results[iRoi] = np.nansum(data_roi)
        if threshold_value_choice == "NaN":
            roi_results_normalised[iRoi] = roi_results[iRoi] / ((roi_y2[iRoi] - roi_y1[iRoi]) * (roi_x2[iRoi] - roi_x1[iRoi]))
        else:
            roi_results_normalised[iRoi] = np.nanmean(data_roi)

        results["roi_intensities_x"].append([roi_x1[iRoi], roi_x2[iRoi]])
        results["roi_intensities_proj_x"].append(np.nansum(data_roi, axis=0).tolist())

    results["roi_intensities"] = [float(r) for r in roi_results]
    results["roi_intensities_normalised"] = [float(r) for r in roi_results_normalised]



