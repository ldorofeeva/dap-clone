import argparse
import json
import os
from copy import copy
from random import randint
from time import sleep

import jungfrau_utils as ju
import numpy as np
import zmq
from peakfinder8_extension import peakfinder_8


FLAGS = 0


def radial_profile(data, r, nr, keep_pixels=None):
    if keep_pixels is not None:
        tbin = np.bincount(r, data[keep_pixels].ravel())
    else:
        tbin = np.bincount(r, data.ravel())
    radialprofile = tbin / nr
    return radialprofile

def prepare_radial_profile(data, center, keep_pixels=None):
    y, x = np.indices((data.shape))
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2)
    if keep_pixels is not None:
        r = r[keep_pixels].astype(int).ravel()
    else:
        r = r.astype(np.int).ravel()
    nr = np.bincount(r)
    return r, nr



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--backend", default=None, help="backend address")
    parser.add_argument("--accumulator", default="localhost", help="name of host where accumulator works")
    parser.add_argument("--accumulator_port", default=13002, type=int, help="accumulator port")
    parser.add_argument("--visualisation", default="localhost", help="name of host where visualisation works")
    parser.add_argument("--visualisation_port", default=13002, type=int, help="visualisation port")
    parser.add_argument("--peakfinder_parameters", default=None, help="json file with peakfinder parameters")
    parser.add_argument("--skip_frames_rate", default=1, type=int, help="send to streamvis each of skip_frames_rate frames")

    clargs = parser.parse_args()

    if clargs.backend:
        BACKEND_ADDRESS = clargs.backend
    else:
        raise SystemExit("no backend address defined")

    FA_HOST_ACCUMULATE    = clargs.accumulator
    FA_PORT_ACCUMULATE    = clargs.accumulator_port
    FA_HOST_VISUALISATION = clargs.visualisation
    FA_PORT_VISUALISATION = clargs.visualisation_port

    skip_frames_rate = clargs.skip_frames_rate

    peakfinder_parameters = {}
    peakfinder_parameters_time = -1
    if clargs.peakfinder_parameters is not None and os.path.exists(clargs.peakfinder_parameters):
        with open(clargs.peakfinder_parameters, "r") as read_file:
            peakfinder_parameters = json.load(read_file)
        peakfinder_parameters_time = os.path.getmtime(clargs.peakfinder_parameters)

    pulseid = 0

    ju_stream_adapter = ju.StreamAdapter()

    zmq_context = zmq.Context(io_threads=4)
    poller = zmq.Poller()

# all the normal workers
    if True:
        worker = 1

    # receive from backend:
        backend_socket = zmq_context.socket(zmq.PULL)
        backend_socket.connect(BACKEND_ADDRESS)

        poller.register(backend_socket, zmq.POLLIN)

        accumulator_socket = zmq_context.socket(zmq.PUSH)
        accumulator_socket.connect(f"tcp://{FA_HOST_ACCUMULATE}:{FA_PORT_ACCUMULATE}")

        visualisation_socket = zmq_context.socket(zmq.PUB)
        visualisation_socket.connect(f"tcp://{FA_HOST_VISUALISATION}:{FA_PORT_VISUALISATION}")

    # in case of problem with communication to visualisation, keep in 0mq buffer only few messages
        visualisation_socket.set_hwm(10)

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
                    new_time = os.path.getmtime(clargs.peakfinder_parameters)
                    if ( new_time - peakfinder_parameters_time ) > 2.0:
                        old_peakfinder_parameters = peakfinder_parameters
                        sleep(0.5)
                        with open(clargs.peakfinder_parameters, "r") as read_file:
                            peakfinder_parameters = json.load(read_file)
                        peakfinder_parameters_time = new_time
                        center_radial_integration = None
                        if worker ==  0:
                            print(f"({pulseid}) update peakfinder parameters {old_peakfinder_parameters}", flush=True)
                            print(f"                                     --> {peakfinder_parameters}", flush=True)
                            print("",flush=True)
            except Exception as e:
                print(f"({pulseid}) problem ({e}) to read peakfinder parameters file, worker : {worker}", flush=True)

            events = dict(poller.poll(2000)) # check every 2 seconds in each worker
            if backend_socket in events:

                metadata = backend_socket.recv_json(FLAGS)
                image = backend_socket.recv(FLAGS, copy=False, track=False)
                image = np.frombuffer(image, dtype=metadata["type"]).reshape(metadata["shape"])

                results = copy(metadata)
                if results["shape"][0] == 2 and results["shape"][1] == 2:
                    continue

                pulseid = results.get("pulse_id", 0)
                results.update(peakfinder_parameters)

                detector = results.get("detector_name", "")

                results["laser_on"] = False
                results["number_of_spots"] = 0
                results["is_hit_frame"] = False

                daq_rec = results.get("daq_rec",0)
                event_laser    = bool((daq_rec >> 16) & 1)
                event_darkshot = bool((daq_rec >> 17) & 1)
                event_fel      = bool((daq_rec >> 18) & 1)
                event_ppicker  = bool((daq_rec >> 19) & 1)
#
                if not event_darkshot:
                    results["laser_on"] = event_laser

# Filter only ppicker events, if requested; skipping all other events
                select_only_ppicker_events = results.get("select_only_ppicker_events", 0)
                if select_only_ppicker_events and not event_ppicker:
                    continue

# special settings for p20270, only few shots were opened by pulse-picker
#                if detector in ["JF06T32V02"]:
#                    if event_ppicker:
#                        results["number_of_spots"] = 50
#                        results["is_hit_frame"] = True

                double_pixels = results.get("double_pixels", "mask")

                pedestal_file_name = metadata.get("pedestal_name", None)
                if pedestal_file_name is not None and pedestal_file_name != pedestal_file_name_saved:
                    n_corner_pixels_mask = results.get("n_corner_pixels_mask", 0)
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
#
                disabled_modules = results.get("disabled_modules", [])

# add additional mask at the edge of modules for JF06T08
                apply_additional_mask = (results.get("apply_additional_mask", 0) == 1)
                if detector == "JF06T08V04" and apply_additional_mask:
                    # edge pixels
                    pixel_mask_pf[67:1097,1063] = 0
                    pixel_mask_pf[0:1030, 1100] = 0

                    pixel_mask_pf[1106:2136, 1131] = 0
                    pixel_mask_pf[1039:2069, 1168] = 0

                    pixel_mask_pf[1039:2069, 1718] = 0
                    pixel_mask_pf[1039:2069, 1681] = 0

                    pixel_mask_pf[1106:2136, 618] = 0

                    pixel_mask_pf[1106:2136, 581] = 0

                    pixel_mask_pf[67:1097,513] = 0

                    pixel_mask_pf[67:1097, 550] = 0

                    pixel_mask_pf[0:1030, 1650] = 0

                    pixel_mask_pf[0:1030, 1613] = 0

                    pixel_mask_pf[1106, 68:582] = 0

                    pixel_mask_pf[1096, 550:1064] = 0
                    pixel_mask_pf[1106, 618:1132] = 0

                    pixel_mask_pf[1029, 1100:1614] = 0
                    pixel_mask_pf[1039, 1168:1682] = 0

                    pixel_mask_pf[1039, 1718:2230] = 0

                    pixel_mask_pf[1096, 0:513] = 0

                    pixel_mask_pf[1029, 1650:2163] = 0

                    pixel_mask_pf[2068, 1168:2232] = 0

                    pixel_mask_pf[67,0:1063] = 0

                    #bad region in left bottom inner module
                    pixel_mask_pf[842:1097, 669:671] = 0

                    #second bad region in left bottom inner module
                    pixel_mask_pf[1094, 620:807] = 0

                    # vertical line in upper left bottom module
                    pixel_mask_pf[842:1072, 87:90] = 0

                    pixel_mask_pf[1794, 1503:1550] = 0

                if detector == "JF17T16V01" and apply_additional_mask:
                    # mask module 11
                    pixel_mask_pf[2619:3333,1577:2607] = 0

                if pixel_mask_corrected is not None:
                    data_s = copy(image)
                    saturated_pixels_coordinates = ju_stream_adapter.handler.get_saturated_pixels(data_s, mask=True, geometry=True, gap_pixels=True, double_pixels=double_pixels)
                    results["saturated_pixels"] = len(saturated_pixels_coordinates[0])
                    results["saturated_pixels_x"] = saturated_pixels_coordinates[1].tolist()
                    results["saturated_pixels_y"] = saturated_pixels_coordinates[0].tolist()

# pump probe analysis
                do_radial_integration = results.get("do_radial_integration", 0)

                if do_radial_integration != 0:

                    data_copy_1 = np.copy(data)

                    if keep_pixels is None and pixel_mask_pf is not None:
                        keep_pixels = pixel_mask_pf!=0
                    if center_radial_integration is None:
                        center_radial_integration = [results["beam_center_x"], results["beam_center_y"]]
                        r_radial_integration = None
                    if r_radial_integration is None:
                        r_radial_integration, nr_radial_integration = prepare_radial_profile(data_copy_1, center_radial_integration, keep_pixels)
                        r_min_max = [int(np.min(r_radial_integration)), int(np.max(r_radial_integration)) + 1]


                    apply_threshold = results.get("apply_threshold", 0)

                    if apply_threshold != 0 and all(k in results for k in ("threshold_min", "threshold_max")):
                        threshold_min = float(results["threshold_min"])
                        threshold_max = float(results["threshold_max"])
                        data_copy_1[data_copy_1 < threshold_min] = np.nan
                        if threshold_max > threshold_min:
                            data_copy_1[data_copy_1 > threshold_max] = np.nan

                    rp = radial_profile(data_copy_1, r_radial_integration, nr_radial_integration, keep_pixels)

                    silent_region_min = results.get("radial_integration_silent_min", None)
                    silent_region_max = results.get("radial_integration_silent_max", None)

                    if (
                        silent_region_min is not None and
                        silent_region_max is not None and
                        silent_region_max > silent_region_min and
                        silent_region_min > r_min_max[0] and 
                        silent_region_max < r_min_max[1]
                    ):

                        integral_silent_region = np.sum(rp[silent_region_min:silent_region_max])
                        rp = rp / integral_silent_region
                        results["radint_normalised"] = [silent_region_min, silent_region_max]

                    results["radint_I"] = list(rp[r_min_max[0]:])
                    results["radint_q"] = r_min_max

            #copy image to work with peakfinder, just in case
                d = np.copy(data)

            # make all masked pixels values nans
                if pixel_mask_pf is not None:
                    d[pixel_mask_pf != 1] = np.nan

                apply_threshold = results.get("apply_threshold", 0)
                threshold_value_choice = results.get("threshold_value", "NaN")
                threshold_value = 0 if threshold_value_choice == "0" else np.nan
                if apply_threshold != 0 and all(k in results for k in ("threshold_min", "threshold_max")):
                    threshold_min = float(results["threshold_min"])
                    threshold_max = float(results["threshold_max"])
                    d[d < threshold_min] = threshold_value
                    if threshold_max > threshold_min:
                        d[d > threshold_max] = threshold_value

            # if roi calculation request is present, make it
                roi_x1 = results.get("roi_x1", [])
                roi_x2 = results.get("roi_x2", [])
                roi_y1 = results.get("roi_y1", [])
                roi_y2 = results.get("roi_y2", [])

                if len(roi_x1) > 0 and len(roi_x1) == len(roi_x2) and len(roi_x1) == len(roi_y1) and len(roi_x1) == len(roi_y2):
                    roi_results = [0] * len(roi_x1)
                    roi_results_normalised = [0] * len(roi_x1)

                    if pixel_mask_pf is not None:

                        results["roi_intensities_x"] = []
                        results["roi_intensities_proj_x"] = []

                        for iRoi in range(len(roi_x1)):
                            data_roi = np.copy(d[roi_y1[iRoi]:roi_y2[iRoi], roi_x1[iRoi]:roi_x2[iRoi]])

                            roi_results[iRoi] = np.nansum(data_roi)
                            if threshold_value_choice == "NaN":
                                roi_results_normalised[iRoi] = roi_results[iRoi] / ((roi_y2[iRoi] - roi_y1[iRoi]) * (roi_x2[iRoi] - roi_x1[iRoi]))
                            else:
                                roi_results_normalised[iRoi] = np.nanmean(data_roi)

                            results["roi_intensities_x"].append([roi_x1[iRoi], roi_x2[iRoi]])
                            results["roi_intensities_proj_x"].append(np.nansum(data_roi,axis=0).tolist())

                        results["roi_intensities"] = [float(r) for r in roi_results]
                        results["roi_intensities_normalised"] = [float(r) for r in roi_results_normalised ]

# SPI analysis
                do_spi_analysis = results.get("do_spi_analysis", 0)

                if (do_spi_analysis != 0) and "roi_intensities_normalised" in results and len(results["roi_intensities_normalised"]) >= 2:

                    if "spi_limit" in results and len(results["spi_limit"]) == 2:

                        number_of_spots = 0
                        if results["roi_intensities_normalised"][0] >= results["spi_limit"][0]:
                            number_of_spots += 25
                        if results["roi_intensities_normalised"][1] >= results["spi_limit"][1]:
                            number_of_spots += 50

                        results["number_of_spots"] = number_of_spots
                        if number_of_spots > 0:
                            results["is_hit_frame"] = True

# in case all needed parameters are present, make peakfinding
                do_peakfinder_analysis = results.get("do_peakfinder_analysis", 0)
                if do_peakfinder_analysis != 0 and pixel_mask_pf is not None and all(k in results for k in ("beam_center_x", "beam_center_y", "hitfinder_min_snr", "hitfinder_min_pix_count", "hitfinder_adc_thresh")):
                    x_beam = results["beam_center_x"] - 0.5 # to coordinates where position of first pixel/point is 0.5, 0.5
                    y_beam = results["beam_center_y"] - 0.5 # to coordinates where position of first pixel/point is 0.5, 0.5
                    hitfinder_min_snr = results["hitfinder_min_snr"]
                    hitfinder_min_pix_count = int(results["hitfinder_min_pix_count"])
                    hitfinder_adc_thresh = results["hitfinder_adc_thresh"]

                    asic_ny, asic_nx = d.shape
                    nasics_y, nasics_x = 1, 1
                    hitfinder_max_pix_count = 100
                    max_num_peaks = 10000

                    # usually don't need to change this value, rather robust
                    hitfinder_local_bg_radius= 20.

                    #in case of further modification with the mask, make a new one, independent from real mask
                    maskPr = np.copy(pixel_mask_pf)

                    y, x = np.indices(d.shape)
                    pix_r = np.sqrt((x-x_beam)**2 + (y-y_beam)**2)

                    peak_list_x, peak_list_y, peak_list_value = peakfinder_8(
                        max_num_peaks,
                        d.astype(np.float32),
                        maskPr.astype(np.int8),
                        pix_r.astype(np.float32),
                        asic_nx, asic_ny,
                        nasics_x, nasics_y,
                        hitfinder_adc_thresh,
                        hitfinder_min_snr,
                        hitfinder_min_pix_count,
                        hitfinder_max_pix_count,
                        hitfinder_local_bg_radius
                    )


                    number_of_spots = len(peak_list_x)
                    results["number_of_spots"] = number_of_spots
                    if number_of_spots != 0:
                        results["spot_x"] = [-1.0] * number_of_spots
                        results["spot_y"] = [-1.0] * number_of_spots
                        results["spot_intensity"] = copy(peak_list_value)
                        for i in range(number_of_spots):
                            results["spot_x"][i] = peak_list_x[i] + 0.5
                            results["spot_y"][i] = peak_list_y[i] + 0.5
                    else:
                        results["spot_x"] = []
                        results["spot_y"] = []
                        results["spot_intensity"] = []

                    npeaks_threshold_hit = results.get("npeaks_threshold_hit", 15)

                    if number_of_spots >= npeaks_threshold_hit:
                        results["is_hit_frame"] = True

                forceSendVisualisation = False
                if data.dtype != np.uint16:
                    apply_threshold = results.get("apply_threshold", 0)
                    apply_aggregation = results.get("apply_aggregation", 0)
                    if apply_aggregation == 0:
                        data_summed = None
                        n_aggregated_images = 1
                    if apply_threshold != 0 or apply_aggregation != 0:
                        if apply_threshold != 0 and all(k in results for k in ("threshold_min", "threshold_max")):
                            threshold_min = float(results["threshold_min"])
                            threshold_max = float(results["threshold_max"])
                            data[data < threshold_min] = 0.0
                            if threshold_max > threshold_min:
                                data[data > threshold_max] = 0.0
                        if (apply_aggregation != 0 ) and "aggregation_max" in results:
                            if data_summed is not None:
                                data += data_summed
                                n_aggregated_images += 1
                            data_summed = data.copy()
                            data_summed[data == -np.nan] = -np.nan
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

                frame_number = metadata["frame"]
#
                accumulator_socket.send_json(results, FLAGS)

                if (apply_aggregation != 0 ) and "aggregation_max" in results:
                    if forceSendVisualisation:
                        visualisation_socket.send_json(results, FLAGS | zmq.SNDMORE)
                        visualisation_socket.send(data, FLAGS, copy=True, track=True)
                    else:
                        data = np.empty((2, 2), dtype=np.uint16)
                        results["type"]  = str(data.dtype)
                        results["shape"] = data.shape
                        visualisation_socket.send_json(results, FLAGS | zmq.SNDMORE)
                        visualisation_socket.send(data, FLAGS, copy=True, track=True)
                else:
                    if results["is_good_frame"] and (results["is_hit_frame"] or randint(1, skip_frames_rate) == 1):
                        visualisation_socket.send_json(results, FLAGS | zmq.SNDMORE)
                        visualisation_socket.send(data, FLAGS, copy=True, track=True)
                    else:
                        data = np.empty((2, 2), dtype=np.uint16)
                        results["type"]  = str(data.dtype)
                        results["shape"] = data.shape
                        visualisation_socket.send_json(results, FLAGS | zmq.SNDMORE)
                        visualisation_socket.send(data, FLAGS, copy=True, track=True)





if __name__ == "__main__":
    main()



