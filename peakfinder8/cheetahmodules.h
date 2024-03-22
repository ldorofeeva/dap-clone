/*
 *  cheetahmodules.h
 *  cheetah
 *
 *  Created by Anton Barty on 7/2/11.
 *  Copyright 2011 CFEL. All rights reserved.
 *
 */

int peakfinder3(tPeakList*, float*, char*, long, long, long, long, float, float, long, long, long);
int peakfinder6(tPeakList*, float*, char*, long, long, long, long, float, float, long, long, long, float);
int peakfinder8(tPeakList*, float*, char*, float*, long, long, long, long, float, float, long, long, long);
int peakfinder8old(tPeakList*, float*, char*, float*, long, long, long, long, float, float, long, long, long);
int killNearbyPeaks(tPeakList*, float );


#include <stdint.h>
// from detectorObject.h file
//--------------------------------------------------------------------------------------------------------------------
/*
 * Bits for pixel masks
 * Oriented along conventions defined for CXI file format ( https://github.com/FilipeMaia/CXI/raw/master/cxi_file_format.pdf )
 * CONVENTIONS:
 * - All options are dominantly inherited during assembly and pixel integration (see assembleImage.cpp)
 * - The default value for all options is "false"
 * */
static const uint16_t PIXEL_IS_PERFECT = 0;                         // Remember to change this value if necessary after adding a new option
static const uint16_t PIXEL_IS_INVALID = 1;                         // bit 0
static const uint16_t PIXEL_IS_SATURATED = 2;                       // bit 1
static const uint16_t PIXEL_IS_HOT = 4;                             // bit 2
static const uint16_t PIXEL_IS_DEAD = 8;                            // bit 3
static const uint16_t PIXEL_IS_SHADOWED = 16;                       // bit 4
static const uint16_t PIXEL_IS_IN_PEAKMASK = 32;                    // bit 5
static const uint16_t PIXEL_IS_TO_BE_IGNORED = 64;                  // bit 6
static const uint16_t PIXEL_IS_BAD = 128;                           // bit 7
static const uint16_t PIXEL_IS_OUT_OF_RESOLUTION_LIMITS = 256;      // bit 8
static const uint16_t PIXEL_IS_MISSING = 512;                       // bit 9
static const uint16_t PIXEL_IS_NOISY = 1024;                        // bit 10
static const uint16_t PIXEL_IS_ARTIFACT_CORRECTED = 2048;           // bit 11
static const uint16_t PIXEL_FAILED_ARTIFACT_CORRECTION = 4096;      // bit 12
static const uint16_t PIXEL_IS_PEAK_FOR_HITFINDER = 8192;           // bit 13
static const uint16_t PIXEL_IS_PHOTON_BACKGROUND_CORRECTED = 16384; // bit 14
static const uint16_t PIXEL_IS_ALL = PIXEL_IS_INVALID | PIXEL_IS_SATURATED | PIXEL_IS_HOT | PIXEL_IS_DEAD | PIXEL_IS_SHADOWED | PIXEL_IS_IN_PEAKMASK | PIXEL_IS_TO_BE_IGNORED | PIXEL_IS_BAD | PIXEL_IS_OUT_OF_RESOLUTION_LIMITS | PIXEL_IS_MISSING | PIXEL_IS_NOISY | PIXEL_IS_ARTIFACT_CORRECTED | PIXEL_FAILED_ARTIFACT_CORRECTION | PIXEL_IS_PEAK_FOR_HITFINDER | PIXEL_IS_PHOTON_BACKGROUND_CORRECTED; // all bits
//
inline bool isAnyOfBitOptionsSet(uint16_t value, uint16_t option) {return ((value & option)!=0);}
//--------------------------------------------------------------------------------------------------------------------
