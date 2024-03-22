import argparse
import os

import zmq


FLAGS = 0
OUTPUT_DIR_NAME = "/gpfs/photonics/swissfel/buffer/dap/data"



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--accumulator", default="localhost", help="name of host where accumulator works")
    parser.add_argument("--accumulator_port", default=13002, type=int, help="accumulator port")

    args = parser.parse_args()

#    FA_HOST_ACCUMULATE = args.accumulator
    FA_PORT_ACCUMULATE = args.accumulator_port

    zmq_context = zmq.Context(io_threads=4)
    poller = zmq.Poller()

# Accumulator
    accumulator_socket = zmq_context.socket(zmq.PULL)
    accumulator_socket.bind(f"tcp://*:{FA_PORT_ACCUMULATE}")

    poller.register(accumulator_socket, zmq.POLLIN)

    n_frames_received = 0

    run_name_before = "very_first_start"
    fNameOutput = f"{OUTPUT_DIR_NAME}/{run_name_before}.dap"
    if not os.path.isdir(os.path.dirname(fNameOutput)):
        os.makedirs(os.path.dirname(fNameOutput))
    outputDap = open(fNameOutput, "a")

    while True:
        events = dict(poller.poll(10)) # in accumulator check for worker output every 0.01 seconds

        if accumulator_socket in events:
            results = accumulator_socket.recv_json(FLAGS)
            n_frames_received += 1

            pulse_id = results.get("pulse_id", 0)
            run_name = str(pulse_id//10000*10000)
            detector = results.get("detector_name", "")

            if run_name != run_name_before:
                run_name_before = run_name
                outputDap.close()
                fNameOutput = f"{OUTPUT_DIR_NAME}/{detector}/{run_name_before}.dap"
                if not os.path.isdir(os.path.dirname(fNameOutput)):
                    os.makedirs(os.path.dirname(fNameOutput))
                outputDap = open(fNameOutput, "a")

            pr_rois = results.get("roi_intensities", [])
            print(pulse_id, results.get("is_good_frame", -1), results.get("is_hit_frame", False), results.get("number_of_spots", -1), results.get("laser_on", False), *pr_rois, file=outputDap)

        else:
            outputDap.flush() # may be too intensive





if __name__ == "__main__":
    main()



