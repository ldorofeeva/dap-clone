import argparse
from random import randint

import numpy as np

from algos import calc_apply_threshold, calc_mask_pixels, calc_peakfinder_analysis, calc_radial_integration, calc_roi, calc_spi_analysis, JFData
from utils import BufferedJSON, read_bit
from zmqsocks import ZMQSockets


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--backend_address", default=None)
    parser.add_argument("--accumulator_host", default="localhost")
    parser.add_argument("--accumulator_port", default=13002, type=int)
    parser.add_argument("--visualisation_host", default="localhost")
    parser.add_argument("--visualisation_port", default=13002, type=int)
    parser.add_argument("--peakfinder_parameters", default=None, help="json file with peakfinder parameters")
    parser.add_argument("--skip_frames_rate", default=1, type=int, help="send to streamvis each of skip_frames_rate frames")

    clargs = parser.parse_args()

    if not clargs.backend_address:
        raise SystemExit("please provide a backend address")

    work(
        clargs.backend_address,
        clargs.accumulator_host,
        clargs.accumulator_port,
        clargs.visualisation_host,
        clargs.visualisation_port,
        clargs.peakfinder_parameters,
        clargs.skip_frames_rate
    )



def work(backend_address, accumulator_host, accumulator_port, visualisation_host, visualisation_port, fn_peakfinder_parameters, skip_frames_rate):
    bj_peakfinder_parameters = BufferedJSON(fn_peakfinder_parameters)

    jfdata = JFData()

    zmq_socks = ZMQSockets(backend_address, accumulator_host, accumulator_port, visualisation_host, visualisation_port)


    pulse_id = 0

    n_aggregated_images = 1
    data_summed = None


    while True:
        try:
            peakfinder_parameters = bj_peakfinder_parameters.load()
        except Exception as e:
            print(f"({pulse_id}) cannot read peakfinder parameters file: {e}", flush=True) #TODO: logging?


        if not zmq_socks.has_data():
            continue

        image, metadata = zmq_socks.get_data()

        if metadata["shape"] == [2, 2]: # this is used as marker for empty images
            continue

        pulse_id = metadata.get("pulse_id", 0)

        results = metadata.copy()
        results.update(peakfinder_parameters)

        results["number_of_spots"] = 0
        results["is_hit_frame"] = False


        daq_rec = results.get("daq_rec", 0)
        event_laser    = read_bit(daq_rec, 16)
        event_darkshot = read_bit(daq_rec, 17)
#        event_fel      = read_bit(daq_rec, 18)
        event_ppicker  = read_bit(daq_rec, 19)

        results["laser_on"] = event_laser and not event_darkshot

        # if requested, filter on ppicker events by skipping other events
        select_only_ppicker_events = results.get("select_only_ppicker_events", False)
        if select_only_ppicker_events and not event_ppicker:
            continue


        pedestal_name = metadata.get("pedestal_name", None)

        jfdata.ensure_current_pixel_mask(pedestal_name)

        double_pixels = results.get("double_pixels", "mask")

        data = jfdata.process(image, metadata, double_pixels)

        if not data:
            continue

        pixel_mask_pf = jfdata.get_pixel_mask(results, double_pixels)

        if pixel_mask_pf is not None:
            saturated_pixels_y, saturated_pixels_x = jfdata.get_saturated_pixels(image, double_pixels)
            results["saturated_pixels"] = len(saturated_pixels_x)
            results["saturated_pixels_x"] = saturated_pixels_x.tolist()
            results["saturated_pixels_y"] = saturated_pixels_y.tolist()


        calc_radial_integration(results, data, pixel_mask_pf)

        pfdata = data.copy() #TODO: is this copy needed?

        calc_mask_pixels(pfdata, pixel_mask_pf) # changes pfdata in place
        calc_apply_threshold(results, pfdata) # changes pfdata in place
        calc_roi(results, pfdata, pixel_mask_pf)
        calc_spi_analysis(results)
        calc_peakfinder_analysis(results, pfdata, pixel_mask_pf)

# ???
        forceSendVisualisation = False
        if data.dtype != np.uint16:
            apply_threshold = results.get("apply_threshold", False)
            apply_aggregation = results.get("apply_aggregation", False)
            if not apply_aggregation:
                data_summed = None
                n_aggregated_images = 1
            if apply_threshold or apply_aggregation:
                if apply_threshold and all(k in results for k in ("threshold_min", "threshold_max")):
                    threshold_min = float(results["threshold_min"])
                    threshold_max = float(results["threshold_max"])
                    data[data < threshold_min] = 0.0
                    if threshold_max > threshold_min:
                        data[data > threshold_max] = 0.0
                if apply_aggregation and "aggregation_max" in results:
                    if data_summed is not None:
                        data += data_summed
                        n_aggregated_images += 1
                    data_summed = data.copy()
                    data_summed[data == -np.nan] = -np.nan #TODO: this does nothing
                    results["aggregated_images"] = n_aggregated_images
                    results["worker"] = 1 #TODO: keep this for backwards compatibility?
                    if n_aggregated_images >= results["aggregation_max"]:
                        forceSendVisualisation = True
                        data_summed = None
                        n_aggregated_images = 1
                if pixel_mask_pf is not None:
                    data[~pixel_mask_pf] = np.nan

            else:
                data = image

        results["type"]  = str(data.dtype)
        results["shape"] = data.shape


        zmq_socks.send_accumulator(results)


        send_empty_cond1 = (apply_aggregation and "aggregation_max" in results and not forceSendVisualisation)
        send_empty_cond2 = (not results["is_good_frame"] or not (results["is_hit_frame"] or randint(1, skip_frames_rate) == 1))

        if send_empty_cond1 or send_empty_cond2:
            data = np.empty((2, 2), dtype=np.uint16)
            results["type"]  = str(data.dtype)
            results["shape"] = data.shape

        zmq_socks.send_visualisation(results, data)





if __name__ == "__main__":
    main()



