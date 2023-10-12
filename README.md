# dap

Detector Analysis Pipeline
Runs on detector data stream produced by sf-daq


## Installation
At PSI-Swissfel there is already pre-installed package/conda environment to use with:
```
source /sf/jungfrau/applications/miniconda3/etc/profile.d/conda.sh
conda activate dap
```

### To install from source
Create conda environment
```
conda create -n test-dap cython numpy pyzmq jungfrau_utils
conda activate test-dap
```
Clone code of the dap and install peakfinder8_extension in the conda environment (in the same session where conda environment was made)
```
git clone https://gitlab.psi.ch/sf-daq/dap.git
cd dap
make install
``` 

## Architecture

Design of dap is made with the idea to scale horisontally and be able to process different algorithms(very different in computing complexity) running on data from detectors of different sizes (from 1 module to 32 modules detector). Independent **worker**s consumes  zeromq stream of detector data from sf-daq, run desired/selected algorithms on the frame it got from the stream and sends results : 
  * (frame with metadata information) to visualisation by [streamvis](https://github.com/paulscherrerinstitute/streamvis) 
  * (only metadata information) to **accumulator**. 
  
  Purpose of **accumulator** is to save results of dap processing. Since currently dap is running inside network which doesn't allow to send results as BS source(s), results are saved in dap buffer and is written permanently to data space upon of user request to [sf-daq](https://github.com/paulscherrerinstitute/sf_daq_broker) ("save_dap_results: True" in the detector section of request to sf-daq).

### Worker
 Each [worker](https://gitlab.psi.ch/sf-daq/dap/-/blob/main/dap/worker.py) run completely independent from another worker, and do frames processing, getting them from sf-daq by zeromq stream. Detector data is sent as a raw (ADC) values, so before applying any algorithm, worker do a conversion to energy, using [jungfrau_utils](https://github.com/paulscherrerinstitute/jungfrau_utils) package. Input parameters for the worker:
 ```
 $ python dap/worker.py --help
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
Number of needed workers strongly depends on the detector size and the desired algorithm. In easiest case (1 module detector and algorithm is to make threshold on energy values of pixels) - 1-2 workers are enough; while for the larger detector(8-16 or 32 modules) and heavy algorithm like peakfinder8 - more than hundred workers are needed. It's better to start each worker pinned to a particular processor core, since they are CPU limited application. Since each worker is completely independent from each other - it's possible to run workers on a different nodes, distributing load and increasing number of workers.

### Accumulator
Purpose of accumulator is to collect result of the processing done by workers. Currently dap is running in network which doesn't allow sending this result as BS source(s), so as temporary workaround, saving of the sub-sample of dap output results (frame indentification and intensity in the selected roi's) is done to the dap-buffer. Accumulator input parameters:
```
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

### Implemented algorithms
There are several algorithms implemented in dap, following the request/need of the experiments. 

   * peakfinder 
   
     algorithm, based on peakfinder8 from cheetah package. Identifies peaks as connected pixels with the intensity above background, where background is radial averaged, determined iteratively excluding signal pixels.

     Input parameters to algorithm:
       * `'do_peakfinder_analysis': 1/0` - to perform or not peakfinder8 algorithm
       * `'beam_center_x/beam_center_y': float/float` (beam center in the detector coordinates)
       * `'hitfinder_min_snr': float` - signal-to-noise value to discriminate background and signal
       * `hitfinder_min_pix_count': float` - minimum number of pixels to form a peak
       * `hitfinder_adc_thresh: float` - exclude pixels below the threshold from peak formation/determination
       * `'npeaks_threshold_hit': float` - threshold on number of found peaks to mark frame as *hit* or not

     Output of algorithm:
       * `'number_of_spots': int` - number of found peaks
       * `'spot_x/spot_y/spot_intensity': 3*list[float]` - coordinates and intensity of the found peaks in the frame
       * `'is_hit_frame': True/False` - mark frame as hit or not, in case number of found peaks are above defined threshold

   * radial profile integration
   
      Input parameters to algorithm: 
       * `'do_radial_integration': 1/0` - to perform or not radial integration on dap
       * `'beam_center_x/beam_center_y': float/float` - beam center in the detector coordinates
       * `'apply_threshold': 1/0` - apply or not threshold to the pixel intensities before doing radial integaration
       * `'threshold_min/threshold_max': float/float` - in case of applying threshold - value of the threshold (threshold_max is applied only if it's value larger than threshold_min)
       * `'radial_integration_silent_min/radial_integration_silent_max': float/float` - if both values are present - normalize radial integrated profile to the region between that values). Needed to be able to combine frames, to exclude different beam intensity in each of it.
     
     Output of algorithm:  
       * `'radint_I': list[float]` - (in pixels coordinates) of radial integrated profile
       * `'radint_q' : list[float]` - (intensity of normalised intensity) if the profile

   * threshold on pixel intensity

     ignore measured pixel intensity if that intensity is above or below threshold values

     Input parameters to algorithm:
       * `'apply_threshold': 1/0` - apply or not threshold to pixel intensity
       * `'threshold_min/threshold_max': float/float` - in case of applying threshold - value of the threshold (threshold_max is applied only if it's value larger than threshold_min)
       * `'threshold_value': 0/NaN` - subsitute pixel intensity by 0 or NaN value, if pixels intensity is outside of the defined values

   * ROI processing

     it's possible to define multiple ROI's on the detector and dap will output results for each of that ROI. Algorithm to threshold pixel intensity will be applied before roi processing, if requested.

     Input parameters:
       * `'roi_x1/roi_x2/roi_y1/roi_y2': 4*list[float]` - coordinates of ROI's

     Output of algorithm:
       * `'roi_intensities': list[float]` - summ of the intensities of pixels in roi
       * `'roi_intensities_normalised': list[float]` - intensity inside the defined ROI normalised to the ROI size or number of active pixels inside the ROI 
       * `'roi_intensities_x': list(float, float)` - x1/x2 (left/right) x-coordinates of the roi
       * `'roi_intensities_proj_x': list(value)` - projection on the x-coordinate of pixel intensities (sum) 

   * High intensity frame determination (was used for SPI experiments)

     Determine and mark if frame contains signal in a certain regions. It's a simple algorithm which uses "ROI processing" results and compares normalised intensities in first two ROI's to the threshold values. In case any of the threshold is exceeded - frame marked as hit.

     Input parameters:
       * `'do_spi_analysis': 1/0` - run determination algorithm
       * `'roi_x1/roi_x2/roi_y1/roi_y2': 4*list[float]` - coordinates of (at least) two ROI's
       * `'spi_limit': list(float, float)` - threshold values for first to ROI's

     Output of algorithm:
       * `'is_hit_frame': True/False` - mark frame as a hit, in case intensity in at least one ROI is above the threshold
       * `'number_of_spots': int` - 0: if intenisty in both ROI's are below corresponding threshold; 25 - ROI1 is energetic, but not ROI2; 50 - ROI2 is energetic, but not ROI1; 75 - intensities in both ROI's are above the threshold  

   * Frame aggregation

      For small intensity signal, which is hard to see on single frame, it's possible to aggregate frames on dap level and send resulting (aggregated) frame to visualisation. Note, however, that such aggregation is happening on every worker independently, so number of frames to aggregate should be reasonable compared to number of running workers of dap for that detector. Aggregation does not influence any other algorithms - they are running on real frames. Algorithm to make a threshold can be applied before frames aggregation.

      Input parameters:
        * `'apply_aggregation' : 1/0` - apply or not aggregation to frames before sending them to visualisation  
        * `'aggregation_max': int` -number of frames to aggregate before sending them to visualisation. Note that this value is per worker

      Output of algorithm:
        * `'aggregated_images': int` - number of aggregated images  
       
   * Frame labeling

      In case if the event propagation is implemented for the detector (so some event information is known from the detector header), frame can be marked accordingly on dap level to enable frame sorting on visualisation step.

      Currently implemented markers:
        * `'laser_on': True/False` - frame is marked as laser activated if darkshot event code is False and laser event code is True; in all other cases frame marked as not laser activated
          
   * Saturated pixels

      Analysis on number and position of saturated pixels is done for each frame received by the dap. 
    
      Output of algorithm:
        * `'saturated_pixels': int` - number of saturated pixels in the frame
        * `'saturated_pixels_x/saturated_pixels_y': list[float]/list[float]` - coordinates of saturated pixels  

   * Parameters propagated from dap input file to visualisation

      Some of the input parameters to dap are not used by the dap processing, but propagated to visualisation and used there to display certain characteristics of data
         * 'disabled_modules': list() (list of the number of disabled modules to visualise them)
         * 'detector_distance': value (distance from sample to detector in meters)
         * 'beam_energy': value (photon beam energy in eV)

   * Apply additonal mask

       For sensitive algorithms (like peakfinder) it may be important to remove some of the detector parts (defective pixels, edge pixels of the modules.. ). Currently definition of that detector parts are made manually and hardcoded in the worker.py code. Activation of that removal is done with `'apply_additional_mask': 0/1` input flag                

### Input parameters (file)

 All input parameters to algorithms described in the previous section, are specified in the json file which provided as an input to the worker.py application (--peakfinder_parameters option). Each of the worker constantly monitor update to that json file and in case of the change - re-loads that file to apply new set of parameters to the data stream.

 Example of the json file:
 ```
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
    "disabled_modules": [],
    "roi_x1": [],
    "roi_y1": [],
    "roi_x2": [],
    "roi_y2": []
}
 ```
That's the example of real dap input parameter file for 4M detector of Alvra. Peakfinder parameter is selected to process frame. No aggregation, thresholding, module disabling, radial integration are requested.

## Acknowledgment

 Initially DAP was made for SFX analysis, to run peak finder on a stream of data. peakfinder8 from cheetah was used for this purpose and big thanks to Valerio Mariani who provided cython implementation of peakfinder8
