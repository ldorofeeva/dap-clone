import numpy as np


def calc_roi(results, data, roi_x1, roi_x2, roi_y1, roi_y2, pixel_mask_pf, threshold_value_choice):
    if pixel_mask_pf is None:
        return

    roi_results = [0] * len(roi_x1)
    roi_results_normalised = [0] * len(roi_x1)

    results["roi_intensities_x"] = []
    results["roi_intensities_proj_x"] = []

    for iRoi in range(len(roi_x1)):
        data_roi = np.copy(data[roi_y1[iRoi]:roi_y2[iRoi], roi_x1[iRoi]:roi_x2[iRoi]])

        roi_results[iRoi] = np.nansum(data_roi)
        if threshold_value_choice == "NaN":
            roi_results_normalised[iRoi] = roi_results[iRoi] / ((roi_y2[iRoi] - roi_y1[iRoi]) * (roi_x2[iRoi] - roi_x1[iRoi]))
        else:
            roi_results_normalised[iRoi] = np.nanmean(data_roi)

        results["roi_intensities_x"].append([roi_x1[iRoi], roi_x2[iRoi]])
        results["roi_intensities_proj_x"].append(np.nansum(data_roi, axis=0).tolist())

    results["roi_intensities"] = [float(r) for r in roi_results]
    results["roi_intensities_normalised"] = [float(r) for r in roi_results_normalised]



