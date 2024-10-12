from .mask import calc_mask_pixels
from .thresh import threshold


def calc_apply_aggregation(results, data, pixel_mask_pf, aggregator):
    # last round was ready, restart
    if aggregator.is_ready():
        aggregator.reset()

    calc_apply_threshold(results, data) # changes data in place
    data = calc_aggregate(results, data, aggregator)
    calc_mask_pixels(data, pixel_mask_pf) # changes data in place

    aggregator.nmax = results.get("aggregation_max")
    aggregation_is_ready = aggregator.is_ready()

    return data, aggregation_is_ready



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



def calc_aggregate(results, data, aggregator):
    apply_aggregation = results.get("apply_aggregation", False)
    if not apply_aggregation:
        aggregator.reset()
        return data

    if "aggregation_max" not in results:
        aggregator.reset()
        return data

    aggregator += data

    data = aggregator.data
    n_aggregated_images = aggregator.counter

    results["aggregated_images"] = n_aggregated_images
    results["worker"] = 1 #TODO: keep this for backwards compatibility?

    return data



