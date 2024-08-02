import numpy as np


def calc_apply_threshold(results, data):
    apply_threshold = results.get("apply_threshold", False)
    threshold_value_choice = results.get("threshold_value", "NaN")
    threshold_value = 0 if threshold_value_choice == "0" else np.nan

    #TODO: this is duplicated in calc_radial_integration
    if apply_threshold and all(k in results for k in ("threshold_min", "threshold_max")):
        threshold_min = float(results["threshold_min"])
        threshold_max = float(results["threshold_max"])
        data[data < threshold_min] = threshold_value
        #TODO: skipping max is a guess, but not obvious/symmetric -- better to ensure the order min < max by switching them if needed
        if threshold_max > threshold_min:
            data[data > threshold_max] = threshold_value



