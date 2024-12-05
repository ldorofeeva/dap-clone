
def calc_spi_analysis(results):
    do_spi_analysis = results.get("do_spi_analysis", False)
    if not do_spi_analysis:
        return

    for k in ("spi_limit", "roi_intensities_normalised"):
        if k not in results:
            return

    spi_limit = results["spi_limit"]
    roi_intensities_normalised = results["roi_intensities_normalised"]

    number_of_spots = 0
    for index, (rin, sl) in enumerate(zip(roi_intensities_normalised, spi_limit)):
        if rin >= sl:
            number_of_spots += 25 * (index+1)

    results["number_of_spots"] = number_of_spots

    if number_of_spots > 0:
        results["is_hit_frame"] = True



