import argparse

import numpy as np

from algos import calc_apply_aggregation, calc_apply_threshold, calc_mask_pixels, calc_peakfinder_analysis, calc_radial_integration, calc_roi, calc_spi_analysis, JFData
from utils import Aggregator, BufferedJSON, randskip, read_bit
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

    aggregator = Aggregator()


    while True:
        if not zmq_socks.has_data():
            continue

        raw_image, metadata = zmq_socks.get_data()

        if metadata["shape"] == [2, 2]: # this is used as marker for empty images
            continue


        pulse_id = metadata.get("pulse_id", 0)

        try:
            peakfinder_parameters = bj_peakfinder_parameters.load()
        except Exception as e:
            print(f"({pulse_id}) cannot read peakfinder parameters file: {e}", flush=True) #TODO: logging?


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

        image = jfdata.process(raw_image, metadata, double_pixels)

        if image is None:
            continue

        pixel_mask_pf = jfdata.get_pixel_mask(results, double_pixels)

        if pixel_mask_pf is not None:
            saturated_pixels_y, saturated_pixels_x = jfdata.get_saturated_pixels(raw_image, double_pixels)
            results["saturated_pixels"] = len(saturated_pixels_x)
            results["saturated_pixels_x"] = saturated_pixels_x.tolist()
            results["saturated_pixels_y"] = saturated_pixels_y.tolist()


        calc_radial_integration(results, image, pixel_mask_pf)

        pfimage = image.copy() #TODO: is this copy needed?

        calc_mask_pixels(pfimage, pixel_mask_pf) # changes pfimage in place
        calc_apply_threshold(results, pfimage) # changes pfimage in place
        calc_roi(results, pfimage, pixel_mask_pf)
        calc_spi_analysis(results)
        calc_peakfinder_analysis(results, pfimage, pixel_mask_pf)

# ???
        image, aggregation_is_ready = calc_apply_aggregation(results, image, pixel_mask_pf, aggregator)

        results["type"]  = str(image.dtype)
        results["shape"] = image.shape


        zmq_socks.send_accumulator(results)


        apply_aggregation = results.get("apply_aggregation", False)
        aggregation_is_enabled = (apply_aggregation and "aggregation_max" in results)
        aggregation_is_enabled_but_not_ready = (aggregation_is_enabled and not aggregation_is_ready)

        is_bad_frame = (not results["is_good_frame"])

        # hits are sent at full rate, but no-hits are sent at reduced frequency
        is_no_hit_frame = (not results["is_hit_frame"])
        random_skip = randskip(skip_frames_rate)
        is_no_hit_frame_and_skipped = (is_no_hit_frame and random_skip)

        if aggregation_is_enabled_but_not_ready or is_bad_frame or is_no_hit_frame_and_skipped:
            image = np.empty((2, 2), dtype=np.uint16)
            results["type"]  = str(image.dtype)
            results["shape"] = image.shape

        zmq_socks.send_visualisation(results, image)





if __name__ == "__main__":
    main()



