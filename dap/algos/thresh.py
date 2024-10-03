import numpy as np


#TODO: this is duplicated in calc_radial_integration and calc_force_send
def calc_apply_threshold(results, data):
    apply_threshold = results.get("apply_threshold", False)
    if not apply_threshold:
        return

    for k in ("threshold_min", "threshold_max"):
        if k not in results:
            return

    threshold_value_choice = results.get("threshold_value", "NaN")
    threshold_value = 0 if threshold_value_choice == "0" else np.nan #TODO

    threshold_min = float(results["threshold_min"])
    threshold_max = float(results["threshold_max"])

    threshold(data, threshold_min, threshold_max, threshold_value)



def threshold(data, vmin, vmax, replacement):
    """
    threshold data in place by replacing values < vmin and values > vmax with replacement
    """
    data[data < vmin] = replacement
    #TODO: skipping max is a guess, but not obvious/symmetric -- better to ensure the order min < max by switching them if needed
    if vmax > vmin:
        data[data > vmax] = replacement



