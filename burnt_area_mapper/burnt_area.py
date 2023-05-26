from sentinel import Sentinel
from datetime import timedelta, datetime
# import xarray as xr
from utils.util import (
    recalibrate_time
)
    

class BurntArea(Sentinel):

    def __init__(self, fire_start, fire_end, imagery, coords, bands=["B12", "B8A"], resolution=60) -> None:
        self.sentinel = Sentinel()
        self.config = self.sentinel._auth()
        self.fire_start = fire_start
        self.fire_end = fire_end
        self.imagery = imagery
        self.coords = coords
        self.bands = bands
        self.resolution = resolution

    def recalibrate_time(self, time, action, days_to_subtract=7):
        if action == "+":
            end_date = datetime.date(time + timedelta(days=7))
            start_date = datetime.date(time)
        elif action == "-":
            start_date = datetime.date(time - timedelta(days=days_to_subtract))
            end_date = datetime.date(time)
        else:
            "No es buone de nada!"
        return start_date, end_date, days_to_subtract

    def download_fire(self, time, action, days_sub=7):
        start_date, end_date, days_sub = self.recalibrate_time(time, action, days_sub)
        image, download_type = self._get_imagery(start_date=start_date, end_date=end_date, coords=self.coords, action=action)
        if image == "recalibrate":
            days_sub += 7
            self.download_fire(time, action, days_sub)
        return image, download_type

    def calc_ba(self, image, download_type):
        NIR = self.get_band(image, 0, download_type)
        SWIR = self.get_band(image, 1, download_type)
        ba = ((NIR - SWIR) / (NIR + SWIR))
        return ba
    
    def get_band(self, image, indice, download_type="regular"):
        if download_type == "regular":
            band = image[:,:,indice]
            return band
        band = image[indice,:,:]
        return band
    
    def calc_dnbr(self, pre, post):
        dnbr = pre - post
        return dnbr
    

    def process(self):
        pre_fire, download_type = self.download_fire(time=self.fire_start, action="-")
        post_fire, download_type = self.download_fire(time=self.fire_end, action="+")
        pre_fire_index = self.calc_ba(pre_fire, download_type)
        post_fire_index = self.calc_ba(post_fire, download_type)
        final_image = self.calc_dnbr(pre_fire_index, post_fire_index)
        return final_image
