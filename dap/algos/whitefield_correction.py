import numpy as np
import h5py

def div(image, whitefield):
    image = np.divide(
        image,
        whitefield,
        out=np.zeros_like(image),
        where=whitefield != 0
    )
    return image

def sub(image, whitefield):
    image -= whitefield
    return image

def calc_apply_whitefield_correction(results, data):
    wf_methods = {
        "div": div,
        "sub": sub
    }

    do_whitefield_correction = results.get("do_whitefield_correction", False)
    if not do_whitefield_correction:
        print(f"No whitefield correction")
        return

    params_required = [
        "wf_data_file",
        "wf_method",
    ]

    if not all([param in results.keys() for param in params_required]):
        print(f"ERROR: Not enough parameters for whitefield correction. Skipping\n"
              f"{params_required=}")
        return

    wf_data_file = results["wf_data_file"]
    wf_method = results["wf_method"]

    if wf_method not in wf_methods.keys():
        print(f"ERROR: Unknown whitefield correction method {wf_method}. Skipping\n"
              f"{params_required=}")
        return

    with h5py.File("r", wf_data_file) as wfile:
        whitefield_image = np.asarray(wfile["data/data"])

    return wf_methods[wf_method](data, whitefield_image)

