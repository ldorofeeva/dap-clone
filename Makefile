
all: peakfinder8_extension.so

peakfinder8_extension.so: peakfinder8/libpeakfinder8.so
	python setup.py build_ext --inplace

clean:
	rm -rf build
	rm -rf peakfinder8/libpeakfinder8.so peakfinder8/peakfinders.o
	rm -rf peakfinder8_extension.*.so
	rm -rf dist peakfinder8_extension.egg-info
	rm -rf peakfinder8/cython/peakfinder8_extension.cpp

peakfinder8/peakfinders.o: peakfinder8/cheetahmodules.h  peakfinder8/peakfinders.cpp  peakfinder8/peakfinders.h 
	gcc -fPIC -I ./peakfinder8 -c peakfinder8/peakfinders.cpp -o peakfinder8/peakfinders.o

peakfinder8/libpeakfinder8.so: peakfinder8/peakfinders.o
	gcc -shared -o peakfinder8/libpeakfinder8.so peakfinder8/peakfinders.o -lc

install: all
	cp peakfinder8/libpeakfinder8.so ${CONDA_PREFIX}/lib/.
	python setup.py install

