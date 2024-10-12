import numpy as np
import zmq


FLAGS = 0


class ZMQSockets:

    def __init__(self, backend_address, accumulator_host, accumulator_port, visualisation_host, visualisation_port):
        zmq_context = zmq.Context(io_threads=4)
        self.poller = poller = zmq.Poller()

        # receive from backend:
        self.backend_socket = backend_socket = zmq_context.socket(zmq.PULL)
        backend_socket.connect(backend_address)

        poller.register(backend_socket, zmq.POLLIN)

        self.accumulator_socket = accumulator_socket = zmq_context.socket(zmq.PUSH)
        accumulator_socket.connect(f"tcp://{accumulator_host}:{accumulator_port}")

        self.visualisation_socket = visualisation_socket = zmq_context.socket(zmq.PUB)
        visualisation_socket.connect(f"tcp://{visualisation_host}:{visualisation_port}")

        # in case of problem with communication to visualisation, keep in 0mq buffer only few messages
        visualisation_socket.set_hwm(10)


    def has_data(self):
        events = dict(self.poller.poll(2000)) # check every 2 seconds in each worker
        return (self.backend_socket in events)

    def get_data(self):
        metadata = self.backend_socket.recv_json(FLAGS)
        image = self.backend_socket.recv(FLAGS, copy=False, track=False)
        image = np.frombuffer(image, dtype=metadata["type"]).reshape(metadata["shape"])
        return image, metadata


    def send_accumulator(self, results):
        self.accumulator_socket.send_json(results, FLAGS)

    def send_visualisation(self, results, data):
        self.visualisation_socket.send_json(results, FLAGS | zmq.SNDMORE)
        self.visualisation_socket.send(data, FLAGS, copy=True, track=True)



