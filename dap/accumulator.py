import argparse
import os

import zmq


FLAGS = 0
OUTPUT_DIR_NAME = "/gpfs/photonics/swissfel/buffer/dap/data"



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--accumulator_host", default="localhost")
    parser.add_argument("--accumulator_port", default=13002, type=int)

    clargs = parser.parse_args()

    accumulate(clargs.accumulator_host, clargs.accumulator_port)



def accumulate(_accumulator_host, accumulator_port): #TODO: accumulator_host is not used
    zmq_context = zmq.Context(io_threads=4)
    poller = zmq.Poller()

    accumulator_socket = zmq_context.socket(zmq.PULL)
    accumulator_socket.bind(f"tcp://*:{accumulator_port}")

    poller.register(accumulator_socket, zmq.POLLIN)

    run_name_before = "very_first_start"
    fname_output = f"{OUTPUT_DIR_NAME}/{run_name_before}.dap"
    output_dap = open_new_file(fname_output)

    n_frames_received = 0

    while True:
        events = dict(poller.poll(10)) # in accumulator check for worker output every 0.01 seconds

        if accumulator_socket not in events:
            output_dap.flush() # may be too intensive
            continue

        results = accumulator_socket.recv_json(FLAGS)
        n_frames_received += 1

        detector = results.get("detector_name", "")
        pulse_id = results.get("pulse_id", 0)
        run_name = str(pulse_id // 10000 * 10000)

        if run_name != run_name_before:
            run_name_before = run_name
            fname_output = f"{OUTPUT_DIR_NAME}/{detector}/{run_name_before}.dap"
            output_dap.close()
            output_dap = open_new_file(fname_output)

        res_is_good_frame   = results.get("is_good_frame", -1)
        res_is_hit_frame    = results.get("is_hit_frame", False)
        res_number_of_spots = results.get("number_of_spots", -1)
        res_laser_on        = results.get("laser_on", False)
        res_roi_intensities = results.get("roi_intensities", [])

        print(pulse_id, res_is_good_frame, res_is_hit_frame, res_number_of_spots, res_laser_on, *res_roi_intensities, file=output_dap)



def open_new_file(fname):
    dname = os.path.dirname(fname)
    os.makedirs(dname, exist_ok=True)
    return open(fname, "a")





if __name__ == "__main__":
    main()



