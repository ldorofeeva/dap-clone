"""
Streak Finder algorithm implemented by CFEL Chapman group

Requires Convergent beam streak finder package installed:

https://github.com/simply-nicky/streak_finder
(note g++ 11 required for building)
"""

from streak_finder import PatternStreakFinder
from streak_finder.label import Structure2D


def calc_streakfinder_analysis(results, data, pixel_mask_sf):
    do_streakfinder_analysis = results.get("do_streakfinder_analysis", False)
    if not do_streakfinder_analysis:
        print(f"No streak finder analysis")
        return

    params_required = [
        "sf_structure_radius",
        "sf_structure_rank",
        "sf_min_size",
        "sf_vmin",
        "sf_npts",
        "sf_xtol"
    ]

    if not all([param in results.keys() for param in params_required]):
        print(f"ERROR: Not enough parameters for streak finder analysis. Skipping\n"
              f"{params_required=}")
        return

    radius = results["sf_structure_radius"]
    rank = results["sf_structure_rank"]
    min_size = results["sf_min_size"]
    vmin = results["sf_vmin"]
    npts = results["sf_npts"]
    xtol = results["sf_xtol"]

    struct = Structure2D(radius, rank)
    psf = PatternStreakFinder(data=data, mask=pixel_mask_sf, structure=struct, min_size=min_size)

    peaks = psf.detect_peaks(vmin=vmin, npts=npts)
    streaks = psf.detect_streaks(peaks=peaks, xtol=xtol, vmin=vmin)

    results.update({"streaks": streaks.to_lines()})  # arr(4, n_lines); 0coord x0, y0, x1, y1