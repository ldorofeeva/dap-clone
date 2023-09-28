# dap

Detector Analysis Pipeline
Runs on detector data stream produced by sf-daq

## Name
DAP is a Detector Analysis Pipeline which runs on detector stream data produced by sf-daq

## Description

## Installation
At PSI-Swissfel there is already pre-installed package/conda environment to use with:
```
source /sf/jungfrau/applications/miniconda3/etc/profile.d/conda.sh
conda activate dap
```

### To install from source
Create conda environment
```
conda create -n test-dap cython numpy pyzmq jungfrau_util
conda activate test-dap
```
Clone code of the dap and install peakfinder8_extension in the conda environment
```
git clone https://gitlab.psi.ch/sf-daq/dap.git
cd dap
make install
``` 

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Acknowledgment

 Initially DAP was made for SFX analysis, to run peak finder on a stream of data. peakfinder8 from cheetah was used for this purpose and big thanks to Valerio Mariani who provided cython implementation of peakfinder8
