import copy
import json
from datetime import datetime, timedelta

import numpy as np
from sentinel import Sentinel
from sentinel_sat import Sentinel_Sat


class BurntArea(Sentinel, Sentinel_Sat):
    def __init__(
        self,
        fire_start,
        fire_end,
        imagery,
        coords,
        provider,
        bands=["B12", "B8A"],
        resolution=60,
    ) -> None:
        self.sentinel = Sentinel()
        self.config = self.sentinel._auth()
        self.fire_start = fire_start
        self.fire_end = fire_end
        self.imagery = imagery
        self.coords = coords
        self.provider = provider
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

    def download_sentinelsat_fire(self, time, action, days_sub=7):
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
        self.apis = Sentinel_Sat(
            start_date=start_date, end_date=end_date, input_file=self.coords
        )
        image, download_type = self.apis.ss_process()
        if image == "recalibrate":
            days_sub += 7
            self.download_sentinelsat_fire(time, action, days_sub)
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
        if download_type == "cop":
            band_load = self.load_raster_config()
            nir_band_ind = band_load["B8A"]
            swir_band_ind = band_load["B11"]
            NIR = self.get_band(image, nir_band_ind, download_type)
            SWIR = self.get_band(image, swir_band_ind, download_type)
        else:
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
        # if download_type == "cop":
        #     band = (((band - np.min(band)) * ((255 - 0) / (np.max(band) - np.min(band)))) + 0).astype(np.int8)
        #     print(band.dtype)
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
        """
        This function calculates the water mask as NDWI
        Inputs:
            image: numpy ndarray image with several bands
            download_type: whether download was regular or batch
        Returns:
            water_mask: numpy ndarray water mask
        """
        # print(np.unique(image, return_counts=True))
        if download_type == "cop":
            band_load = self.load_raster_config()
            green_band_ind = band_load["B03"]
            print(green_band_ind)
            blue_band_ind = band_load["B02"]
            nir_band_ind = band_load["B8A"]
            swir_band_ind = band_load["B11"]
            GREEN = self.get_band(image, green_band_ind, download_type)
            NIR = self.get_band(image, nir_band_ind, download_type)
            # ndwi = (GREEN - NIR) / (GREEN + NIR)
            BLUE = self.get_band(image, blue_band_ind, download_type)
            SWIR = self.get_band(image, swir_band_ind, download_type)
        else:
            GREEN = self.get_band(image, 0, download_type).astype(np.int8)
            NIR = self.get_band(image, 1, download_type).astype(np.int8)
            # ndwi = (GREEN - NIR) / (GREEN + NIR)
            BLUE = self.get_band(image, 5, download_type).astype(np.int8)
            SWIR = self.get_band(image, 6, download_type).astype(np.int8)
        swm = (BLUE + GREEN) / (NIR + SWIR)
        swm_water_mask = copy.copy(swm)
        swm_water_mask[(swm >= 1.1) & (swm <= 5.6)] = -15
        # swm_water_mask = np.where((swm >= 1.4) & (swm <= 1.6), -15, 0)
        # swm = ((B2 + B3) / (B8 + B11)) seems like a good check too
        # B2 - blue
        # B3 - green
        # B8 - NIR
        # B11 - SWIR
        # ndwi_water_mask = np.where(ndwi > 0.3, -15, 0)
        return swm_water_mask

    def load_raster_config(self):
        """
        This function loads the raster configuration.
        Inputs:
            name: name of output json
        """
        with open(
            "./data/S2B_MSIL2A_20230303T001109_N0509_R073_T55HGD_20230303T154543.SAFE-R20m.json",
            "r",
        ) as outfile:
            file = json.load(outfile)
            return file

    def apply_water_mask(self, image, mask):
        """
        This function applies the water mask to the final output.
        Inputs:
            image: numpy ndarray final output
            mask: water mask
        Returns:
            final_image: masked output
        """
        new_mask = np.ma.masked_where(mask == -15, mask)
        final_image = np.ma.masked_where(np.ma.getmask(new_mask), image)
        final_image = final_image.filled(fill_value=-15)
        return final_image

    def apply_final_classification(self, image):
        """
        This function applies the final classification of burned areas.
        Inputs:
            image: image to classify
        Returns:
            image_reclass: reclassified image
        """
        image_reclass = copy.copy(image)
        # image_reclass[np.where(image == -15)] = 100
        image_reclass[np.where((image > -300) & (image <= -13))] = 50
        image_reclass[np.where((image >= -14.00) & (image <= -0.251))] = 2
        image_reclass[np.where((image > -0.250) & (image <= -0.101))] = 3
        image_reclass[np.where((image > -0.100) & (image <= 0.09))] = 4
        image_reclass[np.where((image > 0.100) & (image <= 0.269))] = 5
        image_reclass[np.where((image > 0.270) & (image <= 0.439))] = 6
        image_reclass[np.where((image > 0.440) & (image <= 0.659))] = 7
        image_reclass[np.where((image > 0.660) & (image <= 40.300))] = 8
        image_reclass[np.where(image > 40)] = 60
        image_reclass[np.where(image_reclass == 50)] = 1
        raster_dict = {
            "1": "Water",
            "2": "Enhanced regrowth, high (post-fire)",
            "3": "Enhanced regrowth, low (post-fire)",
            "4": "Unburned",
            "5": "Low Severity",
            "6": "Moderate-low Severity",
            "7": "Moderate-high Severity",
            "8": "High Severity",
            "60": "Unclassified",
        }
        self.write_raster_config("raster_classification", raster_dict)
        return image_reclass

    def write_raster_config(self, name, config_dict):
        """
        This function writes the raster configuration.
        Inputs:
            name: name of output json
            config_dict: dictionary with classification
        """
        with open(f"./data/{name}.json", "w") as outfile:
            json.dump(config_dict, outfile)

    def nbr_process(self):
        """
        This is a process function to follow the normalized burn ratio algorithm
        Returns:
            final_image: normalized burn ratio ndarray
        """
        pre_fire, post_fire, download_type = self.download_imagery()
        pre_water_mask = self._get_water_mask(pre_fire, download_type)
        _ = self._get_water_mask(post_fire, download_type)
        pre_fire_index = self.calc_ba(pre_fire, download_type)
        post_fire_index = self.calc_ba(post_fire, download_type)
        final_image = self.calc_dnbr(pre_fire_index, post_fire_index)
        image_masked = self.apply_water_mask(final_image, pre_water_mask)
        classified = self.apply_final_classification(image_masked)
        return classified

    def download_imagery(self):
        if self.provider == "CA":
            pre_fire, download_type = self.download_sentinelsat_fire(
                time=self.fire_start, action="-"
            )
            post_fire, download_type = self.download_sentinelsat_fire(
                time=self.fire_end, action="+"
            )
        elif self.provider == "SH":
            pre_fire, download_type = self.download_fire(
                time=self.fire_start, action="-"
            )
            post_fire, download_type = self.download_fire(
                time=self.fire_end, action="+"
            )
        else:
            print("No specified provider!")
        return pre_fire, post_fire, download_type
