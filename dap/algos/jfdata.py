import numpy as np

import jungfrau_utils as ju

from .addmask import calc_apply_additional_mask


class JFData:

    def __init__(self):
        self.ju_stream_adapter = ju.StreamAdapter()
        self.id_pixel_mask_corrected = None
        self.pixel_mask_pf = None


    def refresh_pixel_mask(self):
        pixel_mask_current = self.ju_stream_adapter.handler.pixel_mask
        self.ju_stream_adapter.handler.pixel_mask = pixel_mask_current


    def process(self, image, metadata, double_pixels):
        return self.ju_stream_adapter.process(image, metadata, double_pixels=double_pixels)


    def has_pedestal_file(self):
        return bool(self.ju_stream_adapter.handler.pedestal_file)


    def get_pixel_mask(self, results, double_pixels):
        pixel_mask_corrected = self.ju_stream_adapter.handler.get_pixel_mask(double_pixels=double_pixels)
        if pixel_mask_corrected is None:
            self.id_pixel_mask_corrected = None
            self.pixel_mask_pf = None
            return None

        # starting from ju 3.3.1 pedestal file is cached in library, re-calculated only if parameters (and/or pedestal file) have changed
        new_id_pixel_mask_corrected = id(pixel_mask_corrected)
        old_id_pixel_mask_corrected = self.id_pixel_mask_corrected
        if new_id_pixel_mask_corrected == old_id_pixel_mask_corrected:
            return self.pixel_mask_pf

        pixel_mask_pf = np.ascontiguousarray(pixel_mask_corrected)
        calc_apply_additional_mask(results, pixel_mask_pf) # changes pixel_mask_pf in place

        self.id_pixel_mask_corrected = new_id_pixel_mask_corrected
        self.pixel_mask_pf = pixel_mask_pf

        return pixel_mask_pf


    def get_saturated_pixels(self, image, double_pixels):
        return self.ju_stream_adapter.handler.get_saturated_pixels(image, double_pixels=double_pixels)



