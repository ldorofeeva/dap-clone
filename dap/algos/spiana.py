
def calc_spi_analysis(results):
    if "spi_limit" not in results:
        return

    spi_limit = results["spi_limit"]

    if len(spi_limit) != 2:
        return

    if "roi_intensities_normalised" not in results:
        return

    roi_intensities_normalised = results["roi_intensities_normalised"]

    if len(roi_intensities_normalised) < 2:
        return

    number_of_spots = 0
    if roi_intensities_normalised[0] >= spi_limit[0]:
        number_of_spots += 25
    if roi_intensities_normalised[1] >= spi_limit[1]:
        number_of_spots += 50

    results["number_of_spots"] = number_of_spots

    if number_of_spots > 0:
        results["is_hit_frame"] = True



