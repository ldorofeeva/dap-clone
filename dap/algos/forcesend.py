import numpy as np

from .mask import calc_mask_pixels
from .thresh import threshold


def calc_force_send(results, data, pixel_mask_pf, image, aggregator):
    force_send_visualisation = False

    if data.dtype == np.uint16:
        return data, force_send_visualisation

    apply_aggregation = results.get("apply_aggregation", False)
    apply_threshold   = results.get("apply_threshold", False)

    if not apply_aggregation:
        aggregator.reset()

    if not apply_aggregation and not apply_threshold:
        data = image
        return data, force_send_visualisation

    calc_apply_threshold(results, data) # changes data in place

    data, force_send_visualisation = calc_apply_aggregation(results, data, aggregator)

    calc_mask_pixels(data, pixel_mask_pf) # changes data in place

    return data, force_send_visualisation



#TODO: this is duplicated in calc_apply_threshold and calc_radial_integration
def calc_apply_threshold(results, data):
    apply_threshold = results.get("apply_threshold", False)
    if not apply_threshold:
        return

    for k in ("threshold_min", "threshold_max"):
        if k not in results:
            return

    threshold_min = float(results["threshold_min"])
    threshold_max = float(results["threshold_max"])

    threshold(data, threshold_min, threshold_max, 0)



def calc_apply_aggregation(results, data, aggregator):
    force_send_visualisation = False

    apply_aggregation = results.get("apply_aggregation", False)
    if not apply_aggregation:
        return data, force_send_visualisation

    if "aggregation_max" not in results:
        return data, force_send_visualisation

    aggregator += data

    data = aggregator.data
    n_aggregated_images = aggregator.counter

    results["aggregated_images"] = n_aggregated_images
    results["worker"] = 1 #TODO: keep this for backwards compatibility?

    if n_aggregated_images >= results["aggregation_max"]:
        force_send_visualisation = True
        aggregator.reset()

    return data, force_send_visualisation



