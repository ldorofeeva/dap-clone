peakfinder8_include_dir = 'peakfinder8/'
peakfinder8_library_dir = 'peakfinder8/'

from distutils.core import setup , Extension
from Cython.Build import cythonize
import numpy

peakfinder8_ext = Extension ( "peakfinder8_extension" , sources = [ "peakfinder8/cython/peakfinder8_extension.pyx"] ,
                                                        include_dirs = [ peakfinder8_include_dir, numpy.get_include() ],
                                                        library_dirs = [ peakfinder8_library_dir ],
                                                        libraries=["peakfinder8"],
                                                        language = "c++" )


setup ( name = "peakfinder8_extension" , ext_modules = cythonize ( peakfinder8_ext ))
