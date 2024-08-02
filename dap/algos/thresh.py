import numpy as np


def calc_apply_threshold(results, pfdata):
    apply_threshold = results.get("apply_threshold", False)
    threshold_value_choice = results.get("threshold_value", "NaN")
    threshold_value = 0 if threshold_value_choice == "0" else np.nan
    if apply_threshold and all(k in results for k in ("threshold_min", "threshold_max")):
        threshold_min = float(results["threshold_min"])
        threshold_max = float(results["threshold_max"])
        pfdata[pfdata < threshold_min] = threshold_value
        if threshold_max > threshold_min:
            pfdata[pfdata > threshold_max] = threshold_value
    return threshold_value_choice



