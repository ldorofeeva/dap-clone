# dap (Detector Analysis Pipeline)

Runs on detector data stream provided by [sf-daq](https://github.com/paulscherrerinstitute/sf_daq_broker)


# Installation

## Pre-Installed Package (PSI)

At PSI, a pre-installed conda environment is available:
```bash
source /sf/jungfrau/applications/miniconda3/etc/profile.d/conda.sh
conda activate dap
```

## Installing from Source

Create and activate conda environment

```bash
conda create -n test-dap cython numpy pyzmq jungfrau_utils
conda activate test-dap
```

Clone and install dap

```bash
git clone https://gitlab.psi.ch/sf-daq/dap.git
cd dap
make install
``` 

# Architecture

The dap architecture is designed for horizontal scalability, processing various algorithms on detector data of different sizes. Each independent worker consumes a ZeroMQ stream from sf-daq, applies selected algorithms on received frames, and sends results:
- Metadata-enriched frames to [streamvis](https://github.com/paulscherrerinstitute/streamvis).
- Metadata-only results to the accumulator for storage.

## Worker
Each worker runs independently and processes frames received via ZeroMQ. Before applying algorithms, it converts raw (ADC) detector values to energy using [jungfrau_utils](https://github.com/paulscherrerinstitute/jungfrau_utils). 
Input parameters:
```bash
python dap/worker.py --help
usage: worker.py [-h] [--backend BACKEND] [--accumulator ACCUMULATOR]
                 [--accumulator_port ACCUMULATOR_PORT]
                 [--visualisation VISUALISATION]
                 [--visualisation_port VISUALISATION_PORT]
                 [--peakfinder_parameters PEAKFINDER_PARAMETERS]
                 [--skip_frames_rate SKIP_FRAMES_RATE]

options:
  -h, --help            show this help message and exit
  --backend BACKEND     backend address
  --accumulator ACCUMULATOR
                        name of host where accumulator works
  --accumulator_port ACCUMULATOR_PORT
                        accumulator port
  --visualisation VISUALISATION
                        name of host where visualisation works
  --visualisation_port VISUALISATION_PORT
                        visualisation port
  --peakfinder_parameters PEAKFINDER_PARAMETERS
                        json file with peakfinder parameters
  --skip_frames_rate SKIP_FRAMES_RATE
                        send to streamvis each of skip_frames_rate frames
```

The number of required workers varies based on detector size and algorithm complexity. 
Workers can be pinned to specific processor cores and distributed across multiple nodes.

## Accumulator

The accumulator collects results from workers due to network constraints, temporarily saving them to the dap-buffer before permanent storage upon user request made to sf-daq.

Input parameters:
```bash
python dap/accumulator.py --help
usage: accumulator.py [-h] [--accumulator ACCUMULATOR]
                      [--accumulator_port ACCUMULATOR_PORT]

options:
  -h, --help            show this help message and exit
  --accumulator ACCUMULATOR
                        name of host where accumulator works
  --accumulator_port ACCUMULATOR_PORT
                        accumulator port
```

# Implemented algorithms
 
   * **peakfinder Algorithm** 
   
     This algorithm is based on peakfinder8 from the [cheetah package](https://www.desy.de/~barty/cheetah/Cheetah/Welcome.html). It identifies peaks as connected pixels exhibiting intensity above the background. The background is determined iteratively by radial averaging, excluding signal pixels.

     Input parameters:
       * `'do_peakfinder_analysis': 1/0` - Specifies whether to execute the peakfinder8 algorithm.
       * `'beam_center_x/beam_center_y': float/float` - Represents the beam center coordinates in the detector space.
       * `'hitfinder_min_snr': float` - Signal-to-noise value used to differentiate between background and signal.
       * `hitfinder_min_pix_count': float` - Sets the minimum pixel count required to constitute a peak.
       * `hitfinder_adc_thresh: float` - Excludes pixels below this threshold from peak determination.
       * `'npeaks_threshold_hit': float` - Threshold on the number of discovered peaks to categorize a frame as a hit or not.

     Algorithm Output:
       * `'number_of_spots': int` - Indicates the count of identified peaks.
       * `'spot_x/spot_y/spot_intensity': 3*list[float]` - Provides coordinates and intensity of the identified peaks within the frame.
       * `'is_hit_frame': True/False` - Marks whether a frame qualifies as a hit based on the number of identified peaks exceeding the defined threshold.

   * **Radial Profile Integration**
   
      This algorithm integrates pixel intensities radially based on defined parameters.

      Input parameters: 
       * `'do_radial_integration': 1/0` - Indicates whether radial integration should occur within dap.
       * `'beam_center_x/beam_center_y': float/float` - Specifies the beam center coordinates in the detector space.
       * `'apply_threshold': 1/0` - Determines whether to apply a threshold to pixel intensities before radial integration.
       * `'radial_integration_silent_min/radial_integration_silent_max': float/float` - If both values are present, normalizes the radial integrated profile within this specified range. This is crucial for frame combination to eliminate variations in beam intensity across frames.
     
     Output of algorithm:  
       * `'radint_I': list[float]` - Represents the radial integrated profile in pixel coordinates.
       * `'radint_q' : [float, float]` - Represents the minimum and maximum x-coordinate values considered during integration in pixel coordinates.

   * **Thresholding Pixel Intensity**

      This function disregards measured pixel intensity falling above or below specified threshold values.

     Algorithm Input Parameters:
       * `'apply_threshold': 1/0` - Enables or disables the application of threshold to pixel intensity.
       * `'threshold_min/threshold_max': float/float` - Specifies threshold values. If applied, `threshold_max` is enforced only when its value surpasses `threshold_min`.
       * `'threshold_value': 0/NaN` - Replaces pixel intensity with either 0 or NaN if the pixel intensity falls outside the defined threshold values.

   * **Region of Interest (ROI) Processing**

     dap allows the definition of multiple ROIs on the detector, and it generates output results for each defined ROI. Prior to ROI processing, the algorithm to threshold pixel intensity can be applied if requested.

     Input parameters:
       * `'roi_x1/roi_x2/roi_y1/roi_y2': 4*list[float]` - Specifies the coordinates of the ROIs.

     Algorithm Output:
       * `'roi_intensities': list[float]` - Sum of pixel intensities within the ROI.
       * `'roi_intensities_normalised': list[float]` - Intensity within the defined ROI normalized to the ROI size (the count of active pixels within the ROI).
       * `'roi_intensities_x': list(float, float)` - x1/x2 (left/right) x-coordinates of the ROI.
       * `'roi_intensities_proj_x': list(value)` - Projection onto the x-coordinate of pixel intensities (sum). 

   * **Detecting Frames with High intensity in Specific Regions**

     This algorithm identifies frames containing signals within defined regions. It leverages "ROI processing" outcomes by comparing normalized intensities in the first two ROIs against predetermined thresholds. If any threshold is exceeded, the frame is labeled as a *hit*.

     Input parameters:
       * `'do_spi_analysis': 1/0` - Initiates the determination algorithm.
       * `'roi_x1/roi_x2/roi_y1/roi_y2': 4*list[float]` - Coordinates of (at least) two ROIs.
       * `'spi_limit': list(float, float)` - Threshold values for first two ROIs.

     Algorithm Output:
       * `'is_hit_frame': True/False` - Marks frame as a *hit* if intensity in at least one ROI surpasses the threshold.
       * `'number_of_spots': int` - Indicates:
         *  0: if intensity in both ROIs falls below the respective thresholds
         * 25: ROI1 has high energy but not ROI2
         * 50: ROI2 has high energy but not ROI1
         * 75: intensities in both ROIs exceed the thresholds  

   * **Frame aggregation**
  
      When dealing with faint signals that are challenging to discern in individual frames, dap offers the option to aggregate frames, combining them at the dap level before sending the resulting aggregate frame to visualization. It's important to note that this aggregation occurs independently for each worker. Thus, it's crucial to maintain a reasonable balance between the number of frames to aggregate and the number of active dap workers for a given detector. This aggregation process does not impact other algorithms, as they operate on individual frames (example: the threshold algorithm runs before frame aggregation).

      Input parameters:
        * `'apply_aggregation' : 1/0` - Enables or disables frame aggregation before transmission to visualization.
        * `'aggregation_max': int` - Specifies the maximum number of frames to aggregate before transmitting to visualization. This value pertains to each worker.

      Algorithm Output:
        * `'aggregated_images': int` - Indicates the count of aggregated images. 
       
   * **Frame Tagging**

      When event propagation is integrated into the detector, dap allows frames to be tagged accordingly, facilitating their categorization during visualization.
      
      Presently supported markers:
        * `'laser_on': True/False` - Marks frames as "laser activated" when the darkshot event code is False and the laser event code is True. Otherwise, frames are labeled as "not laser activated".
          
   * **Detection of Saturated Pixels**

      For every frame received by dap, an analysis is performed to ascertain the quantity and positions of saturated pixels.
    
      Algorithm Output:
        * `'saturated_pixels': int` - Number of saturated pixels within the frame.
        * `'saturated_pixels_x/saturated_pixels_y': list[float]/list[float]` - Coordinates of the saturated pixels.  

   * **Transmitted Parameters from dap Input to Visualization**

      Certain input parameters in dap remain unused during the dap processing phase. However, these parameters are transmitted to the visualization component, where they serve to depict specific data characteristics:
       * `'disabled_modules': list[int]` - Enumerates the disabled module numbers for visualization.
       * `'detector_distance': float`  - Distance between sample and detector in meters.
       * `'beam_energy': float` -  Photon beam energy in eV.

   * **Implement Additional Masking**

       Sensitive algorithms, such as the peakfinder, often necessitate the exclusion of specific detector regions (like defective or module edge pixels). Presently, defining these detector segments requires manual hardcoding within the worker.py code.
       
       Use the `'apply_additional_mask': 0/1`  - Input flag to enable this functionality.

   * **Filter based on pulse picker information**
       
       If the event propagation capability is accessible for the detector and the pulse picker information is correctly configured for propagation, the filtration based on pulse picker information becomes feasible by using the 
       `'select_only_ppicker_events': 0/1` - Input flag.

## Input parameters (File)

Algorithms use input parameters specified in a JSON file provided to worker.py (`--peakfinder_parameters`). It constantly monitors this file for updates to apply new parameters.

 Example JSON:
 ```json
 {
    "beam_center_x": 1119.0,
    "beam_center_y": 1068.0,
    "detector_distance": 0.092,
    "do_peakfinder_analysis": 1,
    "hitfinder_adc_thresh": 20.0,
    "hitfinder_min_pix_count": 3,
    "hitfinder_min_snr": 5.0,
    "apply_additional_mask": 1,
    "npeaks_threshold_hit": 30,
    "beam_energy": 11993.610318642704,
    "apply_threshold": 0,
    "threshold_min": 0,
    "threshold_max": 35,
    "apply_aggregation": 0,
    "aggregation_max": 2,
    "double_pixels": "mask",
    "detector_rate": 100,
    "do_radial_integration": 0,
    "do_spi_analysis": 0,
    "threshold_value": "NaN",
    "select_only_ppicker_events": 0,
    "disabled_modules": [],
    "roi_x1": [],
    "roi_y1": [],
    "roi_x2": [],
    "roi_y2": []
}
 ```

# Acknowledgment

Special thanks to Valerio Mariani for providing the cython implementation of peakfinder8.

