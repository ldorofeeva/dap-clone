
def calc_spi_analysis(results):
    if "spi_limit" in results and len(results["spi_limit"]) == 2:

        number_of_spots = 0
        if results["roi_intensities_normalised"][0] >= results["spi_limit"][0]:
            number_of_spots += 25
        if results["roi_intensities_normalised"][1] >= results["spi_limit"][1]:
            number_of_spots += 50

        results["number_of_spots"] = number_of_spots
        if number_of_spots > 0:
            results["is_hit_frame"] = True



