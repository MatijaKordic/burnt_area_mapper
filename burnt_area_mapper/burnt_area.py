import copy
from datetime import datetime, timedelta

import numpy as np
from sentinel import Sentinel


class BurntArea(Sentinel):
    def __init__(
        self,
        fire_start,
        fire_end,
        imagery,
        coords,
        bands=["B12", "B8A"],
        resolution=60,
    ) -> None:
        self.sentinel = Sentinel()
        self.config = self.sentinel._auth()
        self.fire_start = fire_start
        self.fire_end = fire_end
        self.imagery = imagery
        self.coords = coords
        self.bands = bands
        self.resolution = resolution

    def recalibrate_time(self, time, action, days_to_subtract=7):
        """
        This function recalibrates the time for the composite creation
        Inputs:
            time: the initial point time
            action: whether it is pre or post time
            days_to_subtract: number of days for composite creation
        Returns:
            start_date: start date of composite
            end_date: end date of composite
            days_to_subtract: number of days subtracted
        """
        if action == "+":
            end_date = datetime.date(time + timedelta(days=days_to_subtract))
            start_date = datetime.date(time)
        elif action == "-":
            start_date = datetime.date(time - timedelta(days=days_to_subtract))
            end_date = datetime.date(time)
        else:
            "No es buone de nada!"
        return start_date, end_date, days_to_subtract

    def download_fire(self, time, action, days_sub=7):
        """
        This is a process function for download of imagery
        Inputs:
            time: initial time
            action: whether it is pre or post time
            days_sub: number of days for composite creation
        Returns:
            image: final imagery
            download_type: regular or batch download
        """
        start_date, end_date, days_sub = self.recalibrate_time(
            time, action, days_sub
        )
        image, download_type = self._get_imagery(
            start_date=start_date,
            end_date=end_date,
            coords=self.coords,
            action=action,
        )
        if image == "recalibrate":
            days_sub += 7
            self.download_fire(time, action, days_sub)
        return image, download_type

    def calc_ba(self, image, download_type):
        """
        This function calculates the burnt area
        Inputs:
            image: numpy ndarray image
            download_type: whether batch or single download
        Returns:
            ba: burned area
        """
        NIR = self.get_band(image, 1, download_type).astype(np.int8)
        SWIR = self.get_band(image, 2, download_type).astype(np.int8)
        ba = (NIR - SWIR) / (NIR + SWIR)
        return ba

    def get_band(self, image, indice, download_type="regular"):
        """
        This function extracts a specific band from ndarray
        Inputs:
            image: numpy ndarray
            indice: band position
            download_type: whether it is a regular or batch download as the format of ndarray differs
        Returns:
            band: the band as numpy ndarray
        """
        if download_type == "regular":
            band = image[:, :, indice]
            return band
        band = image[indice, :, :]
        return band

    def calc_dnbr(self, pre, post):
        """
        Calculates the difference of nbr
        Inputs:
            pre: pre fire normalized burn ratio
            post: post fire normalized burn ratio
        Returns:
            dnbr: difference of the normalized burn ratio
        """
        dnbr = pre - post
        return dnbr

    def _get_water_mask(self, image, download_type):
        GREEN = self.get_band(image, 0, download_type).astype(np.int8)
        NIR = self.get_band(image, 1, download_type).astype(np.int8)
        ndwi = (GREEN - NIR) / (GREEN + NIR)
        # swm = ((B2 + B3) / (B8 + B11))
        # B2 - blue
        # B3 - green
        # B8 - NIR
        # B11 - SWIR
        water_mask = np.where(ndwi > 0.3, -15, 0)
        return water_mask

    def apply_water_mask(self, image, mask):
        new_mask = np.ma.masked_where(mask == -15, mask)
        final_image = np.ma.masked_where(np.ma.getmask(new_mask), image)
        final_image = final_image.filled(fill_value=-15)
        # y = np.array([2,1,5,2])                         # y axis
        # x = np.array([1,2,3,4])                         # x axis
        # m = np.ma.masked_where(y>5, y)                  # filter out values larger than 5
        # new_x = np.ma.masked_where(np.ma.getmask(m), x)
        return final_image

    def apply_final_classification(self, image):
        image_reclass = copy.copy(image)
        image_reclass[np.where(image == -15)] = 100
        image_reclass[np.where((image > -300) & (image <= -13))] = 50
        image_reclass[np.where((image >= -14.00) & (image <= -0.251))] = 2
        image_reclass[np.where((image > -0.250) & (image <= -0.101))] = 3
        image_reclass[np.where((image > -0.100) & (image <= 0.09))] = 4
        image_reclass[np.where((image > 0.100) & (image <= 0.269))] = 5
        image_reclass[np.where((image > 0.270) & (image <= 0.439))] = 6
        image_reclass[np.where((image > 0.440) & (image <= 0.659))] = 7
        image_reclass[np.where((image > 0.660) & (image <= 40.300))] = 8
        image_reclass[np.where(image > 40)] = 60
        image_reclass[np.where(image_reclass == 50)] = 10
        return image_reclass.astype("int8")

    def nbr_process(self):
        """
        This is a process function to follow the normalized burn ratio algorithm
        Returns:
            final_image: normalized burn ratio ndarray
        """
        pre_fire, download_type = self.download_fire(
            time=self.fire_start, action="-"
        )
        post_fire, download_type = self.download_fire(
            time=self.fire_end, action="+"
        )
        pre_water_mask = self._get_water_mask(pre_fire, download_type)
        _ = self._get_water_mask(post_fire, download_type)
        pre_fire_index = self.calc_ba(pre_fire, download_type)
        post_fire_index = self.calc_ba(post_fire, download_type)
        final_image = self.calc_dnbr(pre_fire_index, post_fire_index)
        image_masked = self.apply_water_mask(final_image, pre_water_mask)
        classified = self.apply_final_classification(image_masked)
        print(classified)
        print(np.unique(classified, return_counts=True))
        return classified
