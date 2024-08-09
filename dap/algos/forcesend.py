import numpy as np


def calc_force_send(results, data, pixel_mask_pf, image, data_summed, n_aggregated_images):
    force_send_visualisation = False

    if data.dtype == np.uint16:
        return data, force_send_visualisation, data_summed, n_aggregated_images

    apply_aggregation = results.get("apply_aggregation", False)
    apply_threshold   = results.get("apply_threshold", False)

    if not apply_aggregation:
        data_summed = None
        n_aggregated_images = 1

    if not apply_aggregation and not apply_threshold:
        data = image
        return data, force_send_visualisation, data_summed, n_aggregated_images

    calc_apply_threshold(results, data) # changes data in place

    data, force_send_visualisation, data_summed, n_aggregated_images = calc_apply_aggregation(results, data, data_summed, n_aggregated_images)

    calc_apply_pixel_mask(data, pixel_mask_pf) # changes data in place

    return data, force_send_visualisation, data_summed, n_aggregated_images



def calc_apply_threshold(results, data):
    apply_threshold = results.get("apply_threshold", False)
    if apply_threshold and all(k in results for k in ("threshold_min", "threshold_max")):
        threshold_min = float(results["threshold_min"])
        threshold_max = float(results["threshold_max"])
        data[data < threshold_min] = 0.0
        if threshold_max > threshold_min:
            data[data > threshold_max] = 0.0


def calc_apply_aggregation(results, data, data_summed, n_aggregated_images):
    force_send_visualisation = False

    apply_aggregation = results.get("apply_aggregation", False)
    if apply_aggregation and "aggregation_max" in results:
        if data_summed is not None:
            data += data_summed
            n_aggregated_images += 1
        data_summed = data.copy()
        results["aggregated_images"] = n_aggregated_images
        results["worker"] = 1 #TODO: keep this for backwards compatibility?

        if n_aggregated_images >= results["aggregation_max"]:
            force_send_visualisation = True
            data_summed = None
            n_aggregated_images = 1

    return data, force_send_visualisation, data_summed, n_aggregated_images


def calc_apply_pixel_mask(data, pixel_mask_pf):
    if pixel_mask_pf is not None:
        data[~pixel_mask_pf] = np.nan



