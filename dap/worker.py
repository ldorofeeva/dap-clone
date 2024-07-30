import argparse
import os
from copy import copy
from random import randint
from time import sleep

import jungfrau_utils as ju
import numpy as np

from algos import calc_radial_integration, calc_apply_additional_mask, calc_peakfinder_analysis, calc_spi_analysis, calc_roi
from zmqsocks import ZMQSockets
from utils import json_load, read_bit


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
    peakfinder_parameters = {}
    peakfinder_parameters_time = -1
    if fn_peakfinder_parameters is not None and os.path.exists(fn_peakfinder_parameters):
        peakfinder_parameters = json_load(fn_peakfinder_parameters)
        peakfinder_parameters_time = os.path.getmtime(fn_peakfinder_parameters)

    pulseid = 0

    ju_stream_adapter = ju.StreamAdapter()

    zmq_socks = ZMQSockets(backend_address, accumulator_host, accumulator_port, visualisation_host, visualisation_port)

# all the normal workers
    worker = 1

    keep_pixels = None
    r_radial_integration = None
    center_radial_integration = None

    results = {}

    pedestal_file_name_saved = None

    pixel_mask_corrected = None
    pixel_mask_pf = None

    n_aggregated_images = 1
    data_summed = None

    while True:

# check if peakfinder parameters changed and then re-read it
        try:
            if peakfinder_parameters_time > 0:
                new_time = os.path.getmtime(fn_peakfinder_parameters)
                time_delta = new_time - peakfinder_parameters_time
                if time_delta > 2.0:
                    old_peakfinder_parameters = peakfinder_parameters
                    sleep(0.5)
                    peakfinder_parameters = json_load(fn_peakfinder_parameters)
                    peakfinder_parameters_time = new_time
                    center_radial_integration = None
                    if worker ==  0:
                        print(f"({pulseid}) update peakfinder parameters {old_peakfinder_parameters}", flush=True)
                        print(f"                                     --> {peakfinder_parameters}", flush=True)
                        print(flush=True)
        except Exception as e:
            print(f"({pulseid}) problem ({e}) to read peakfinder parameters file, worker : {worker}", flush=True)

        if not zmq_socks.has_data():
            continue

        image, metadata = zmq_socks.get_data()

        results = copy(metadata)
        if results["shape"][0] == 2 and results["shape"][1] == 2:
            continue

        pulseid = results.get("pulse_id", 0)
        results.update(peakfinder_parameters)

        detector = results.get("detector_name", "")

        results["laser_on"] = False
        results["number_of_spots"] = 0
        results["is_hit_frame"] = False

        daq_rec = results.get("daq_rec", 0)
        event_laser    = read_bit(daq_rec, 16)
        event_darkshot = read_bit(daq_rec, 17)
#        event_fel      = read_bit(daq_rec, 18)
        event_ppicker  = read_bit(daq_rec, 19)

        if not event_darkshot:
            results["laser_on"] = event_laser

# Filter only ppicker events, if requested; skipping all other events
        select_only_ppicker_events = results.get("select_only_ppicker_events", False)
        if select_only_ppicker_events and not event_ppicker:
            continue

# special settings for p20270, only few shots were opened by pulse-picker
#        if detector in ["JF06T32V02"]:
#            if event_ppicker:
#                results["number_of_spots"] = 50
#                results["is_hit_frame"] = True

        double_pixels = results.get("double_pixels", "mask")

        pedestal_file_name = metadata.get("pedestal_name", None)
        if pedestal_file_name is not None and pedestal_file_name != pedestal_file_name_saved:
            pixel_mask_current = ju_stream_adapter.handler.pixel_mask
            ju_stream_adapter.handler.pixel_mask = pixel_mask_current
            pedestal_file_name_saved = pedestal_file_name

        data = ju_stream_adapter.process(image, metadata, double_pixels=double_pixels)

        # pedestal file is not in stream, skip this frame
        if ju_stream_adapter.handler.pedestal_file is None or ju_stream_adapter.handler.pedestal_file == "":
            continue

        data = np.ascontiguousarray(data)

        # starting from ju 3.3.1 pedestal file is cached in library, re-calculated only if parameters (and/or pedestal file) are changed
        id_pixel_mask_1 = id(pixel_mask_corrected)
        pixel_mask_corrected = ju_stream_adapter.handler.get_pixel_mask(geometry=True, gap_pixels=True, double_pixels=double_pixels)
        id_pixel_mask_2 = id(pixel_mask_corrected)

        if id_pixel_mask_1 != id_pixel_mask_2:
            keep_pixels = None
            r_radial_integration = None
            if pixel_mask_corrected is not None:
                #pixel_mask_corrected = np.ascontiguousarray(pixel_mask_corrected)
                pixel_mask_pf = np.ascontiguousarray(pixel_mask_corrected).astype(np.int8, copy=False)

            else:
                pixel_mask_pf = None

# add additional mask at the edge of modules for JF06T08
        apply_additional_mask = results.get("apply_additional_mask", False)
        if apply_additional_mask:
            calc_apply_additional_mask(detector, pixel_mask_pf)

        if pixel_mask_corrected is not None:
            data_s = copy(image)
            saturated_pixels_coordinates = ju_stream_adapter.handler.get_saturated_pixels(data_s, mask=True, geometry=True, gap_pixels=True, double_pixels=double_pixels)
            results["saturated_pixels"] = len(saturated_pixels_coordinates[0])
            results["saturated_pixels_x"] = saturated_pixels_coordinates[1].tolist()
            results["saturated_pixels_y"] = saturated_pixels_coordinates[0].tolist()


# pump probe analysis
        do_radial_integration = results.get("do_radial_integration", False)
        if do_radial_integration:
            keep_pixels, center_radial_integration, r_radial_integration = calc_radial_integration(results, data, keep_pixels, pixel_mask_pf, center_radial_integration, r_radial_integration)


    #copy image to work with peakfinder, just in case
        pfdata = np.copy(data)

    # make all masked pixels values nans
        if pixel_mask_pf is not None:
            pfdata[pixel_mask_pf != 1] = np.nan

        apply_threshold = results.get("apply_threshold", False)
        threshold_value_choice = results.get("threshold_value", "NaN")
        threshold_value = 0 if threshold_value_choice == "0" else np.nan
        if apply_threshold and all(k in results for k in ("threshold_min", "threshold_max")):
            threshold_min = float(results["threshold_min"])
            threshold_max = float(results["threshold_max"])
            pfdata[pfdata < threshold_min] = threshold_value
            if threshold_max > threshold_min:
                pfdata[pfdata > threshold_max] = threshold_value

    # if roi calculation request is present, make it
        roi_x1 = results.get("roi_x1", [])
        roi_x2 = results.get("roi_x2", [])
        roi_y1 = results.get("roi_y1", [])
        roi_y2 = results.get("roi_y2", [])

        if len(roi_x1) > 0 and len(roi_x1) == len(roi_x2) == len(roi_y1) == len(roi_y2):
            calc_roi(results, pfdata, roi_x1, roi_x2, roi_y1, roi_y2, pixel_mask_pf, threshold_value_choice)

# SPI analysis
        do_spi_analysis = results.get("do_spi_analysis", False)
        if do_spi_analysis:
            calc_spi_analysis(results)

# in case all needed parameters are present, make peakfinding
        do_peakfinder_analysis = results.get("do_peakfinder_analysis", False)
        if do_peakfinder_analysis and pixel_mask_pf is not None and all(k in results for k in ("beam_center_x", "beam_center_y", "hitfinder_min_snr", "hitfinder_min_pix_count", "hitfinder_adc_thresh")):
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
                    results["worker"] = worker
                    if n_aggregated_images >= results["aggregation_max"]:
                        forceSendVisualisation = True
                        data_summed = None
                        n_aggregated_images = 1
                data[pixel_mask_pf == 0] = np.NaN

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



